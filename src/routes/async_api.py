"""Async API endpoints for long-running operations."""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from celery.result import AsyncResult

from src.celery_app import celery_app
from src.tasks.document_tasks import (
    generate_roi_async, 
    generate_summary_report_async,
    export_project_data_async
)
from src.tasks.ai_tasks import (
    analyze_evidence_async,
    generate_timeline_suggestions_async,
    analyze_causal_chain_async,
    generate_investigation_questions_async,
    validate_investigation_completeness_async
)
from src.tasks.file_tasks import (
    process_uploaded_file_async,
    batch_process_evidence_async,
    validate_file_integrity_async
)
from src.utils.validators import validate_project_access, validate_json_body
from src.utils.rate_limit import rate_limit

# Create blueprint
async_api_bp = Blueprint('async_api', __name__)


@async_api_bp.route('/projects/<int:project_id>/generate-roi-async', methods=['POST'])
@jwt_required()
@rate_limit(max_requests=5, window_seconds=300)  # 5 requests per 5 minutes
@validate_project_access
@validate_json_body(['format'])
def generate_roi_async_endpoint(project_id):
    """Start async ROI generation."""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        options = {
            'format': data.get('format', 'docx'),
            'include_appendices': data.get('include_appendices', False),
            'include_recommendations': data.get('include_recommendations', True)
        }
        
        # Queue the task
        task = generate_roi_async.delay(project_id, int(user_id), options)
        
        return jsonify({
            'status': 'processing',
            'task_id': task.id,
            'message': 'ROI generation started. Check task status for progress.',
            'status_url': f'/api/async/task/{task.id}/status'
        }), 202
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@async_api_bp.route('/projects/<int:project_id>/analyze-evidence-async/<int:evidence_id>', methods=['POST'])
@jwt_required()
@rate_limit(max_requests=10, window_seconds=60)
@validate_project_access
def analyze_evidence_async_endpoint(project_id, evidence_id):
    """Start async evidence analysis."""
    try:
        # Verify evidence belongs to project
        from src.models.evidence import Evidence
        evidence = Evidence.query.filter_by(id=evidence_id, project_id=project_id).first()
        if not evidence:
            return jsonify({'error': 'Evidence not found'}), 404
        
        # Queue the task
        task = analyze_evidence_async.delay(evidence_id)
        
        return jsonify({
            'status': 'processing',
            'task_id': task.id,
            'message': 'Evidence analysis started.',
            'status_url': f'/api/async/task/{task.id}/status'
        }), 202
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@async_api_bp.route('/projects/<int:project_id>/timeline-suggestions-async', methods=['POST'])
@jwt_required()
@rate_limit(max_requests=10, window_seconds=60)
@validate_project_access
def generate_timeline_suggestions_async_endpoint(project_id):
    """Start async timeline suggestion generation."""
    try:
        data = request.get_json() or {}
        
        context = {
            'focus_area': data.get('focus_area'),
            'time_range': data.get('time_range')
        }
        
        # Queue the task
        task = generate_timeline_suggestions_async.delay(project_id, context)
        
        return jsonify({
            'status': 'processing',
            'task_id': task.id,
            'message': 'Timeline suggestion generation started.',
            'status_url': f'/api/async/task/{task.id}/status'
        }), 202
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@async_api_bp.route('/projects/<int:project_id>/causal-analysis-async', methods=['POST'])
@jwt_required()
@rate_limit(max_requests=5, window_seconds=300)
@validate_project_access
def analyze_causal_chain_async_endpoint(project_id):
    """Start async causal chain analysis."""
    try:
        data = request.get_json() or {}
        incident_type = data.get('incident_type')
        
        # Queue the task
        task = analyze_causal_chain_async.delay(project_id, incident_type)
        
        return jsonify({
            'status': 'processing',
            'task_id': task.id,
            'message': 'Causal chain analysis started.',
            'status_url': f'/api/async/task/{task.id}/status'
        }), 202
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@async_api_bp.route('/projects/<int:project_id>/export-async', methods=['POST'])
@jwt_required()
@rate_limit(max_requests=5, window_seconds=300)
@validate_project_access
@validate_json_body(['format'])
def export_project_async_endpoint(project_id):
    """Start async project data export."""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        export_format = data.get('format', 'json')
        if export_format not in ['json', 'csv', 'xlsx']:
            return jsonify({'error': 'Invalid export format'}), 400
        
        # Queue the task
        task = export_project_data_async.delay(project_id, int(user_id), export_format)
        
        return jsonify({
            'status': 'processing',
            'task_id': task.id,
            'message': f'Project export to {export_format} started.',
            'status_url': f'/api/async/task/{task.id}/status'
        }), 202
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@async_api_bp.route('/projects/<int:project_id>/process-evidence-batch', methods=['POST'])
@jwt_required()
@rate_limit(max_requests=5, window_seconds=300)
@validate_project_access
def batch_process_evidence_endpoint(project_id):
    """Start batch processing of all evidence files."""
    try:
        # Queue the task
        task = batch_process_evidence_async.delay(project_id)
        
        return jsonify({
            'status': 'processing',
            'task_id': task.id,
            'message': 'Batch evidence processing started.',
            'status_url': f'/api/async/task/{task.id}/status'
        }), 202
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@async_api_bp.route('/projects/<int:project_id>/validate-completeness-async', methods=['POST'])
@jwt_required()
@rate_limit(max_requests=10, window_seconds=60)
@validate_project_access
def validate_completeness_async_endpoint(project_id):
    """Start async investigation completeness validation."""
    try:
        # Queue the task
        task = validate_investigation_completeness_async.delay(project_id)
        
        return jsonify({
            'status': 'processing',
            'task_id': task.id,
            'message': 'Investigation completeness validation started.',
            'status_url': f'/api/async/task/{task.id}/status'
        }), 202
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@async_api_bp.route('/projects/<int:project_id>/investigation-questions-async', methods=['POST'])
@jwt_required()
@rate_limit(max_requests=10, window_seconds=60)
@validate_project_access
def generate_questions_async_endpoint(project_id):
    """Start async investigation question generation."""
    try:
        # Queue the task
        task = generate_investigation_questions_async.delay(project_id)
        
        return jsonify({
            'status': 'processing',
            'task_id': task.id,
            'message': 'Investigation question generation started.',
            'status_url': f'/api/async/task/{task.id}/status'
        }), 202
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@async_api_bp.route('/task/<task_id>/status', methods=['GET'])
@jwt_required()
@rate_limit(max_requests=60, window_seconds=60)  # 1 request per second
def get_task_status(task_id):
    """Get status of an async task."""
    try:
        result = AsyncResult(task_id, app=celery_app)
        
        response = {
            'task_id': task_id,
            'state': result.state,
            'current': 0,
            'total': 1,
            'status': 'Unknown'
        }
        
        if result.state == 'PENDING':
            response['status'] = 'Task is waiting to be processed'
        elif result.state == 'STARTED':
            response['status'] = 'Task has started'
        elif result.state == 'PROGRESS':
            response['current'] = result.info.get('current', 0)
            response['total'] = result.info.get('total', 1)
            response['status'] = result.info.get('status', 'Processing...')
        elif result.state == 'SUCCESS':
            response['status'] = 'Task completed successfully'
            response['result'] = result.result
        elif result.state == 'FAILURE':
            response['status'] = 'Task failed'
            response['error'] = str(result.info)
        elif result.state == 'RETRY':
            response['status'] = 'Task is being retried'
            response['error'] = str(result.info)
        elif result.state == 'REVOKED':
            response['status'] = 'Task was cancelled'
        
        return jsonify(response)
        
    except Exception as e:
        return jsonify({
            'error': 'Failed to get task status',
            'details': str(e)
        }), 500


@async_api_bp.route('/task/<task_id>/cancel', methods=['POST'])
@jwt_required()
@rate_limit(max_requests=10, window_seconds=60)
def cancel_task(task_id):
    """Cancel an async task."""
    try:
        result = AsyncResult(task_id, app=celery_app)
        result.revoke(terminate=True)
        
        return jsonify({
            'status': 'cancelled',
            'task_id': task_id,
            'message': 'Task cancellation requested'
        })
        
    except Exception as e:
        return jsonify({
            'error': 'Failed to cancel task',
            'details': str(e)
        }), 500


@async_api_bp.route('/tasks/active', methods=['GET'])
@jwt_required()
@rate_limit(max_requests=10, window_seconds=60)
def get_active_tasks():
    """Get list of active tasks for the current user."""
    try:
        user_id = get_jwt_identity()
        
        # Get active tasks from Celery
        inspect = celery_app.control.inspect()
        active = inspect.active()
        
        if not active:
            return jsonify({'tasks': []})
        
        # Filter tasks for current user
        user_tasks = []
        for worker, tasks in active.items():
            for task in tasks:
                # Check if task belongs to user (this is a simplified check)
                # In production, you might want to store user_id in task metadata
                if 'args' in task and len(task['args']) > 1:
                    if str(task['args'][1]) == str(user_id):
                        user_tasks.append({
                            'task_id': task['id'],
                            'name': task['name'],
                            'worker': worker,
                            'args': task.get('args', []),
                            'kwargs': task.get('kwargs', {})
                        })
        
        return jsonify({'tasks': user_tasks})
        
    except Exception as e:
        return jsonify({
            'error': 'Failed to get active tasks',
            'details': str(e)
        }), 500