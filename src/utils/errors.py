"""Custom error handling for IOAgent application."""

from typing import Optional, Dict, Any, Tuple
from flask import jsonify, current_app
from werkzeug.exceptions import HTTPException
import traceback
from src.models.user import db

class IOAgentError(Exception):
    """Base exception for IOAgent application."""
    status_code = 500
    message = "An error occurred"
    
    def __init__(self, message: Optional[str] = None, status_code: Optional[int] = None, payload: Optional[Dict[str, Any]] = None):
        super().__init__()
        if message is not None:
            self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for JSON response."""
        rv = {'success': False, 'error': self.message}
        if self.payload:
            rv.update(self.payload)
        return rv

class ValidationError(IOAgentError):
    """Raised when input validation fails."""
    status_code = 400
    message = "Validation error"

class AuthenticationError(IOAgentError):
    """Raised when authentication fails."""
    status_code = 401
    message = "Authentication required"

class AuthorizationError(IOAgentError):
    """Raised when user lacks permission."""
    status_code = 403
    message = "Permission denied"

class NotFoundError(IOAgentError):
    """Raised when a resource is not found."""
    status_code = 404
    message = "Resource not found"

class ConflictError(IOAgentError):
    """Raised when there's a conflict (e.g., duplicate resource)."""
    status_code = 409
    message = "Resource conflict"

class RateLimitError(IOAgentError):
    """Raised when rate limit is exceeded."""
    status_code = 429
    message = "Rate limit exceeded"

class ExternalServiceError(IOAgentError):
    """Raised when an external service (e.g., AI API) fails."""
    status_code = 503
    message = "External service unavailable"

def handle_ioagent_error(error: IOAgentError) -> Tuple[Dict[str, Any], int]:
    """Handle IOAgent custom errors."""
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    
    # Log error details
    if error.status_code >= 500:
        current_app.logger.error(f"{error.__class__.__name__}: {error.message}")
    else:
        current_app.logger.warning(f"{error.__class__.__name__}: {error.message}")
    
    return response, error.status_code

def handle_http_exception(error: HTTPException) -> Tuple[Dict[str, Any], int]:
    """Handle werkzeug HTTP exceptions."""
    response = jsonify({
        'success': False,
        'error': error.description or str(error)
    })
    response.status_code = error.code or 500
    
    current_app.logger.warning(f"HTTP {error.code}: {error.description}")
    
    return response, error.code or 500

def handle_generic_exception(error: Exception) -> Tuple[Dict[str, Any], int]:
    """Handle unexpected exceptions."""
    # Log full traceback for debugging
    current_app.logger.error(f"Unhandled exception: {str(error)}\n{traceback.format_exc()}")
    
    # Don't expose internal details in production
    if current_app.config.get('DEBUG'):
        message = str(error)
    else:
        message = "An unexpected error occurred"
    
    response = jsonify({
        'success': False,
        'error': message
    })
    response.status_code = 500
    
    return response, 500

def register_error_handlers(app):
    """Register error handlers with Flask app."""
    app.register_error_handler(IOAgentError, handle_ioagent_error)
    app.register_error_handler(HTTPException, handle_http_exception)
    app.register_error_handler(Exception, handle_generic_exception)
    
    # Register specific HTTP error codes
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'success': False,
            'error': 'Resource not found'
        }), 404
    
    @app.errorhandler(405)
    def method_not_allowed(error):
        return jsonify({
            'success': False,
            'error': 'Method not allowed'
        }), 405
    
    @app.errorhandler(413)
    def request_entity_too_large(error):
        return jsonify({
            'success': False,
            'error': 'File too large'
        }), 413
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

class ErrorContext:
    """Context manager for consistent error handling."""
    
    def __init__(self, operation: str, rollback: bool = True):
        self.operation = operation
        self.rollback = rollback
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            return False
        
        # Handle known exceptions
        if isinstance(exc_val, IOAgentError):
            # Already properly formatted
            return False
        
        # Log the error
        current_app.logger.error(f"Error in {self.operation}: {str(exc_val)}", exc_info=True)
        
        # Rollback database if needed
        if self.rollback:
            try:
                from src.models.user import db
                db.session.rollback()
            except:
                pass
        
        # Don't suppress the exception
        return False