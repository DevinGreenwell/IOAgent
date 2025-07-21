"""Flask application factory for IOAgent."""

import os
import logging
from flask import Flask, jsonify, send_from_directory, request, Response
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from werkzeug.exceptions import NotFound

from src.config.config import get_config
from src.models.user import db
from src.utils.errors import register_error_handlers
from src.utils.security import get_security_headers


def create_app(config_name=None):
    """Create and configure Flask application."""
    # Create Flask app
    app = Flask(__name__, static_folder='static')
    
    # Load configuration
    config = get_config(config_name)
    app.config.from_object(config)
    config.init_app(app)
    
    # Initialize extensions
    db.init_app(app)
    jwt = JWTManager(app)
    migrate = Migrate(app, db)
    
    # Configure CORS
    CORS(app, origins=app.config['CORS_ORIGINS'], supports_credentials=True)
    
    # Register error handlers
    register_error_handlers(app)
    
    # Register security headers middleware
    @app.after_request
    def add_security_headers(response):
        """Add security headers to all responses."""
        for header, value in get_security_headers().items():
            response.headers[header] = value
        
        # Add HSTS in production
        if app.config.get('FLASK_ENV') == 'production':
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        
        return response
    
    # Request logging middleware
    @app.before_request
    def log_request():
        """Log incoming requests."""
        if request.endpoint != 'static':
            app.logger.info(f"{request.method} {request.path} from {request.remote_addr}")
    
    # Register blueprints
    from src.routes.auth import auth_bp
    from src.routes.api import api_bp
    from src.routes.user import user_bp
    from src.routes.async_api import async_api_bp
    from src.routes.cached_api import cached_api_bp
    from src.routes.cache_api import cache_api_bp
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(user_bp, url_prefix='/api/users')
    app.register_blueprint(async_api_bp, url_prefix='/api/async')
    app.register_blueprint(cached_api_bp, url_prefix='/api/cached')
    app.register_blueprint(cache_api_bp, url_prefix='/api/admin')
    
    # SPA route handling
    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def serve_spa(path):
        """Serve the single page application."""
        # Security check for path traversal
        if path and '..' in path:
            app.logger.warning(f"Potential path traversal attempt: {path}")
            return "Invalid path", 403
        
        # Try to serve the file if it exists
        static_folder = app.static_folder
        if path and static_folder:
            try:
                return send_from_directory(static_folder, path)
            except NotFound:
                pass
        
        # Otherwise serve index.html for SPA routing
        if static_folder:
            return send_from_directory(static_folder, 'index.html')
        
        return "Static files not configured", 500
    
    # Health check endpoint
    @app.route('/health')
    def health_check():
        """Health check endpoint for monitoring."""
        return jsonify({
            'status': 'healthy',
            'app': app.config['APP_NAME'],
            'version': app.config['VERSION'],
            'environment': app.config['FLASK_ENV']
        })
    
    # Create database tables
    with app.app_context():
        db.create_all()
        app.logger.info("Database initialized")
    
    return app