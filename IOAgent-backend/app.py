import os
import sys
import secrets
import logging
from datetime import datetime
from werkzeug.utils import secure_filename
from werkzeug.exceptions import RequestEntityTooLarge

# Add the parent directory to Python path to import from src
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, send_from_directory, jsonify, request
from flask_cors import CORS
from src.models.user import db
from src.routes.user import user_bp
from src.routes.api import api_bp

# Initialize Flask app
app = Flask(__name__, static_folder=os.path.dirname(__file__))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Security configuration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or secrets.token_hex(32)
app.config['SESSION_COOKIE_SECURE'] = os.environ.get('FLASK_ENV') == 'production'
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# File upload configuration
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
ALLOWED_EXTENSIONS = {
    'pdf': 'application/pdf',
    'doc': 'application/msword',
    'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'png': 'image/png',
    'jpg': 'image/jpeg',
    'jpeg': 'image/jpeg',
    'gif': 'image/gif',
    'mp4': 'video/mp4',
    'avi': 'video/x-msvideo',
    'mp3': 'audio/mpeg',
    'wav': 'audio/wav',
    'txt': 'text/plain'
}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Create upload directory if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
logger.info(f"Upload folder created/verified at: {UPLOAD_FOLDER}")

# Configure CORS
cors_origins = os.environ.get(
    'CORS_ORIGINS', 
    'http://localhost:3000,http://127.0.0.1:5000,http://localhost:5000,https://devingreenwell.github.io'
).split(',')
CORS(app, origins=cors_origins, supports_credentials=True)

# Database configuration
db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src', 'database', 'app.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{db_path}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_pre_ping': True,
    'pool_recycle': 300,
}

# Initialize database
db.init_app(app)

# Helper functions
def allowed_file(filename):
    """Check if the file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_file_type(filename):
    """Get MIME type for a given filename"""
    ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
    return ALLOWED_EXTENSIONS.get(ext, 'application/octet-stream')

def generate_unique_filename(original_filename):
    """Generate a unique filename to prevent collisions"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    safe_filename = secure_filename(original_filename)
    name, ext = os.path.splitext(safe_filename)
    # Limit filename length
    name = name[:50] if len(name) > 50 else name
    return f"{timestamp}_{name}{ext}"

# Error handlers
@app.errorhandler(413)
@app.errorhandler(RequestEntityTooLarge)
def handle_file_too_large(e):
    """Handle file too large errors"""
    return jsonify({
        'success': False,
        'error': 'File too large. Maximum file size is 16MB.'
    }), 413

@app.errorhandler(404)
def handle_not_found(e):
    """Handle 404 errors"""
    # If it's an API route, return JSON
    if request.path.startswith('/api/'):
        return jsonify({
            'success': False,
            'error': 'Endpoint not found'
        }), 404
    # Otherwise, serve the SPA
    return send_from_directory(app.static_folder, 'index.html')

@app.errorhandler(500)
def handle_internal_error(e):
    """Handle internal server errors"""
    logger.error(f"Internal server error: {str(e)}")
    return jsonify({
        'success': False,
        'error': 'Internal server error'
    }), 500

# Register API blueprints
app.register_blueprint(api_bp, url_prefix='/api')
app.register_blueprint(user_bp, url_prefix='/api')

# File upload endpoint
@app.route('/api/projects/<project_id>/upload', methods=['POST'])
def upload_file(project_id):
    """Handle file uploads for a project"""
    try:
        # Check if project exists (you'll need to implement this)
        # project = Project.query.get(project_id)
        # if not project:
        #     return jsonify({'success': False, 'error': 'Project not found'}), 404
        
        # Check if file is in request
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file provided'}), 400
        
        file = request.files['file']
        
        # Check if file is selected
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400
        
        # Validate file
        if not allowed_file(file.filename):
            return jsonify({
                'success': False, 
                'error': f'File type not allowed. Allowed types: {", ".join(ALLOWED_EXTENSIONS.keys())}'
            }), 400
        
        # Generate unique filename
        original_filename = file.filename
        unique_filename = generate_unique_filename(original_filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        
        # Create project-specific subfolder
        project_folder = os.path.join(app.config['UPLOAD_FOLDER'], f'project_{project_id}')
        os.makedirs(project_folder, exist_ok=True)
        filepath = os.path.join(project_folder, unique_filename)
        
        # Save file
        file.save(filepath)
        logger.info(f"File saved: {filepath}")
        
        # Get additional metadata from request
        description = request.form.get('description', f'Uploaded file: {original_filename}')
        file_type = request.form.get('type', get_file_type(original_filename))
        source = request.form.get('source', 'user_upload')
        
        # Here you would typically:
        # 1. Create an Evidence record in the database
        # 2. Associate it with the project
        # 3. Store metadata like file size, upload time, etc.
        
        # For now, return success with file info
        file_info = {
            'id': secrets.token_urlsafe(16),  # Generate a unique ID
            'filename': original_filename,
            'stored_filename': unique_filename,
            'description': description,
            'type': file_type,
            'source': source,
            'size': os.path.getsize(filepath),
            'uploaded_at': datetime.now().isoformat(),
            'project_id': project_id
        }
        
        return jsonify({
            'success': True,
            'file': file_info,
            'message': f'File {original_filename} uploaded successfully'
        }), 200
        
    except RequestEntityTooLarge:
        return jsonify({
            'success': False,
            'error': 'File too large. Maximum file size is 16MB.'
        }), 413
    except Exception as e:
        logger.error(f"Error uploading file: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Error uploading file: {str(e)}'
        }), 500

# File download endpoint
@app.route('/api/projects/<project_id>/download/<filename>', methods=['GET'])
def download_file(project_id, filename):
    """Handle file downloads"""
    try:
        # Validate filename to prevent directory traversal
        safe_filename = secure_filename(filename)
        project_folder = os.path.join(app.config['UPLOAD_FOLDER'], f'project_{project_id}')
        
        # Check if file exists
        filepath = os.path.join(project_folder, safe_filename)
        if not os.path.exists(filepath):
            return jsonify({'success': False, 'error': 'File not found'}), 404
        
        # Send file
        return send_from_directory(project_folder, safe_filename, as_attachment=True)
        
    except Exception as e:
        logger.error(f"Error downloading file: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Error downloading file: {str(e)}'
        }), 500

# Delete file endpoint
@app.route('/api/projects/<project_id>/evidence/<evidence_id>', methods=['DELETE'])
def delete_evidence(project_id, evidence_id):
    """Delete evidence file"""
    try:
        # Here you would:
        # 1. Check if the evidence exists in the database
        # 2. Get the filename associated with the evidence
        # 3. Delete the physical file
        # 4. Remove the database record
        
        # For now, return success
        return jsonify({
            'success': True,
            'message': 'Evidence deleted successfully'
        }), 200
        
    except Exception as e:
        logger.error(f"Error deleting evidence: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Error deleting evidence: {str(e)}'
        }), 500

# Delete timeline entry endpoint
@app.route('/api/projects/<project_id>/timeline/<entry_id>', methods=['DELETE'])
def delete_timeline_entry(project_id, entry_id):
    """Delete timeline entry"""
    try:
        # Here you would:
        # 1. Check if the timeline entry exists
        # 2. Remove it from the project's timeline
        # 3. Update the database
        
        return jsonify({
            'success': True,
            'message': 'Timeline entry deleted successfully'
        }), 200
        
    except Exception as e:
        logger.error(f"Error deleting timeline entry: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Error deleting timeline entry: {str(e)}'
        }), 500

# Security headers middleware
@app.after_request
def add_security_headers(response):
    """Add security headers to all responses"""
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    
    # Only add HSTS in production
    if os.environ.get('FLASK_ENV') == 'production':
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    
    # More permissive CSP for development
    if os.environ.get('FLASK_ENV') == 'production':
        response.headers['Content-Security-Policy'] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "font-src 'self' https://cdn.jsdelivr.net; "
            "img-src 'self' data: https:; "
            "connect-src 'self';"
        )
    
    return response

# Request logging middleware
@app.before_request
def log_request():
    """Log incoming requests"""
    if request.path.startswith('/api/'):
        logger.info(f"{request.method} {request.path} from {request.remote_addr}")

# Database initialization
with app.app_context():
    # Ensure database directory exists
    db_dir = os.path.dirname(db_path)
    os.makedirs(db_dir, exist_ok=True)
    
    # Create tables
    db.create_all()
    logger.info("Database initialized")

# Static file serving routes (these should come AFTER API routes)
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    """Serve static files and handle SPA routing"""
    static_folder_path = app.static_folder
    if static_folder_path is None:
        return "Static folder not configured", 500

    # Security: Prevent path traversal attacks
    if path and '..' in path:
        logger.warning(f"Potential path traversal attempt: {path}")
        return "Invalid path", 403
    
    # Normalize the path
    if path:
        # Remove any leading slashes and normalize
        safe_path = os.path.normpath(path).lstrip('/')
        
        # Additional security check
        if safe_path.startswith('..') or os.path.isabs(safe_path):
            logger.warning(f"Invalid path attempt: {safe_path}")
            return "Invalid path", 403
        
        # Construct full path
        full_path = os.path.join(static_folder_path, safe_path)
        
        # Ensure the resolved path is within the static folder
        try:
            full_path = os.path.realpath(full_path)
            static_folder_real = os.path.realpath(static_folder_path)
            if not full_path.startswith(static_folder_real):
                logger.warning(f"Path escape attempt: {full_path}")
                return "Invalid path", 403
        except Exception as e:
            logger.error(f"Error resolving path: {e}")
            return "Invalid path", 403
            
        # Serve the file if it exists
        if os.path.exists(full_path) and os.path.isfile(full_path):
            return send_from_directory(static_folder_path, safe_path)
    
    # For SPA routing, always serve index.html for non-API routes
    index_path = os.path.join(static_folder_path, 'index.html')
    if os.path.exists(index_path):
        return send_from_directory(static_folder_path, 'index.html')
    else:
        logger.error("index.html not found")
        return "Application not properly deployed", 500

# Health check endpoint
@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint for monitoring"""
    return jsonify({
        'success': True,
        'status': 'healthy',
        'timestamp': datetime.now().isoformat()
    }), 200

if __name__ == '__main__':
    # Configuration from environment variables
    port = int(os.environ.get('PORT', 5000))
    debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    
    # Don't use debug mode in production
    if os.environ.get('FLASK_ENV') == 'production':
        debug_mode = False
    
    logger.info(f"Starting application on port {port} (debug={debug_mode})")
    
    # Run the application
    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug_mode,
        use_reloader=debug_mode
    )