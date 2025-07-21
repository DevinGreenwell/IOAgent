"""Validation decorators and utilities for IOAgent application."""

from functools import wraps
from flask import request, jsonify, current_app
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from typing import Optional, List, Dict, Any, Callable
from src.utils.security import sanitize_html, escape_html

def validate_project_id(project_id: str) -> bool:
    """Validate a project ID to prevent injection attacks."""
    if not project_id or not isinstance(project_id, str):
        return False
    # Allow alphanumeric characters, hyphens, and underscores
    # Limit length to prevent buffer overflow
    if len(project_id) > 100:
        return False
    # Check for common injection patterns
    dangerous_patterns = ['..', '/', '\\', '\x00', '%00', '\n', '\r', '\t']
    for pattern in dangerous_patterns:
        if pattern in project_id:
            return False
    # Ensure it's a valid identifier format
    import re
    if not re.match(r'^[a-zA-Z0-9_-]+$', project_id):
        return False
    return True

def validate_project_access(f: Callable) -> Callable:
    """Decorator to validate project_id parameter and check access."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Get project_id from route parameters
        project_id = kwargs.get('project_id')
        
        if not project_id:
            return jsonify({'success': False, 'error': 'Project ID required'}), 400
        
        # Validate format
        from src.utils.validation_helpers import validate_project_id_format
        if not validate_project_id_format(project_id):
            return jsonify({'success': False, 'error': 'Invalid project ID format'}), 400
        
        # Verify JWT is present
        try:
            verify_jwt_in_request()
            user_id = get_jwt_identity()
        except Exception as e:
            return jsonify({'success': False, 'error': 'Authentication required'}), 401
        
        # Import here to avoid circular imports
        from src.models.user import Project
        
        # Check if project exists and belongs to user
        project = Project.query.filter_by(
            id=project_id,
            user_id=int(user_id)
        ).first()
        
        if not project:
            return jsonify({'success': False, 'error': 'Project not found or access denied'}), 404
        
        # Add project to kwargs for use in the route
        kwargs['project'] = project
        
        return f(*args, **kwargs)
    
    return decorated_function

def validate_json_body(required_fields: Optional[List[str]] = None, 
                      optional_fields: Optional[List[str]] = None,
                      sanitize_fields: Optional[List[str]] = None) -> Callable:
    """
    Decorator to validate JSON request body.
    
    Args:
        required_fields: List of required field names
        optional_fields: List of optional field names (for documentation)
        sanitize_fields: List of fields to HTML sanitize
    """
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Check content type
            if not request.is_json:
                return jsonify({
                    'success': False,
                    'error': 'Content-Type must be application/json'
                }), 400
            
            # Get JSON data
            try:
                data = request.get_json(force=True)
            except Exception:
                return jsonify({
                    'success': False,
                    'error': 'Invalid JSON data'
                }), 400
            
            if not data:
                return jsonify({
                    'success': False,
                    'error': 'No data provided'
                }), 400
            
            # Check required fields
            if required_fields:
                missing_fields = []
                for field in required_fields:
                    if field not in data:
                        missing_fields.append(field)
                    elif data[field] is None or (isinstance(data[field], str) and not data[field].strip()):
                        missing_fields.append(field)
                
                if missing_fields:
                    return jsonify({
                        'success': False,
                        'error': f'Missing or empty required fields: {", ".join(missing_fields)}'
                    }), 400
            
            # Sanitize specified fields
            if sanitize_fields:
                for field in sanitize_fields:
                    if field in data and isinstance(data[field], str):
                        data[field] = sanitize_html(data[field])
            
            # Add validated data to kwargs
            kwargs['validated_data'] = data
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator

def validate_file_upload(allowed_extensions: Optional[List[str]] = None,
                        max_size_mb: int = 16) -> Callable:
    """
    Decorator to validate file uploads.
    
    Args:
        allowed_extensions: List of allowed file extensions
        max_size_mb: Maximum file size in megabytes
    """
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'file' not in request.files:
                return jsonify({
                    'success': False,
                    'error': 'No file provided'
                }), 400
            
            file = request.files['file']
            
            if file.filename == '':
                return jsonify({
                    'success': False,
                    'error': 'No file selected'
                }), 400
            
            # Check file extension
            if allowed_extensions:
                ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
                if ext not in allowed_extensions:
                    return jsonify({
                        'success': False,
                        'error': f'File type not allowed. Allowed types: {", ".join(allowed_extensions)}'
                    }), 400
            
            # Check file size (read content length from headers)
            if request.content_length:
                max_size_bytes = max_size_mb * 1024 * 1024
                if request.content_length > max_size_bytes:
                    return jsonify({
                        'success': False,
                        'error': f'File too large. Maximum size: {max_size_mb}MB'
                    }), 400
            
            kwargs['uploaded_file'] = file
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator

def validate_pagination(max_per_page: int = 100) -> Callable:
    """
    Decorator to validate and parse pagination parameters.
    
    Args:
        max_per_page: Maximum items per page allowed
    """
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                page = int(request.args.get('page', 1))
                per_page = int(request.args.get('per_page', 20))
                
                if page < 1:
                    page = 1
                
                if per_page < 1:
                    per_page = 20
                elif per_page > max_per_page:
                    per_page = max_per_page
                
                kwargs['page'] = page
                kwargs['per_page'] = per_page
                
            except (ValueError, TypeError):
                return jsonify({
                    'success': False,
                    'error': 'Invalid pagination parameters'
                }), 400
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator

def sanitize_output(fields_to_escape: Optional[List[str]] = None) -> Callable:
    """
    Decorator to sanitize output data before sending response.
    
    Args:
        fields_to_escape: List of field names to HTML escape
    """
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args, **kwargs):
            result = f(*args, **kwargs)
            
            # If result is a tuple (response, status_code), extract response
            if isinstance(result, tuple):
                response, status_code = result
            else:
                response = result
                status_code = 200
            
            # If response is already a Response object, return as is
            if hasattr(response, 'get_json'):
                return result
            
            # Process dict responses
            if isinstance(response, dict) and fields_to_escape:
                response = _escape_fields_recursive(response, fields_to_escape)
            
            return jsonify(response), status_code
        
        return decorated_function
    return decorator

def _escape_fields_recursive(data: Any, fields_to_escape: List[str]) -> Any:
    """Recursively escape specified fields in nested data structures."""
    if isinstance(data, dict):
        result = {}
        for key, value in data.items():
            if key in fields_to_escape and isinstance(value, str):
                result[key] = escape_html(value)
            else:
                result[key] = _escape_fields_recursive(value, fields_to_escape)
        return result
    elif isinstance(data, list):
        return [_escape_fields_recursive(item, fields_to_escape) for item in data]
    else:
        return data