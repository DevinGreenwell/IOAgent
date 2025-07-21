"""Cached API endpoints for improved performance."""

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import timedelta

from src.services.cached_services import (
    CachedProjectService, 
    CachedUserService,
    CachedAIService
)
from src.middleware.cache_middleware import cache_response, skip_cache_if_admin
from src.utils.validators import validate_project_access
from src.utils.rate_limit import rate_limit

# Create blueprint
cached_api_bp = Blueprint('cached_api', __name__)

# Initialize services
ai_service = CachedAIService()


@cached_api_bp.route('/projects/<int:project_id>/summary', methods=['GET'])
@jwt_required()
@rate_limit(max_requests=60, window_seconds=60)
@validate_project_access
@cache_response(expire=timedelta(minutes=15), vary_on=['jwt'], unless=skip_cache_if_admin)
def get_project_summary(project_id):
    """Get cached project summary with statistics."""
    try:
        summary = CachedProjectService.get_project_summary(project_id)
        
        if not summary:
            return jsonify({'error': 'Project not found'}), 404
        
        return jsonify(summary)
        
    except Exception as e:
        return jsonify({
            'error': 'Failed to get project summary',
            'details': str(e)
        }), 500


@cached_api_bp.route('/projects/<int:project_id>/timeline-cached', methods=['GET'])
@jwt_required()
@rate_limit(max_requests=60, window_seconds=60)
@validate_project_access
@cache_response(expire=timedelta(minutes=30), vary_on=['jwt'])
def get_cached_timeline(project_id):
    """Get cached project timeline."""
    try:
        timeline = CachedProjectService.get_project_timeline(project_id)
        
        return jsonify({
            'timeline': timeline,
            'count': len(timeline),
            'cached': True
        })
        
    except Exception as e:
        return jsonify({
            'error': 'Failed to get timeline',
            'details': str(e)
        }), 500


@cached_api_bp.route('/projects/<int:project_id>/causal-analysis-cached', methods=['GET'])
@jwt_required()
@rate_limit(max_requests=60, window_seconds=60)
@validate_project_access
@cache_response(expire=timedelta(minutes=30), vary_on=['jwt'])
def get_cached_causal_analysis(project_id):
    """Get cached causal analysis."""
    try:
        analysis = CachedProjectService.get_causal_analysis(project_id)
        
        return jsonify({
            'analysis': analysis,
            'cached': True
        })
        
    except Exception as e:
        return jsonify({
            'error': 'Failed to get causal analysis',
            'details': str(e)
        }), 500


@cached_api_bp.route('/users/<int:user_id>/projects-cached', methods=['GET'])
@jwt_required()
@rate_limit(max_requests=30, window_seconds=60)
@cache_response(expire=timedelta(hours=1), vary_on=['jwt'])
def get_user_projects_cached(user_id):
    """Get cached list of user's projects."""
    try:
        # Verify access
        current_user_id = get_jwt_identity()
        if int(current_user_id) != user_id:
            from src.models.user import User
            user = User.query.get(int(current_user_id))
            if not user or user.role != 'admin':
                return jsonify({'error': 'Access denied'}), 403
        
        projects = CachedUserService.get_user_projects(user_id)
        
        return jsonify({
            'projects': projects,
            'count': len(projects),
            'cached': True
        })
        
    except Exception as e:
        return jsonify({
            'error': 'Failed to get user projects',
            'details': str(e)
        }), 500


@cached_api_bp.route('/users/<int:user_id>/statistics', methods=['GET'])
@jwt_required()
@rate_limit(max_requests=30, window_seconds=60)
@cache_response(expire=timedelta(hours=2), vary_on=['jwt'])
def get_user_statistics(user_id):
    """Get cached user statistics."""
    try:
        # Verify access
        current_user_id = get_jwt_identity()
        if int(current_user_id) != user_id:
            from src.models.user import User
            user = User.query.get(int(current_user_id))
            if not user or user.role != 'admin':
                return jsonify({'error': 'Access denied'}), 403
        
        stats = CachedUserService.get_user_statistics(user_id)
        
        if not stats:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify(stats)
        
    except Exception as e:
        return jsonify({
            'error': 'Failed to get user statistics',
            'details': str(e)
        }), 500


@cached_api_bp.route('/projects/<int:project_id>/ai/timeline-suggestions-cached', methods=['POST'])
@jwt_required()
@rate_limit(max_requests=10, window_seconds=300)
@validate_project_access
def get_cached_timeline_suggestions(project_id):
    """Get cached AI timeline suggestions."""
    try:
        data = request.get_json() or {}
        context = data.get('context', 'general')
        
        # This will use the @cached decorator on the service method
        suggestions = ai_service.get_timeline_suggestions(project_id, context)
        
        return jsonify({
            'suggestions': suggestions,
            'count': len(suggestions),
            'context': context,
            'cached': True
        })
        
    except Exception as e:
        return jsonify({
            'error': 'Failed to get timeline suggestions',
            'details': str(e)
        }), 500


@cached_api_bp.route('/projects/<int:project_id>/ai/causal-suggestions-cached', methods=['POST'])
@jwt_required()
@rate_limit(max_requests=10, window_seconds=300)
@validate_project_access
def get_cached_causal_suggestions(project_id):
    """Get cached AI causal analysis suggestions."""
    try:
        data = request.get_json() or {}
        incident_type = data.get('incident_type')
        
        # This will use the @cached decorator on the service method
        analysis = ai_service.get_causal_analysis_suggestions(project_id, incident_type)
        
        return jsonify({
            'analysis': analysis,
            'incident_type': incident_type,
            'cached': True
        })
        
    except Exception as e:
        return jsonify({
            'error': 'Failed to get causal analysis suggestions',
            'details': str(e)
        }), 500