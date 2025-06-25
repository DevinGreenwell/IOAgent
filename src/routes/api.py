# Flask routes for IOAgent API endpoints

from flask import Blueprint, request, jsonify, send_file, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
import os
import json
import uuid
import secrets
from datetime import datetime

from src.models.user import db, User, Project, Evidence, TimelineEntry, CausalFactor, AnalysisSection
from src.models.project_manager import ProjectManager, TimelineBuilder
from src.models.roi_generator import ROIGenerator, CausalAnalysisEngine
from src.models.roi_generator_uscg import USCGROIGenerator
from src.models.ai_assistant import AIAssistant

# Create blueprint
api_bp = Blueprint('api', __name__)

# Initialize managers (keep for legacy functionality and AI features)
project_manager = ProjectManager()
timeline_builder = TimelineBuilder()
roi_generator = ROIGenerator()
uscg_roi_generator = USCGROIGenerator()
causal_engine = CausalAnalysisEngine()
ai_assistant = AIAssistant()

# Helper function to validate project ID
def validate_project_id(project_id):
    """Validate project ID format"""
    import re
    if not project_id or not isinstance(project_id, str):
        return False
    if len(project_id) > 100:
        return False
    if not re.match(r'^[a-zA-Z0-9_-]+$', project_id):
        return False
    if '..' in project_id or '/' in project_id or '\\' in project_id:
        return False
    return True

@api_bp.route('/projects', methods=['GET'])
@jwt_required()
def list_projects():
    """List all projects"""
    try:
        projects = Project.query.all()
        projects_data = [project.to_dict(include_relationships=False) for project in projects]
        return jsonify({'success': True, 'projects': projects_data})
    except Exception as e:
        current_app.logger.error(f"Error listing projects: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to retrieve projects'}), 500

@api_bp.route('/projects', methods=['POST'])
@jwt_required()
def create_project():
    """Create a new project"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        title = data.get('title', '').strip()
        if not title:
            return jsonify({'success': False, 'error': 'Project title is required'}), 400
        
        investigating_officer = data.get('investigating_officer', '').strip()
        
        # Create new project
        project = Project(
            id=str(uuid.uuid4()),
            title=title[:200],  # Limit length
            investigating_officer=investigating_officer[:100] if investigating_officer else None,
            status='draft'
        )
        
        db.session.add(project)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'project': project.to_dict(include_relationships=True)
        })
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error creating project: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to create project'}), 500

@api_bp.route('/projects/<project_id>', methods=['GET'])
@jwt_required()
def get_project(project_id):
    """Get project details"""
    try:
        # Validate project ID
        if not validate_project_id(project_id):
            return jsonify({'success': False, 'error': 'Invalid project identifier'}), 400
        
        project = Project.query.filter_by(id=project_id).first()
        if not project:
            return jsonify({'success': False, 'error': 'Project not found'}), 404
        
        return jsonify({'success': True, 'project': project.to_dict(include_relationships=True)})
    except Exception as e:
        current_app.logger.error(f"Error getting project {project_id}: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to retrieve project'}), 500

@api_bp.route('/projects/<project_id>', methods=['PUT'])
@jwt_required()
def update_project(project_id):
    """Update project"""
    try:
        # Validate project ID
        if not validate_project_id(project_id):
            return jsonify({'success': False, 'error': 'Invalid project identifier'}), 400
        
        project = Project.query.filter_by(id=project_id).first()
        if not project:
            return jsonify({'success': False, 'error': 'Project not found'}), 404
        
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        # Update basic fields
        if 'title' in data and data['title']:
            project.title = str(data['title'])[:200]
        if 'investigating_officer' in data:
            project.investigating_officer = str(data['investigating_officer'])[:100] if data['investigating_officer'] else None
        if 'status' in data and data['status'] in ['draft', 'in_progress', 'complete']:
            project.status = data['status']
        
        # Update incident info
        if 'incident_info' in data:
            incident_data = data['incident_info']
            if 'incident_date' in incident_data:
                try:
                    if incident_data['incident_date']:
                        project.incident_date = datetime.fromisoformat(incident_data['incident_date'])
                    else:
                        project.incident_date = None
                except (ValueError, TypeError) as e:
                    return jsonify({'success': False, 'error': f'Invalid incident date format: {str(e)}'}), 400
            if 'location' in incident_data:
                project.incident_location = str(incident_data['location'])[:500] if incident_data['location'] else None
            if 'incident_type' in incident_data:
                project.incident_type = str(incident_data['incident_type'])[:100] if incident_data['incident_type'] else None
        
        project.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({'success': True, 'project': project.to_dict(include_relationships=True)})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error updating project {project_id}: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to update project'}), 500

@api_bp.route('/projects/<project_id>', methods=['DELETE'])
@jwt_required()
def delete_project(project_id):
    """Delete project"""
    try:
        success = project_manager.delete_project(project_id)
        if success:
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': 'Failed to delete project'}), 500
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/projects/<project_id>/upload', methods=['POST'])
@jwt_required()
def upload_file(project_id):
    """Upload file to project and extract timeline entries"""
    try:
        # Validate project ID
        if not validate_project_id(project_id):
            return jsonify({'success': False, 'error': 'Invalid project identifier'}), 400
        
        project = Project.query.filter_by(id=project_id).first()
        if not project:
            return jsonify({'success': False, 'error': 'Project not found'}), 404
        
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file provided'}), 400
        
        file = request.files['file']
        
        # File security validation
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400
        
        # Check file size (limit to 50MB)
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)  # Reset file pointer
        
        if file_size > 50 * 1024 * 1024:  # 50MB limit
            return jsonify({'success': False, 'error': 'File size exceeds 50MB limit'}), 400
        
        # Validate file extension
        allowed_extensions = {'.pdf', '.txt', '.doc', '.docx', '.jpg', '.jpeg', '.png', '.gif', '.zip', '.csv', '.xlsx'}
        filename = secure_filename(file.filename)
        file_ext = os.path.splitext(filename)[1].lower()
        
        if file_ext not in allowed_extensions:
            return jsonify({'success': False, 'error': f'File type {file_ext} not allowed'}), 400
        
        # Generate unique filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_filename = f"{timestamp}_{secrets.token_hex(8)}_{filename}"
        
        # Create project uploads directory
        uploads_dir = os.path.join(current_app.config.get('UPLOAD_FOLDER', 'uploads'), f'project_{project_id}')
        os.makedirs(uploads_dir, exist_ok=True)
        
        # Save file
        file_path = os.path.join(uploads_dir, unique_filename)
        file.save(file_path)
        
        # Get additional metadata
        description = str(request.form.get('description', ''))[:500]
        
        # Process file locally instead of using project manager
        # since we already saved it
        from src.models.ai_assistant import AIAssistant
        from src.models.project_manager import ProjectManager
        
        # Extract content from saved file
        pm = ProjectManager()
        content = pm._extract_file_content(file_path)
        
        # Get timeline suggestions if content was extracted
        timeline_suggestions = []
        if content:
            ai = AIAssistant()
            if ai.client:
                # Get existing timeline for context
                existing_timeline = [entry.to_dict() for entry in project.timeline_entries]
                timeline_suggestions = ai.suggest_timeline_entries(content, existing_timeline)
        
        # Store file record for reference (simpler than Evidence)
        # You might want to create a simpler UploadedFile model instead
        evidence = Evidence(
            id=str(uuid.uuid4()),
            filename=unique_filename,
            original_filename=file.filename,
            file_path=os.path.relpath(file_path, current_app.config.get('UPLOAD_FOLDER', 'uploads')),
            file_size=file_size,
            mime_type=file.content_type,
            file_type=pm._determine_file_type(file_path),
            description=description or f"Uploaded file: {file.filename}",
            source='user_upload',
            project_id=project_id
        )
        
        db.session.add(evidence)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'file': {
                'id': evidence.id,
                'filename': evidence.original_filename,
                'uploaded_at': evidence.uploaded_at.isoformat() if evidence.uploaded_at else None
            },
            'timeline_suggestions': timeline_suggestions,
            'message': f'File uploaded successfully. Found {len(timeline_suggestions)} potential timeline entries.'
        })
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error uploading file to project {project_id}: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to upload file'}), 500

@api_bp.route('/projects/<project_id>/timeline', methods=['POST'])
@jwt_required()
def add_timeline_entry(project_id):
    """Add timeline entry"""
    try:
        # Validate project ID
        if not validate_project_id(project_id):
            return jsonify({'success': False, 'error': 'Invalid project identifier'}), 400
        
        project = Project.query.filter_by(id=project_id).first()
        if not project:
            return jsonify({'success': False, 'error': 'Project not found'}), 404
        
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        # Validate required fields
        required_fields = ['timestamp', 'type', 'description']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'success': False, 'error': f'Missing required field: {field}'}), 400
        
        # Validate timestamp format
        try:
            timestamp = datetime.fromisoformat(data['timestamp'])
        except (ValueError, TypeError):
            return jsonify({'success': False, 'error': 'Invalid timestamp format. Use ISO format (YYYY-MM-DDTHH:MM:SS)'}), 400
        
        # Create timeline entry
        entry = TimelineEntry(
            id=str(uuid.uuid4()),
            timestamp=timestamp,
            entry_type=str(data['type'])[:50],
            description=str(data['description'])[:1000],
            confidence_level=data.get('confidence_level', 'medium'),
            is_initiating_event=bool(data.get('is_initiating_event', False)),
            project_id=project_id
        )
        
        # Set assumptions if provided
        if data.get('assumptions'):
            entry.assumptions_list = data['assumptions']
        
        # Set personnel if provided
        if data.get('personnel_involved'):
            entry.personnel_involved_list = data['personnel_involved']
        
        db.session.add(entry)
        db.session.commit()
        
        return jsonify({'success': True, 'entry': entry.to_dict()})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error adding timeline entry to project {project_id}: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to add timeline entry'}), 500

@api_bp.route('/projects/<project_id>/timeline/<entry_id>', methods=['PUT'])
@jwt_required()
def update_timeline_entry(project_id, entry_id):
    """Update timeline entry"""
    try:
        # Validate project ID
        if not validate_project_id(project_id):
            return jsonify({'success': False, 'error': 'Invalid project identifier'}), 400
        
        # Validate entry ID
        if not validate_project_id(entry_id):  # Same validation logic applies
            return jsonify({'success': False, 'error': 'Invalid entry identifier'}), 400
        
        # Check if timeline entry exists
        entry = TimelineEntry.query.filter_by(id=entry_id, project_id=project_id).first()
        if not entry:
            return jsonify({'success': False, 'error': 'Timeline entry not found'}), 404
        
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        # Update entry fields
        if 'timestamp' in data:
            try:
                entry.timestamp = datetime.fromisoformat(data['timestamp'])
            except (ValueError, TypeError) as e:
                return jsonify({'success': False, 'error': f'Invalid timestamp format: {str(e)}'}), 400
        if 'type' in data:
            entry.entry_type = str(data['type'])[:50]
        if 'description' in data:
            entry.description = str(data['description'])[:1000]
        if 'confidence_level' in data:
            entry.confidence_level = data['confidence_level']
        if 'is_initiating_event' in data:
            entry.is_initiating_event = data['is_initiating_event']
        if 'assumptions' in data:
            entry.assumptions_list = data['assumptions']
        if 'personnel_involved' in data:
            entry.personnel_involved_list = data['personnel_involved']
        
        entry.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({'success': True, 'entry': entry.to_dict()})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error updating timeline entry {entry_id}: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to update timeline entry'}), 500

@api_bp.route('/projects/<project_id>/timeline/<entry_id>', methods=['DELETE'])
@jwt_required()
def delete_timeline_entry(project_id, entry_id):
    """Delete timeline entry"""
    try:
        # Validate project ID
        if not validate_project_id(project_id):
            return jsonify({'success': False, 'error': 'Invalid project identifier'}), 400
        
        # Validate entry ID
        if not validate_project_id(entry_id):  # Same validation logic applies
            return jsonify({'success': False, 'error': 'Invalid entry identifier'}), 400
        
        # Check if timeline entry exists
        entry = TimelineEntry.query.filter_by(id=entry_id, project_id=project_id).first()
        if not entry:
            return jsonify({'success': False, 'error': 'Timeline entry not found'}), 404
        
        # Remove the database record
        db.session.delete(entry)
        db.session.commit()
        
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting timeline entry {entry_id}: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to delete timeline entry'}), 500

@api_bp.route('/projects/<project_id>/causal-analysis', methods=['POST'])
@jwt_required()
def run_causal_analysis(project_id):
    """Run causal analysis on timeline"""
    try:
        # Validate project ID
        if not validate_project_id(project_id):
            return jsonify({'success': False, 'error': 'Invalid project identifier'}), 400
        
        project = Project.query.filter_by(id=project_id).first()
        if not project:
            return jsonify({'success': False, 'error': 'Project not found'}), 404
        
        # Get timeline entries
        timeline_entries = project.timeline_entries
        if not timeline_entries:
            return jsonify({'success': False, 'error': 'No timeline entries found for analysis'}), 400
        
        # Create wrapper objects that match expected format for analysis engines
        class TimelineEntryWrapper:
            def __init__(self, entry_dict):
                self.timestamp = datetime.fromisoformat(entry_dict['timestamp']) if entry_dict.get('timestamp') else datetime.utcnow()
                self.type = entry_dict.get('type', 'event')  # entry.to_dict() uses 'type', not 'entry_type'
                self.description = entry_dict.get('description', '')
                self.id = entry_dict.get('id', '')
                self.evidence_ids = entry_dict.get('evidence_ids', [])
                self.personnel_involved = entry_dict.get('personnel_involved', [])
                self.assumptions = entry_dict.get('assumptions', [])
                self.confidence_level = entry_dict.get('confidence_level', 'medium')
                self.is_initiating_event = entry_dict.get('is_initiating_event', False)
        
        class EvidenceWrapper:
            def __init__(self, evidence_dict):
                self.type = evidence_dict.get('type', 'document')
                self.description = evidence_dict.get('description', '')
                self.filename = evidence_dict.get('filename', '')
                self.source = evidence_dict.get('source', 'user_upload')
                self.reliability = evidence_dict.get('reliability', 'medium')
        
        # Convert to wrapper objects
        timeline_objects = [TimelineEntryWrapper(entry.to_dict()) for entry in timeline_entries]
        evidence_objects = [EvidenceWrapper(item.to_dict()) for item in project.evidence_items]
        
        # Run basic causal analysis using the engine
        causal_factors = []
        try:
            causal_factors = causal_engine.analyze_timeline(timeline_objects)
            current_app.logger.info(f"Causal engine identified {len(causal_factors)} factors")
        except Exception as engine_error:
            current_app.logger.warning(f"Causal engine analysis failed: {engine_error}")
        
        # Use AI to enhance analysis if available
        ai_factors = []
        if ai_assistant.client:
            try:
                ai_factors = ai_assistant.identify_causal_factors(timeline_objects, evidence_objects)
                current_app.logger.info(f"AI assistant identified {len(ai_factors)} factors")
            except Exception as ai_error:
                current_app.logger.warning(f"AI analysis failed: {ai_error}")
        
        # Create CausalFactor database records
        created_factors = []
        
        # Process factors from basic engine (CausalFactor objects)
        for factor_obj in causal_factors:
            try:
                # Convert roi_models.CausalFactor to database CausalFactor
                factor = CausalFactor(
                    id=str(uuid.uuid4()),
                    title=str(factor_obj.title or 'Unknown Factor')[:200],
                    description=str(factor_obj.description or '')[:1000],
                    category=factor_obj.category or 'organizational',
                    severity='medium',  # Default since roi_models doesn't have severity
                    likelihood='medium',  # Default since roi_models doesn't have likelihood
                    analysis_text=str(factor_obj.analysis_text or '')[:2000],
                    project_id=project_id
                )
                
                # Set evidence support if provided
                if hasattr(factor_obj, 'evidence_support') and factor_obj.evidence_support:
                    factor.evidence_support_list = factor_obj.evidence_support
                
                db.session.add(factor)
                created_factors.append(factor)
            except Exception as factor_error:
                current_app.logger.error(f"Error creating causal factor from engine: {factor_error}")
                continue
        
        # Process factors from AI (dictionaries)
        for factor_data in ai_factors:
            try:
                factor = CausalFactor(
                    id=str(uuid.uuid4()),
                    title=str(factor_data.get('title', 'Unknown Factor'))[:200],
                    description=str(factor_data.get('description', ''))[:1000],
                    category=factor_data.get('category', 'organizational'),
                    severity=factor_data.get('severity', 'medium'),
                    likelihood=factor_data.get('likelihood', 'medium'),
                    analysis_text=str(factor_data.get('analysis_text', factor_data.get('analysis', '')))[:2000],
                    project_id=project_id
                )
                
                # Set recommendations if provided
                if factor_data.get('recommendations'):
                    factor.recommendations_list = factor_data['recommendations']
                
                # Set evidence support if provided
                if factor_data.get('evidence_support'):
                    factor.evidence_support_list = factor_data['evidence_support']
                
                db.session.add(factor)
                created_factors.append(factor)
            except Exception as factor_error:
                current_app.logger.error(f"Error creating causal factor: {factor_error}")
                continue
        
        db.session.commit()
        current_app.logger.info(f"Created {len(created_factors)} causal factors for project {project_id}")
        
        return jsonify({
            'success': True,
            'causal_factors': [factor.to_dict() for factor in created_factors],
            'message': f'Analysis complete. Identified {len(created_factors)} causal factors.'
        })
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error running causal analysis for project {project_id}: {str(e)}")
        return jsonify({'success': False, 'error': f'Failed to run causal analysis: {str(e)}'}), 500

@api_bp.route('/projects/<project_id>/causal-factors/<factor_id>', methods=['PUT'])
@jwt_required()
def update_causal_factor(project_id, factor_id):
    """Update a causal factor"""
    try:
        # Validate project ID
        if not validate_project_id(project_id):
            return jsonify({'success': False, 'error': 'Invalid project identifier'}), 400
        
        project = Project.query.filter_by(id=project_id).first()
        if not project:
            return jsonify({'success': False, 'error': 'Project not found'}), 404
        
        # Find the causal factor
        causal_factor = CausalFactor.query.filter_by(id=factor_id, project_id=project_id).first()
        if not causal_factor:
            return jsonify({'success': False, 'error': 'Causal factor not found'}), 404
        
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        # Validate required fields
        required_fields = ['title', 'description', 'analysis_text']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'success': False, 'error': f'Missing required field: {field}'}), 400
        
        # Validate negative phrasing for title
        title = data.get('title', '').lower()
        negative_starters = ['failure of', 'inadequate', 'lack of', 'absence of', 'insufficient', 'failure to']
        has_negative_phrasing = any(title.startswith(starter) for starter in negative_starters)
        
        if not has_negative_phrasing:
            return jsonify({
                'success': False, 
                'error': 'Causal factor title must use negative phrasing (e.g., "Failure of...", "Inadequate...", "Lack of...")'
            }), 400
        
        # Update the causal factor
        causal_factor.title = data.get('title')
        causal_factor.category = data.get('category', causal_factor.category)
        causal_factor.description = data.get('description')
        causal_factor.analysis_text = data.get('analysis_text')
        causal_factor.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        current_app.logger.info(f"Updated causal factor {factor_id} for project {project_id}")
        
        return jsonify({
            'success': True,
            'message': 'Causal factor updated successfully',
            'causal_factor': {
                'id': causal_factor.id,
                'title': causal_factor.title,
                'category': causal_factor.category,
                'description': causal_factor.description,
                'analysis_text': causal_factor.analysis_text
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Error updating causal factor: {str(e)}")
        db.session.rollback()
        return jsonify({'success': False, 'error': f'Failed to update causal factor: {str(e)}'}), 500

@api_bp.route('/projects/<project_id>/extract-timeline', methods=['POST'])
@jwt_required()
def extract_timeline_from_evidence(project_id):
    """Extract timeline entries from all evidence files in a project"""
    try:
        # Validate project ID
        if not validate_project_id(project_id):
            return jsonify({'success': False, 'error': 'Invalid project identifier'}), 400
        
        project = Project.query.filter_by(id=project_id).first()
        if not project:
            return jsonify({'success': False, 'error': 'Project not found'}), 404
        
        # Check if project has evidence files
        if not project.evidence_items:
            return jsonify({
                'success': False, 
                'error': 'No evidence files found. Please upload evidence files first.'
            }), 400
        
        current_app.logger.info(f"Extracting timeline from {len(project.evidence_items)} evidence files for project {project_id}")
        
        from src.models.project_manager import ProjectManager
        from src.models.ai_assistant import AIAssistant
        
        pm = ProjectManager()
        ai = AIAssistant()
        
        all_timeline_suggestions = []
        existing_timeline = [entry.to_dict() for entry in project.timeline_entries]
        
        # Process each evidence file
        for evidence in project.evidence_items:
            try:
                # Extract content from file
                file_path = os.path.join(current_app.config.get('UPLOAD_FOLDER', 'uploads'), evidence.file_path)
                if os.path.exists(file_path):
                    content = pm._extract_file_content(file_path)
                    if content and content.strip():
                        # Get AI suggestions for this file
                        suggestions = ai.suggest_timeline_entries(content, existing_timeline)
                        if suggestions:
                            # Add source information to each suggestion
                            for suggestion in suggestions:
                                suggestion['source_file'] = evidence.original_filename
                                suggestion['evidence_id'] = evidence.id
                            all_timeline_suggestions.extend(suggestions)
                        
                        current_app.logger.info(f"Extracted {len(suggestions) if suggestions else 0} suggestions from {evidence.original_filename}")
                    else:
                        current_app.logger.warning(f"No content extracted from {evidence.original_filename}")
                else:
                    current_app.logger.warning(f"File not found: {file_path}")
                    
            except Exception as file_error:
                current_app.logger.error(f"Error processing evidence file {evidence.original_filename}: {str(file_error)}")
                continue
        
        # Remove duplicates based on description similarity
        unique_suggestions = []
        seen_descriptions = set()
        
        for suggestion in all_timeline_suggestions:
            description_lower = suggestion.get('description', '').lower().strip()
            if description_lower and description_lower not in seen_descriptions:
                seen_descriptions.add(description_lower)
                unique_suggestions.append(suggestion)
        
        current_app.logger.info(f"Found {len(unique_suggestions)} unique timeline suggestions from {len(project.evidence_items)} evidence files")
        
        return jsonify({
            'success': True,
            'timeline_suggestions': unique_suggestions,
            'message': f'Analyzed {len(project.evidence_items)} evidence files and found {len(unique_suggestions)} potential timeline entries.'
        })
        
    except Exception as e:
        current_app.logger.error(f"Error extracting timeline from evidence for project {project_id}: {str(e)}")
        return jsonify({'success': False, 'error': f'Failed to extract timeline: {str(e)}'}), 500

@api_bp.route('/projects/<project_id>/generate-roi', methods=['POST'])
@jwt_required()
def generate_roi(project_id):
    """Generate ROI document"""
    try:
        # Validate project ID
        if not validate_project_id(project_id):
            return jsonify({'success': False, 'error': 'Invalid project identifier'}), 400
        
        project = Project.query.filter_by(id=project_id).first()
        if not project:
            return jsonify({'success': False, 'error': 'Project not found'}), 404
        
        # Check if project has sufficient data for ROI generation
        if not project.timeline_entries:
            return jsonify({
                'success': False, 
                'error': 'Project must have timeline entries before generating ROI document'
            }), 400
        
        current_app.logger.info(f"Starting ROI generation for project {project_id}")
        
        # Convert database models to InvestigationProject format
        from src.models.roi_converter import DatabaseToROIConverter
        converter = DatabaseToROIConverter()
        investigation_project = converter.convert_project(project)
        
        current_app.logger.info(f"Converted project data: {len(investigation_project.timeline)} timeline entries, {len(investigation_project.causal_factors)} causal factors")
        
        # Create exports directory
        uploads_dir = current_app.config.get('UPLOAD_FOLDER', 'uploads')
        exports_dir = os.path.join(uploads_dir, f'project_{project_id}', 'exports')
        os.makedirs(exports_dir, exist_ok=True)
        
        # Generate output filename
        safe_title = "".join(c for c in project.title if c.isalnum() or c in (' ', '-', '_')).rstrip()
        safe_title = safe_title.replace(' ', '_')[:50]  # Limit length
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        output_filename = f"ROI_{safe_title}_{timestamp}.docx"
        output_path = os.path.join(exports_dir, output_filename)
        
        current_app.logger.info(f"Generating ROI document at: {output_path}")
        
        # Generate USCG-compliant ROI document
        uscg_roi_generator.generate_roi(investigation_project, output_path)
        
        current_app.logger.info(f"ROI document generated successfully: {output_path}")
        
        # Generate download URL (use dedicated ROI download endpoint)
        download_url = f'/api/projects/{project_id}/download-roi'
        
        return jsonify({
            'success': True,
            'message': 'ROI document generated successfully',
            'file_path': output_path,
            'filename': output_filename,
            'download_url': download_url,
            'project_details': {
                'timeline_entries': len(project.timeline_entries),
                'evidence_items': len(project.evidence_items),
                'causal_factors': len(project.causal_factors)
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Error generating ROI for project {project_id}: {str(e)}")
        import traceback
        current_app.logger.error(f"Full traceback: {traceback.format_exc()}")
        return jsonify({'success': False, 'error': f'Failed to generate ROI document: {str(e)}'}), 500

@api_bp.route('/projects/<project_id>/download-roi', methods=['GET'])
@jwt_required()
def download_roi(project_id):
    """Download generated ROI document"""
    try:
        # Validate project ID
        if not validate_project_id(project_id):
            return jsonify({'success': False, 'error': 'Invalid project identifier'}), 400
        
        project = Project.query.filter_by(id=project_id).first()
        if not project:
            return jsonify({'success': False, 'error': 'Project not found'}), 404
        
        # Look for the most recent ROI document in exports directory
        uploads_dir = current_app.config.get('UPLOAD_FOLDER', 'uploads')
        exports_dir = os.path.join(uploads_dir, f'project_{project_id}', 'exports')
        
        if not os.path.exists(exports_dir):
            return jsonify({
                'success': False,
                'error': 'No ROI documents have been generated for this project'
            }), 404
        
        # Find the most recent ROI file
        roi_files = [f for f in os.listdir(exports_dir) if f.startswith('ROI_') and f.endswith('.docx')]
        
        if not roi_files:
            return jsonify({
                'success': False,
                'error': 'No ROI documents found. Please generate an ROI document first.'
            }), 404
        
        # Get the most recent file (by filename timestamp)
        roi_files.sort(reverse=True)  # Most recent first
        latest_file = roi_files[0]
        file_path = os.path.join(exports_dir, latest_file)
        
        if not os.path.exists(file_path):
            return jsonify({
                'success': False,
                'error': 'ROI document file not found'
            }), 404
        
        current_app.logger.info(f"Serving ROI document: {file_path}")
        
        # Create a user-friendly download name
        safe_title = "".join(c for c in project.title if c.isalnum() or c in (' ', '-', '_')).rstrip()
        download_name = f"ROI_{safe_title.replace(' ', '_')}.docx"
        
        return send_file(file_path, as_attachment=True, download_name=download_name)
        
    except Exception as e:
        current_app.logger.error(f"Error downloading ROI for project {project_id}: {str(e)}")
        return jsonify({'success': False, 'error': f'ROI download error: {str(e)}'}), 500

@api_bp.route('/projects/<project_id>/ai-suggestions', methods=['POST'])
@jwt_required()
def get_ai_suggestions(project_id):
    """Get AI suggestions for timeline entries"""
    try:
        if not ai_assistant.client:
            return jsonify({'success': False, 'error': 'AI assistant not available'}), 400
        
        project = project_manager.load_project(project_id)
        if not project:
            return jsonify({'success': False, 'error': 'Project not found'}), 404
        
        data = request.get_json()
        evidence_text = data.get('evidence_text', '')
        
        suggestions = ai_assistant.suggest_timeline_entries(evidence_text, project.timeline)
        
        return jsonify({
            'success': True,
            'suggestions': suggestions
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/projects/<project_id>/timeline/bulk', methods=['POST'])
@jwt_required()
def add_timeline_entries_bulk(project_id):
    """Add multiple timeline entries at once (from AI suggestions)"""
    try:
        # Validate project ID
        if not validate_project_id(project_id):
            return jsonify({'success': False, 'error': 'Invalid project identifier'}), 400
        
        project = Project.query.filter_by(id=project_id).first()
        if not project:
            return jsonify({'success': False, 'error': 'Project not found'}), 404
        
        data = request.get_json()
        if not data or 'entries' not in data:
            return jsonify({'success': False, 'error': 'No entries provided'}), 400
        
        entries_data = data['entries']
        if not isinstance(entries_data, list):
            return jsonify({'success': False, 'error': 'Entries must be a list'}), 400
        
        created_entries = []
        
        current_app.logger.info(f"Processing {len(entries_data)} timeline entries for project {project_id}")
        
        for i, entry_data in enumerate(entries_data):
            try:
                current_app.logger.info(f"Processing entry {i+1}: {entry_data}")
                
                # Validate required fields
                if not entry_data.get('timestamp') or not entry_data.get('type') or not entry_data.get('description'):
                    current_app.logger.warning(f"Skipping entry {i+1}: missing required fields")
                    continue  # Skip invalid entries
                
                # Validate timestamp format
                try:
                    timestamp = datetime.fromisoformat(entry_data['timestamp'])
                except (ValueError, TypeError) as e:
                    current_app.logger.warning(f"Skipping entry {i+1}: invalid timestamp format: {e}")
                    continue  # Skip entries with invalid timestamps
                
                # Create timeline entry
                entry_id = str(uuid.uuid4())
                current_app.logger.info(f"Creating timeline entry {entry_id}")
                
                entry = TimelineEntry(
                    id=entry_id,
                    timestamp=timestamp,
                    entry_type=str(entry_data['type'])[:50],
                    description=str(entry_data['description'])[:1000],
                    confidence_level=entry_data.get('confidence_level', 'medium'),
                    is_initiating_event=bool(entry_data.get('is_initiating_event', False)),
                    project_id=project_id
                )
                
                # Set assumptions if provided
                if entry_data.get('assumptions'):
                    entry.assumptions_list = entry_data['assumptions']
                
                # Set personnel if provided
                if entry_data.get('personnel_involved'):
                    entry.personnel_involved_list = entry_data['personnel_involved']
                
                db.session.add(entry)
                created_entries.append(entry)
                current_app.logger.info(f"Successfully added entry {entry_id} to session")
                
            except Exception as e:
                current_app.logger.error(f"Error processing entry {i+1}: {e}")
                continue
        
        current_app.logger.info(f"Committing {len(created_entries)} timeline entries")
        db.session.commit()
        current_app.logger.info("Timeline entries committed successfully")
        
        return jsonify({
            'success': True,
            'created': len(created_entries),
            'entries': [entry.to_dict() for entry in created_entries]
        })
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error adding bulk timeline entries to project {project_id}: {str(e)}")
        import traceback
        current_app.logger.error(f"Full traceback: {traceback.format_exc()}")
        return jsonify({'success': False, 'error': f'Failed to add timeline entries: {str(e)}'}), 500

@api_bp.route('/projects/<project_id>/consistency-check', methods=['POST'])
@jwt_required()
def check_consistency(project_id):
    """Check project consistency"""
    try:
        project = project_manager.load_project(project_id)
        if not project:
            return jsonify({'success': False, 'error': 'Project not found'}), 404
        
        # Timeline validation
        timeline_issues = timeline_builder.validate_timeline(project)
        
        # AI consistency check if available
        ai_issues = []
        if ai_assistant.client:
            ai_issues = ai_assistant.check_consistency(project)
        
        all_issues = timeline_issues + ai_issues
        
        return jsonify({
            'success': True,
            'issues': all_issues
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/generate', methods=['POST'])
@jwt_required()
def generate_response():
    try:
        data = request.get_json()
        prompt = data.get("prompt", "")

        # Use AIAssistant class with test model
        ai_response = ai_assistant.chat(prompt)

        return jsonify({ "content": ai_response })
    except Exception as e:
        return jsonify({ "error": str(e) }), 500

@api_bp.route('/projects/<project_id>/analysis-sections', methods=['GET'])
@jwt_required()
def get_analysis_sections(project_id):
    """Get all analysis sections for a project"""
    try:
        if not validate_project_id(project_id):
            return jsonify({'success': False, 'error': 'Invalid project identifier'}), 400
        
        project = Project.query.filter_by(id=project_id).first()
        if not project:
            return jsonify({'success': False, 'error': 'Project not found'}), 404
        
        analysis_sections = AnalysisSection.query.filter_by(project_id=project_id).all()
        sections_data = [section.to_dict() for section in analysis_sections]
        
        return jsonify({
            'success': True,
            'analysis_sections': sections_data
        })
    except Exception as e:
        current_app.logger.error(f"Error getting analysis sections: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to retrieve analysis sections'}), 500

@api_bp.route('/projects/<project_id>/analysis-sections', methods=['POST'])
@jwt_required()
def create_analysis_section(project_id):
    """Create a new analysis section"""
    try:
        if not validate_project_id(project_id):
            return jsonify({'success': False, 'error': 'Invalid project identifier'}), 400
        
        project = Project.query.filter_by(id=project_id).first()
        if not project:
            return jsonify({'success': False, 'error': 'Project not found'}), 404
        
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        title = data.get('title', '').strip()
        analysis_text = data.get('analysis_text', '').strip()
        
        if not title or not analysis_text:
            return jsonify({'success': False, 'error': 'Title and analysis text are required'}), 400
        
        analysis_section = AnalysisSection(
            id=str(uuid.uuid4()),
            title=title[:200],
            analysis_text=analysis_text,
            causal_factor_id=data.get('causal_factor_id'),
            project_id=project_id
        )
        
        # Handle finding and conclusion references
        if data.get('finding_refs'):
            analysis_section.finding_refs_list = data['finding_refs']
        
        if data.get('conclusion_refs'):
            analysis_section.conclusion_refs_list = data['conclusion_refs']
        
        db.session.add(analysis_section)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'analysis_section': analysis_section.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error creating analysis section: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to create analysis section'}), 500

@api_bp.route('/projects/<project_id>/analysis-sections/<section_id>', methods=['PUT'])
@jwt_required()
def update_analysis_section(project_id, section_id):
    """Update an analysis section"""
    try:
        if not validate_project_id(project_id):
            return jsonify({'success': False, 'error': 'Invalid project identifier'}), 400
        
        analysis_section = AnalysisSection.query.filter_by(id=section_id, project_id=project_id).first()
        if not analysis_section:
            return jsonify({'success': False, 'error': 'Analysis section not found'}), 404
        
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        # Update fields
        if 'title' in data:
            title = data['title'].strip()
            if not title:
                return jsonify({'success': False, 'error': 'Title cannot be empty'}), 400
            analysis_section.title = title[:200]
        
        if 'analysis_text' in data:
            analysis_text = data['analysis_text'].strip()
            if not analysis_text:
                return jsonify({'success': False, 'error': 'Analysis text cannot be empty'}), 400
            analysis_section.analysis_text = analysis_text
        
        if 'causal_factor_id' in data:
            analysis_section.causal_factor_id = data['causal_factor_id']
        
        if 'finding_refs' in data:
            analysis_section.finding_refs_list = data['finding_refs']
        
        if 'conclusion_refs' in data:
            analysis_section.conclusion_refs_list = data['conclusion_refs']
        
        analysis_section.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'analysis_section': analysis_section.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error updating analysis section: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to update analysis section'}), 500

@api_bp.route('/projects/<project_id>/analysis-sections/<section_id>', methods=['DELETE'])
@jwt_required()
def delete_analysis_section(project_id, section_id):
    """Delete an analysis section"""
    try:
        if not validate_project_id(project_id):
            return jsonify({'success': False, 'error': 'Invalid project identifier'}), 400
        
        analysis_section = AnalysisSection.query.filter_by(id=section_id, project_id=project_id).first()
        if not analysis_section:
            return jsonify({'success': False, 'error': 'Analysis section not found'}), 404
        
        db.session.delete(analysis_section)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Analysis section deleted successfully'})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting analysis section: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to delete analysis section'}), 500


