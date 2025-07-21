"""Cache management API endpoints."""

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from src.models.user import User
from src.services.cached_services import CacheStatisticsService, CachedProjectService
from src.utils.cache import cache_manager, invalidate_cache
from src.utils.rate_limit import rate_limit

# Create blueprint
cache_api_bp = Blueprint('cache_api', __name__)


@cache_api_bp.route('/cache/status', methods=['GET'])
@jwt_required()
@rate_limit(max_requests=10, window_seconds=60)
def get_cache_status():
    """Get cache status and statistics."""
    try:
        # Check if user is admin
        user_id = get_jwt_identity()
        user = User.query.get(int(user_id))
        
        if not user or user.role != 'admin':
            return jsonify({'error': 'Admin access required'}), 403
        
        # Get cache statistics
        stats = CacheStatisticsService.get_cache_info()
        
        return jsonify(stats)
        
    except Exception as e:
        return jsonify({
            'error': 'Failed to get cache status',
            'details': str(e)
        }), 500


@cache_api_bp.route('/cache/clear', methods=['POST'])
@jwt_required()
@rate_limit(max_requests=5, window_seconds=300)
def clear_cache():
    """Clear cache entries."""
    try:
        # Check if user is admin
        user_id = get_jwt_identity()
        user = User.query.get(int(user_id))
        
        if not user or user.role != 'admin':
            return jsonify({'error': 'Admin access required'}), 403
        
        data = request.get_json() or {}
        pattern = data.get('pattern')
        
        if pattern == '*':
            # Clear all cache
            success = CacheStatisticsService.clear_all_cache()
            message = 'All cache cleared' if success else 'Failed to clear cache'
        elif pattern:
            # Clear by pattern
            count = invalidate_cache(f"ioagent:{pattern}")
            message = f'Cleared {count} cache entries'
            success = True
        else:
            return jsonify({'error': 'Pattern required'}), 400
        
        return jsonify({
            'success': success,
            'message': message
        })
        
    except Exception as e:
        return jsonify({
            'error': 'Failed to clear cache',
            'details': str(e)
        }), 500


@cache_api_bp.route('/projects/<int:project_id>/cache/invalidate', methods=['POST'])
@jwt_required()
@rate_limit(max_requests=20, window_seconds=60)
def invalidate_project_cache(project_id):
    """Invalidate cache for a specific project."""
    try:
        # Verify user has access to project
        from src.models.project import Project
        user_id = get_jwt_identity()
        
        project = Project.query.get(project_id)
        if not project:
            return jsonify({'error': 'Project not found'}), 404
        
        if project.owner_id != int(user_id):
            user = User.query.get(int(user_id))
            if not user or user.role != 'admin':
                return jsonify({'error': 'Access denied'}), 403
        
        # Invalidate project cache
        CachedProjectService.invalidate_project(project_id)
        
        return jsonify({
            'success': True,
            'message': f'Cache invalidated for project {project_id}'
        })
        
    except Exception as e:
        return jsonify({
            'error': 'Failed to invalidate project cache',
            'details': str(e)
        }), 500


@cache_api_bp.route('/cache/warm/<int:project_id>', methods=['POST'])
@jwt_required()
@rate_limit(max_requests=10, window_seconds=60)
def warm_project_cache(project_id):
    """Warm up cache for a project."""
    try:
        # Verify user has access to project
        from src.models.project import Project
        user_id = get_jwt_identity()
        
        project = Project.query.get(project_id)
        if not project:
            return jsonify({'error': 'Project not found'}), 404
        
        if project.owner_id != int(user_id):
            return jsonify({'error': 'Access denied'}), 403
        
        # Warm up caches
        CachedProjectService.get_project_summary(project_id)
        CachedProjectService.get_project_timeline(project_id)
        CachedProjectService.get_causal_analysis(project_id)
        
        return jsonify({
            'success': True,
            'message': f'Cache warmed up for project {project_id}'
        })
        
    except Exception as e:
        return jsonify({
            'error': 'Failed to warm cache',
            'details': str(e)
        }), 500