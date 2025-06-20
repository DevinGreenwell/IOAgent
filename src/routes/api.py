# Flask routes for IOAgent API endpoints

from flask import Blueprint, request, jsonify, send_file
from werkzeug.utils import secure_filename
import os
import json
from datetime import datetime

from src.models.project_manager import ProjectManager, TimelineBuilder
from src.models.roi_generator import ROIGenerator, CausalAnalysisEngine
from src.models.ai_assistant import AIAssistant

# Create blueprint
api_bp = Blueprint('api', __name__)

# Initialize managers
project_manager = ProjectManager()
timeline_builder = TimelineBuilder()
roi_generator = ROIGenerator()
causal_engine = CausalAnalysisEngine()
ai_assistant = AIAssistant()

@api_bp.route('/projects', methods=['GET'])
def list_projects():
    """List all projects"""
    try:
        projects = project_manager.list_projects()
        return jsonify({'success': True, 'projects': projects})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/projects', methods=['POST'])
def create_project():
    """Create a new project"""
    try:
        data = request.get_json()
        title = data.get('title', 'Untitled Investigation')
        investigating_officer = data.get('investigating_officer', '')
        
        project = project_manager.create_project(title, investigating_officer)
        
        return jsonify({
            'success': True,
            'project': {
                'id': project.id,
                'title': project.metadata.title,
                'status': project.metadata.status,
                'created_at': project.metadata.created_at.isoformat()
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/projects/<project_id>', methods=['GET'])
def get_project(project_id):
    """Get project details"""
    try:
        project = project_manager.load_project(project_id)
        if not project:
            return jsonify({'success': False, 'error': 'Project not found'}), 404
        
        return jsonify({'success': True, 'project': project.to_dict()})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/projects/<project_id>', methods=['PUT'])
def update_project(project_id):
    """Update project"""
    try:
        project = project_manager.load_project(project_id)
        if not project:
            return jsonify({'success': False, 'error': 'Project not found'}), 404
        
        data = request.get_json()
        
        # Update metadata
        if 'title' in data:
            project.metadata.title = data['title']
        if 'investigating_officer' in data:
            project.metadata.investigating_officer = data['investigating_officer']
        if 'status' in data:
            project.metadata.status = data['status']
        
        # Update incident info
        if 'incident_info' in data:
            incident_data = data['incident_info']
            if 'incident_date' in incident_data:
                project.incident_info.incident_date = datetime.fromisoformat(incident_data['incident_date'])
            if 'location' in incident_data:
                project.incident_info.location = incident_data['location']
            if 'incident_type' in incident_data:
                project.incident_info.incident_type = incident_data['incident_type']
        
        project_manager.save_project(project)
        
        return jsonify({'success': True, 'project': project.to_dict()})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/projects/<project_id>', methods=['DELETE'])
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
def upload_file(project_id):
    """Upload file to project"""
    try:
        project = project_manager.load_project(project_id)
        if not project:
            return jsonify({'success': False, 'error': 'Project not found'}), 404
        
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file provided'}), 400
        
        file = request.files['file']
        description = request.form.get('description', '')
        
        evidence = project_manager.upload_file(project_id, file, description)
        if evidence:
            project.evidence_library.append(evidence)
            project_manager.save_project(project)
            
            return jsonify({
                'success': True,
                'evidence': evidence.to_dict()
            })
        else:
            return jsonify({'success': False, 'error': 'Failed to upload file'}), 500
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/projects/<project_id>/timeline', methods=['POST'])
def add_timeline_entry(project_id):
    """Add timeline entry"""
    try:
        project = project_manager.load_project(project_id)
        if not project:
            return jsonify({'success': False, 'error': 'Project not found'}), 404
        
        data = request.get_json()
        entry = timeline_builder.add_entry(project, data)
        timeline_builder.sort_timeline(project)
        project_manager.save_project(project)
        
        return jsonify({'success': True, 'entry': entry.to_dict()})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/projects/<project_id>/timeline/<entry_id>', methods=['PUT'])
def update_timeline_entry(project_id, entry_id):
    """Update timeline entry"""
    try:
        project = project_manager.load_project(project_id)
        if not project:
            return jsonify({'success': False, 'error': 'Project not found'}), 404
        
        # Find entry
        entry = None
        for e in project.timeline:
            if e.id == entry_id:
                entry = e
                break
        
        if not entry:
            return jsonify({'success': False, 'error': 'Timeline entry not found'}), 404
        
        data = request.get_json()
        
        # Update entry fields
        if 'timestamp' in data:
            entry.timestamp = datetime.fromisoformat(data['timestamp'])
        if 'type' in data:
            entry.type = data['type']
        if 'description' in data:
            entry.description = data['description']
        if 'evidence_ids' in data:
            entry.evidence_ids = data['evidence_ids']
        if 'assumptions' in data:
            entry.assumptions = data['assumptions']
        if 'is_initiating_event' in data:
            entry.is_initiating_event = data['is_initiating_event']
        
        timeline_builder.sort_timeline(project)
        project_manager.save_project(project)
        
        return jsonify({'success': True, 'entry': entry.to_dict()})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/projects/<project_id>/timeline/<entry_id>', methods=['DELETE'])
def delete_timeline_entry(project_id, entry_id):
    """Delete timeline entry"""
    try:
        project = project_manager.load_project(project_id)
        if not project:
            return jsonify({'success': False, 'error': 'Project not found'}), 404
        
        # Remove entry
        project.timeline = [e for e in project.timeline if e.id != entry_id]
        project_manager.save_project(project)
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/projects/<project_id>/causal-analysis', methods=['POST'])
def run_causal_analysis(project_id):
    """Run causal analysis on timeline"""
    try:
        project = project_manager.load_project(project_id)
        if not project:
            return jsonify({'success': False, 'error': 'Project not found'}), 404
        
        # Run causal analysis
        causal_factors = causal_engine.analyze_timeline(project.timeline)
        
        # Use AI to enhance analysis if available
        if ai_assistant.client:
            ai_factors = ai_assistant.identify_causal_factors(project.timeline, project.evidence_library)
            # Merge AI suggestions with engine results
            for ai_factor in ai_factors:
                from src.models.roi_models import CausalFactor
                factor = CausalFactor()
                factor.category = ai_factor.get('category', 'production')
                factor.title = ai_factor.get('title', '')
                factor.description = ai_factor.get('description', '')
                factor.analysis_text = ai_factor.get('analysis', '')
                causal_factors.append(factor)
        
        project.causal_factors = causal_factors
        project_manager.save_project(project)
        
        return jsonify({
            'success': True,
            'causal_factors': [factor.to_dict() for factor in causal_factors]
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/projects/<project_id>/generate-roi', methods=['POST'])
def generate_roi(project_id):
    """Generate ROI document"""
    try:
        project = project_manager.load_project(project_id)
        if not project:
            return jsonify({'success': False, 'error': 'Project not found'}), 404
        
        # Generate executive summary with AI if available
        if ai_assistant.client:
            summary_data = ai_assistant.generate_executive_summary(project)
            project.roi_document.executive_summary.scene_setting = summary_data.get('scene_setting', '')
            project.roi_document.executive_summary.outcomes = summary_data.get('outcomes', '')
            project.roi_document.executive_summary.causal_factors = summary_data.get('causal_factors', '')
        
        # Generate ROI document
        exports_dir = os.path.join(project_manager._get_project_dir(project_id), "exports")
        os.makedirs(exports_dir, exist_ok=True)
        
        output_path = os.path.join(exports_dir, f"ROI_{project.metadata.title.replace(' ', '_')}.docx")
        roi_generator.generate_roi(project, output_path)
        
        project_manager.save_project(project)
        
        return jsonify({
            'success': True,
            'file_path': output_path,
            'download_url': f'/api/projects/{project_id}/download-roi'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/projects/<project_id>/download-roi', methods=['GET'])
def download_roi(project_id):
    """Download generated ROI document"""
    try:
        project = project_manager.load_project(project_id)
        if not project:
            return jsonify({'success': False, 'error': 'Project not found'}), 404
        
        exports_dir = os.path.join(project_manager._get_project_dir(project_id), "exports")
        roi_file = os.path.join(exports_dir, f"ROI_{project.metadata.title.replace(' ', '_')}.docx")
        
        if not os.path.exists(roi_file):
            return jsonify({'success': False, 'error': 'ROI document not found'}), 404
        
        return send_file(roi_file, as_attachment=True, download_name=f"ROI_{project.metadata.title}.docx")
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/projects/<project_id>/ai-suggestions', methods=['POST'])
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

@api_bp.route('/projects/<project_id>/consistency-check', methods=['POST'])
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

