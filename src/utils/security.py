"""Security utilities for IOAgent application."""

import re
import html
import secrets
from functools import wraps
from flask import request, jsonify, current_app
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from typing import Optional, Dict, Any, List
import bleach

# HTML sanitization configuration
ALLOWED_TAGS = [
    'p', 'br', 'span', 'div', 'strong', 'em', 'u', 'i', 'b',
    'ul', 'ol', 'li', 'blockquote', 'code', 'pre', 'h1', 'h2', 
    'h3', 'h4', 'h5', 'h6'
]

ALLOWED_ATTRIBUTES = {
    '*': ['class'],
    'code': ['class'],
    'pre': ['class']
}

def sanitize_html(text: str) -> str:
    """Sanitize HTML content to prevent XSS attacks."""
    if not text:
        return ""
    
    # Clean with bleach
    cleaned = bleach.clean(
        text,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        strip=True
    )
    
    return cleaned

def escape_html(text: str) -> str:
    """Escape HTML characters for safe display."""
    if not text:
        return ""
    return html.escape(text)

def validate_email(email: str) -> bool:
    """Validate email format."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def validate_password_strength(password: str) -> Dict[str, Any]:
    """Validate password strength and return detailed feedback."""
    errors = []
    
    if len(password) < 8:
        errors.append("Password must be at least 8 characters long")
    
    if not re.search(r'[A-Z]', password):
        errors.append("Password must contain at least one uppercase letter")
    
    if not re.search(r'[a-z]', password):
        errors.append("Password must contain at least one lowercase letter")
    
    if not re.search(r'\d', password):
        errors.append("Password must contain at least one number")
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        errors.append("Password must contain at least one special character")
    
    # Check for common patterns
    common_patterns = ['password', '12345', 'qwerty', 'admin']
    for pattern in common_patterns:
        if pattern.lower() in password.lower():
            errors.append(f"Password should not contain common patterns like '{pattern}'")
    
    return {
        'valid': len(errors) == 0,
        'errors': errors,
        'score': max(0, 5 - len(errors))  # Score out of 5
    }

def generate_secure_token(length: int = 32) -> str:
    """Generate a cryptographically secure random token."""
    return secrets.token_urlsafe(length)

def validate_project_access(f):
    """Decorator to validate project access for authenticated users."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        verify_jwt_in_request()
        
        # Get project_id from route parameters
        project_id = kwargs.get('project_id')
        if not project_id:
            return jsonify({'success': False, 'error': 'Project ID required'}), 400
        
        # Get current user
        user_id = get_jwt_identity()
        
        # Import here to avoid circular imports
        from src.models.roi_models import InvestigationProject
        
        # Check if project exists and belongs to user
        project = InvestigationProject.query.filter_by(
            id=project_id,
            user_id=user_id
        ).first()
        
        if not project:
            return jsonify({'success': False, 'error': 'Project not found or access denied'}), 404
        
        # Add project to kwargs for use in the route
        kwargs['project'] = project
        
        return f(*args, **kwargs)
    
    return decorated_function

def rate_limit_key():
    """Generate rate limit key based on IP and user."""
    identity = get_jwt_identity() if request.headers.get('Authorization') else None
    ip = request.remote_addr
    
    if identity:
        return f"user:{identity}"
    return f"ip:{ip}"

def sanitize_filename(filename: str) -> str:
    """Sanitize filename to prevent path traversal attacks."""
    # Remove any directory components
    filename = filename.replace('..', '').replace('/', '').replace('\\', '')
    
    # Remove any non-alphanumeric characters except dots, hyphens, and underscores
    filename = re.sub(r'[^a-zA-Z0-9._-]', '_', filename)
    
    # Limit length
    name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
    if len(name) > 100:
        name = name[:100]
    
    return f"{name}.{ext}" if ext else name

def validate_json_request(required_fields: List[str]):
    """Decorator to validate JSON request has required fields."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not request.is_json:
                return jsonify({'success': False, 'error': 'Content-Type must be application/json'}), 400
            
            data = request.get_json()
            if not data:
                return jsonify({'success': False, 'error': 'Invalid JSON data'}), 400
            
            missing_fields = [field for field in required_fields if field not in data or not data[field]]
            if missing_fields:
                return jsonify({
                    'success': False, 
                    'error': f'Missing required fields: {", ".join(missing_fields)}'
                }), 400
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator

def generate_csrf_token() -> str:
    """Generate a CSRF token for forms."""
    return secrets.token_hex(16)

def validate_csrf_token(token: str, stored_token: str) -> bool:
    """Validate CSRF token using constant-time comparison."""
    return secrets.compare_digest(token, stored_token)

# Content Security Policy headers
def get_security_headers() -> Dict[str, str]:
    """Get security headers for responses."""
    return {
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'DENY',
        'X-XSS-Protection': '1; mode=block',
        'Referrer-Policy': 'strict-origin-when-cross-origin',
        'Permissions-Policy': 'geolocation=(), microphone=(), camera=()',
        'Content-Security-Policy': (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; "
            "font-src 'self' https://cdnjs.cloudflare.com; "
            "img-src 'self' data: https:; "
            "connect-src 'self';"
        )
    }