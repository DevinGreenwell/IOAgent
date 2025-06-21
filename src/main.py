import os
import sys
import secrets
# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, send_from_directory
from flask_cors import CORS
from src.models.user import db
from src.routes.user import user_bp
from src.routes.api import api_bp

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))

# Use environment variable for secret key, generate secure fallback
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or secrets.token_hex(32)

# Configure CORS more securely - restrict origins in production
cors_origins = os.environ.get('CORS_ORIGINS', 'http://localhost:3000,http://127.0.0.1:5000').split(',')
CORS(app, origins=cors_origins)

# Register API blueprints FIRST (order matters!)
app.register_blueprint(api_bp, url_prefix='/api')
app.register_blueprint(user_bp, url_prefix='/api')

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(os.path.dirname(__file__), 'database', 'app.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# Create database tables
# Add security headers
@app.after_request
def add_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data:;"
    return response

with app.app_context():
    # Ensure database directory exists
    db_dir = os.path.join(os.path.dirname(__file__), 'database')
    os.makedirs(db_dir, exist_ok=True)
    db.create_all()

# Static file serving routes (these should come AFTER API routes)
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    static_folder_path = app.static_folder
    if static_folder_path is None:
        return "Static folder not configured", 404

    # Prevent path traversal attacks
    if path and '..' in path:
        return "Invalid path", 403
    
    # Normalize the path to prevent directory traversal
    if path:
        safe_path = os.path.normpath(path)
        if safe_path.startswith('..') or os.path.isabs(safe_path):
            return "Invalid path", 403
        
        full_path = os.path.join(static_folder_path, safe_path)
        # Ensure the resolved path is within the static folder
        if not full_path.startswith(os.path.abspath(static_folder_path)):
            return "Invalid path", 403
            
        if os.path.exists(full_path) and os.path.isfile(full_path):
            return send_from_directory(static_folder_path, safe_path)
    
    # For SPA routing, always serve index.html for non-API routes
    index_path = os.path.join(static_folder_path, 'index.html')
    if os.path.exists(index_path):
        return send_from_directory(static_folder_path, 'index.html')
    else:
        return "index.html not found", 404

if __name__ == '__main__':
    # Disable debug mode in production
    debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(host='0.0.0.0', port=5000, debug=debug_mode)