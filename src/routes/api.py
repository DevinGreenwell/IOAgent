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
from src.models.roi_generator_uscg import USCGROIGenerator
# from src.models.anthropic_assistant import AnthropicAssistant
from src.utils.validators import validate_project_id, validate_project_access, validate_json_body, validate_file_upload, validate_pagination, sanitize_output
from src.utils.validation_helpers import validate_project_id_format
from src.utils.security import sanitize_html, sanitize_filename
from src.utils.rate_limit import rate_limit, API_RATE_LIMIT, UPLOAD_RATE_LIMIT

# Create blueprint
api_bp = Blueprint('api', __name__)

# Initialize managers 
project_manager = ProjectManager()
timeline_builder = TimelineBuilder()
uscg_roi_generator = USCGROIGenerator()
# ai_assistant = AnthropicAssistant()
ai_assistant = None

# Note: validate_project_id decorator is now imported from utils.validators

@api_bp.route('/projects', methods=['GET'])
@jwt_required()
@rate_limit(*API_RATE_LIMIT)
@validate_pagination(max_per_page=50)
@sanitize_output(fields_to_escape=['title', 'case_number', 'incident_location'])
def list_projects(page=1, per_page=20, **kwargs):
    """List all projects with pagination"""
    try:
        user_id = get_jwt_identity()
        projects_query = Project.query.filter_by(user_id=int(user_id))
        
        # Apply pagination
        pagination = projects_query.paginate(page=page, per_page=per_page, error_out=False)
        projects_data = [project.to_dict(include_relationships=False) for project in pagination.items]
        
        return {
            'success': True,
            'projects': projects_data,
            'pagination': {
                'page': pagination.page,
                'per_page': pagination.per_page,
                'total': pagination.total,
                'pages': pagination.pages
            }
        }
    except Exception as e:
        current_app.logger.error(f"Error listing projects: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to retrieve projects'}), 500

@api_bp.route('/projects', methods=['POST'])
@jwt_required()
@rate_limit(*API_RATE_LIMIT)
@validate_json_body(
    required_fields=['title'],
    optional_fields=['investigating_officer', 'case_number', 'incident_date', 'incident_location'],
    sanitize_fields=['title', 'investigating_officer', 'case_number', 'incident_location']
)
@sanitize_output(fields_to_escape=['title', 'case_number', 'incident_location'])
def create_project(validated_data=None, **kwargs):
    """Create a new project"""
    try:
        user_id = get_jwt_identity()
        
        # Extract and validate data
        title = validated_data.get('title', '').strip()[:200]
        investigating_officer = validated_data.get('investigating_officer', '').strip()[:100]
        case_number = validated_data.get('case_number', '').strip()[:50] if 'case_number' in validated_data else None
        incident_location = validated_data.get('incident_location', '').strip()[:200] if 'incident_location' in validated_data else None
        
        # Parse incident date if provided
        incident_date = None
        if 'incident_date' in validated_data:
            try:
                incident_date = datetime.fromisoformat(validated_data['incident_date'].replace('Z', '+00:00'))
            except (ValueError, AttributeError):
                return jsonify({'success': False, 'error': 'Invalid incident date format'}), 400
        
        # Create new project
        project = Project(
            id=str(uuid.uuid4()),
            user_id=int(user_id),
            title=title,
            investigating_officer=investigating_officer if investigating_officer else None,
            official_number=case_number,  # Fixed: Project model uses official_number, not case_number
            incident_date=incident_date,
            incident_location=incident_location,
            status='draft'
        )
        
        db.session.add(project)
        db.session.commit()
        
        return {
            'success': True,
            'project': project.to_dict(include_relationships=True)
        }
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error creating project: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to create project'}), 500

@api_bp.route('/projects/<project_id>', methods=['GET'])
@jwt_required()
@rate_limit(*API_RATE_LIMIT)
@validate_project_access
@sanitize_output(fields_to_escape=['title', 'case_number', 'incident_location'])
def get_project(project_id, project=None, **kwargs):
    """Get project details"""
    try:
        return {
            'success': True,
            'project': project.to_dict(include_relationships=True)
        }
    except Exception as e:
        current_app.logger.error(f"Error getting project {project_id}: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to retrieve project'}), 500

@api_bp.route('/projects/<project_id>', methods=['PUT'])
@jwt_required()
@rate_limit(*API_RATE_LIMIT)
@validate_project_access
@validate_json_body(
    optional_fields=['title', 'investigating_officer', 'status', 'incident_info'],
    sanitize_fields=['title', 'investigating_officer', 'incident_location', 'incident_type']
)
@sanitize_output(fields_to_escape=['title', 'case_number', 'incident_location'])
def update_project(project_id, project=None, validated_data=None, **kwargs):
    """Update project"""
    try:
        # Update basic fields
        if 'title' in validated_data and validated_data['title']:
            project.title = sanitize_html(str(validated_data['title'])[:200])
        if 'investigating_officer' in validated_data:
            project.investigating_officer = sanitize_html(str(validated_data['investigating_officer'])[:100]) if validated_data['investigating_officer'] else None
        if 'status' in validated_data:
            from src.utils.validation_helpers import validate_project_status
            if validate_project_status(validated_data['status']):
                project.status = validated_data['status']
            else:
                return jsonify({'success': False, 'error': 'Invalid project status'}), 400
        
        # Update incident info
        if 'incident_info' in validated_data:
            incident_data = validated_data['incident_info']
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
            if 'official_number' in incident_data:
                project.official_number = str(incident_data['official_number'])[:50] if incident_data['official_number'] else None
        
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
        allowed_extensions = {'.pdf', '.txt', '.doc', '.docx', '.csv', '.xlsx'}
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
        # from src.models.anthropic_assistant import AnthropicAssistant
        from src.models.project_manager import ProjectManager
        
        # Extract content from saved file
        pm = ProjectManager()
        content = pm._extract_file_content(file_path)
        
        # Don't extract timeline on upload - files are now part of knowledge bank
        # Timeline extraction happens when user clicks "Extract Timeline" button
        
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
            'message': f'File {evidence.original_filename} added to knowledge bank successfully.'
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
        
        # CRITICAL: Check for initiating event (USCG requirement per MCI-O3B Section 3.2)
        initiating_events = [entry for entry in timeline_entries if entry.is_initiating_event]
        if not initiating_events:
            return jsonify({
                'success': False, 
                'error': 'You must identify the Initiating Event (first adverse outcome) in the timeline before running causal analysis. Check the "Initiating Event" box for the appropriate timeline entry.'
            }), 400
        
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
        
        # Use AI for causal analysis
        ai_factors = []
        if ai_assistant.client:
            try:
                ai_factors = ai_assistant.identify_causal_factors(timeline_objects, evidence_objects)
                current_app.logger.info(f"AI assistant identified {len(ai_factors)} factors")
            except Exception as ai_error:
                current_app.logger.warning(f"AI analysis failed: {ai_error}")
        
        # Create CausalFactor database records
        created_factors = []
        
        # Create causal factor database records from AI analysis
        for factor_data in ai_factors:
            try:
                factor = CausalFactor(
                    id=str(uuid.uuid4()),
                    title=str(factor_data.get('title', 'Unknown Factor'))[:200],
                    description=str(factor_data.get('description', ''))[:1000],
                    category=factor_data.get('category', 'organizational'),
                    severity=factor_data.get('severity', 'medium'),
                    likelihood=factor_data.get('likelihood', 'medium'),
                    analysis_text=str(factor_data.get('analysis_text', factor_data.get('analysis', ''))),
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

@api_bp.route('/projects/<project_id>/generate-findings', methods=['POST'])
@jwt_required()
def generate_findings_from_timeline(project_id):
    """Generate professional findings of fact from timeline"""
    try:
        if not validate_project_id(project_id):
            return jsonify({'success': False, 'error': 'Invalid project identifier'}), 400
        
        project = Project.query.filter_by(id=project_id).first()
        if not project:
            return jsonify({'success': False, 'error': 'Project not found'}), 404
        
        # Get timeline entries
        timeline_entries = project.timeline_entries
        if not timeline_entries:
            return jsonify({'success': False, 'error': 'No timeline entries found'}), 400
        
        # Convert to wrapper objects for AI processing
        class TimelineEntryWrapper:
            def __init__(self, entry_dict):
                self.timestamp = datetime.fromisoformat(entry_dict['timestamp']) if entry_dict.get('timestamp') else datetime.utcnow()
                self.type = entry_dict.get('type', 'event')
                self.description = entry_dict.get('description', '')
                self.id = entry_dict.get('id', '')
        
        class EvidenceWrapper:
            def __init__(self, evidence_dict):
                self.type = evidence_dict.get('type', 'document')
                self.description = evidence_dict.get('description', '')
                self.source = evidence_dict.get('source', 'user_upload')
        
        timeline_objects = [TimelineEntryWrapper(entry.to_dict()) for entry in timeline_entries]
        evidence_objects = [EvidenceWrapper(item.to_dict()) for item in project.evidence_items]
        
        # Use AI to generate professional findings
        findings_statements = []
        if ai_assistant.client:
            try:
                findings_statements = ai_assistant.generate_findings_of_fact_from_timeline(timeline_objects, evidence_objects)
                current_app.logger.info(f"Generated {len(findings_statements)} findings statements")
            except Exception as ai_error:
                current_app.logger.warning(f"AI findings generation failed: {ai_error}")
        
        if not findings_statements:
            # Fallback to basic conversion
            findings_statements = []
            for i, entry in enumerate(sorted(timeline_entries, key=lambda x: x.timestamp or datetime.min), 1):
                time_str = entry.timestamp.strftime("%B %d, %Y, at %H%M") if entry.timestamp else "At an unknown time"
                findings_statements.append(f"4.1.{i}. On {time_str}, {entry.description}")
        
        return jsonify({
            'success': True,
            'findings': findings_statements,
            'message': f'Generated {len(findings_statements)} findings of fact statements.'
        })
        
    except Exception as e:
        current_app.logger.error(f"Error generating findings for project {project_id}: {str(e)}")
        return jsonify({'success': False, 'error': f'Failed to generate findings: {str(e)}'}), 500

@api_bp.route('/projects/<project_id>/causal-factors/<factor_id>', methods=['DELETE'])
@jwt_required()
def delete_causal_factor(project_id, factor_id):
    """Delete a causal factor"""
    try:
        # Validate project ID
        if not validate_project_id(project_id):
            return jsonify({'success': False, 'error': 'Invalid project identifier'}), 400
        
        causal_factor = CausalFactor.query.filter_by(id=factor_id, project_id=project_id).first()
        if not causal_factor:
            return jsonify({'success': False, 'error': 'Causal factor not found'}), 404
        
        db.session.delete(causal_factor)
        db.session.commit()
        
        current_app.logger.info(f"Deleted causal factor {factor_id} from project {project_id}")
        
        return jsonify({
            'success': True,
            'message': 'Causal factor deleted successfully'
        })
        
    except Exception as e:
        current_app.logger.error(f"Error deleting causal factor: {str(e)}")
        db.session.rollback()
        return jsonify({'success': False, 'error': f'Failed to delete causal factor: {str(e)}'}), 500

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
        # from src.models.anthropic_assistant import AnthropicAssistant
        
        pm = ProjectManager()
        # ai = AnthropicAssistant()
        ai = None
        
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
        
        # Log all suggestions before deduplication
        current_app.logger.info(f"Total timeline suggestions before deduplication: {len(all_timeline_suggestions)}")
        for i, suggestion in enumerate(all_timeline_suggestions):
            description = suggestion.get('description', '')
            current_app.logger.info(f"Suggestion {i+1}: '{description[:100]}...' (source: {suggestion.get('source_file', 'unknown')})")
        
        # Remove duplicates based on description similarity
        unique_suggestions = []
        seen_descriptions = set()
        
        for suggestion in all_timeline_suggestions:
            description_lower = suggestion.get('description', '').lower().strip()
            if description_lower and description_lower not in seen_descriptions:
                seen_descriptions.add(description_lower)
                unique_suggestions.append(suggestion)
            else:
                current_app.logger.info(f"Filtered duplicate: '{description_lower[:50]}...'")
        
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

@api_bp.route('/projects/<project_id>/generate-roi-direct', methods=['POST'])
@jwt_required()
def generate_roi_direct(project_id):
    """Generate ROI document directly from uploaded evidence files using AI - bypasses timeline/analysis workflow"""
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
                'error': 'Project must have evidence files uploaded to generate ROI directly'
            }), 400
        
        current_app.logger.info(f"Starting DIRECT ROI generation for project {project_id} from {len(project.evidence_items)} evidence files")
        
        # Convert database models to InvestigationProject format
        from src.models.roi_converter import DatabaseToROIConverter
        converter = DatabaseToROIConverter()
        investigation_project = converter.convert_project(project)
        
        # Create exports directory
        uploads_dir = current_app.config.get('UPLOAD_FOLDER', 'uploads')
        exports_dir = os.path.join(uploads_dir, f'project_{project_id}', 'exports')
        os.makedirs(exports_dir, exist_ok=True)
        
        # Generate output filename
        safe_title = "".join(c for c in project.title if c.isalnum() or c in (' ', '-', '_')).rstrip()
        safe_title = safe_title.replace(' ', '_')[:50]  # Limit length
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        output_filename = f"ROI_Direct_{safe_title}_{timestamp}.docx"
        output_path = os.path.join(exports_dir, output_filename)
        
        current_app.logger.info(f"Generating DIRECT ROI document at: {output_path}")
        
        # Generate ROI directly from evidence using AI
        uscg_roi_generator.generate_roi_from_evidence_only(investigation_project, output_path)
        
        current_app.logger.info(f"DIRECT ROI document generated successfully: {output_path}")
        
        # Generate download URL
        download_url = f'/api/projects/{project_id}/download-roi'
        
        return jsonify({
            'success': True,
            'message': 'ROI document generated directly from evidence files using AI',
            'file_path': output_path,
            'filename': output_filename,
            'download_url': download_url,
            'generation_method': 'direct_from_evidence',
            'project_details': {
                'evidence_items': len(project.evidence_items),
                'ai_powered': True
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Error generating DIRECT ROI for project {project_id}: {str(e)}")
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
        
        # Validate category based on event type (USCG requirement)
        event_type = data.get('event_type', 'initiating')
        category = data.get('category', 'organization')
        
        if event_type == 'subsequent' and category != 'defense':
            return jsonify({
                'success': False, 
                'error': 'Subsequent events can ONLY have defense factors (per USCG MCI-O3B requirements)'
            }), 400
        
        analysis_section = AnalysisSection(
            id=str(uuid.uuid4()),
            title=title[:200],
            event_type=event_type,
            category=category,
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
        
        # Handle event_type and category validation (USCG requirement)
        if 'event_type' in data:
            analysis_section.event_type = data['event_type']
        
        if 'category' in data:
            # Validate category based on event type
            new_category = data['category']
            current_event_type = data.get('event_type', analysis_section.event_type)
            
            if current_event_type == 'subsequent' and new_category != 'defense':
                return jsonify({
                    'success': False, 
                    'error': 'Subsequent events can ONLY have defense factors (per USCG MCI-O3B requirements)'
                }), 400
                
            analysis_section.category = new_category
        
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


