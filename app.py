import os
import sys
import secrets
import logging
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
from werkzeug.exceptions import RequestEntityTooLarge

# Load environment variables FIRST, before any other imports
from dotenv import load_dotenv
# Use absolute path to ensure .env file is found regardless of working directory
env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
load_dotenv(dotenv_path=env_path)
print(f"DEBUG: Loading .env from: {env_path}")
print(f"DEBUG: ANTHROPIC_API_KEY found: {'ANTHROPIC_API_KEY' in os.environ}")

# Add the current directory to Python path to import from src
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, send_from_directory, jsonify, request
from flask_cors import CORS
from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity
from flask_migrate import Migrate
from src.models.user import db, User, Project, Evidence, TimelineEntry, CausalFactor
from src.routes.user import user_bp
from src.routes.api import api_bp
from src.routes.auth import auth_bp

# Initialize Flask app
# Set static folder to src/static directory
static_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src', 'static')
app = Flask(__name__, static_folder=static_path)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Debug logging for static path
logger.info(f"Current working directory: {os.getcwd()}")
logger.info(f"App file location: {os.path.abspath(__file__)}")
logger.info(f"Static folder path: {static_path}")
logger.info(f"Static folder exists: {os.path.exists(static_path)}")
if os.path.exists(static_path):
    logger.info(f"Static folder contents: {os.listdir(static_path)}")
index_path = os.path.join(static_path, 'index.html')
logger.info(f"Index.html path: {index_path}")
logger.info(f"Index.html exists: {os.path.exists(index_path)}")

# Security configuration
if os.environ.get('FLASK_ENV') == 'production':
    if not os.environ.get('SECRET_KEY'):
        raise ValueError("SECRET_KEY must be set in production")
    if not os.environ.get('JWT_SECRET_KEY'):
        raise ValueError("JWT_SECRET_KEY must be set in production")

app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-only')
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'dev-jwt-key-only')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)
app.config['JWT_ALGORITHM'] = 'HS256'
app.config['JWT_TOKEN_LOCATION'] = ['headers']
app.config['JWT_HEADER_NAME'] = 'Authorization'
app.config['JWT_HEADER_TYPE'] = 'Bearer'
app.config['JWT_CSRF_IN_COOKIES'] = False
app.config['JWT_CSRF_CHECK_FORM'] = False
app.config['JWT_ACCESS_CSRF_HEADER_NAME'] = None
app.config['JWT_REFRESH_CSRF_HEADER_NAME'] = None
app.config['JWT_CSRF_METHODS'] = []
app.config['SESSION_COOKIE_SECURE'] = os.environ.get('FLASK_ENV') == 'production'
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# File upload configuration
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
ALLOWED_EXTENSIONS = {
    'pdf': 'application/pdf',
    'doc': 'application/msword',
    'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'txt': 'text/plain',
    'csv': 'text/csv',
    'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Create upload directory if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
logger.info(f"Upload folder created/verified at: {UPLOAD_FOLDER}")

# Configure CORS securely
def get_cors_origins():
    """Get CORS origins based on environment"""
    if os.environ.get('FLASK_ENV') == 'production':
        # Production: Allow the actual production domain and common variations
        return [
            'https://ioagent.onrender.com',
            'https://ioagent-*.onrender.com',  # For preview deployments
            '*'  # Allow all for now to debug issues
        ]
    else:
        # Development: Allow localhost and specified domains
        return [
            'http://localhost:3000',
            'http://127.0.0.1:5000',
            'http://localhost:5000',
            'http://localhost:5001'
        ]

cors_origins = get_cors_origins()
logger.info(f"CORS origins configured: {cors_origins}")
CORS(app, origins=cors_origins, supports_credentials=True)

# Database configuration
# TEMPORARY: Use SQLite for production until PostgreSQL driver issues are resolved
# Store db_path globally so it can be used later
db_path = None

def configure_database():
    """Configure database with proper error handling"""
    global db_path
    
    # Create database directory
    db_dir = os.path.join(os.path.dirname(__file__), 'src', 'database')
    os.makedirs(db_dir, exist_ok=True)
    
    # Use SQLite for all environments temporarily
    db_path = os.path.join(db_dir, 'app.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{db_path}"
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
    }
    
    logger.info(f"Using SQLite database: {db_path}")
    logger.warning("PostgreSQL temporarily disabled - using SQLite for all environments")
    
    return True

# Configure database
configure_database()

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database and JWT
db.init_app(app)
jwt = JWTManager(app)
migrate = Migrate(app, db)

# Helper functions
def allowed_file(filename):
    """Check if the file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def validate_file_content(file_path, expected_extension):
    """Validate file content matches the claimed extension using python-magic"""
    try:
        import magic
        
        # Get the MIME type of the actual file content
        mime_type = magic.from_file(file_path, mime=True)
        
        # Map of extensions to expected MIME types
        extension_mime_map = {
            'pdf': ['application/pdf'],
            'doc': ['application/msword'],
            'docx': ['application/vnd.openxmlformats-officedocument.wordprocessingml.document'],
            'png': ['image/png'],
            'jpg': ['image/jpeg'],
            'jpeg': ['image/jpeg'],
            'gif': ['image/gif'],
            'mp4': ['video/mp4'],
            'avi': ['video/x-msvideo'],
            'mp3': ['audio/mpeg'],
            'wav': ['audio/wav', 'audio/x-wav'],
            'txt': ['text/plain']
        }
        
        expected_mimes = extension_mime_map.get(expected_extension.lower(), [])
        return mime_type in expected_mimes
        
    except ImportError:
        # If python-magic is not available, fall back to extension checking
        logger.warning("python-magic not available, using extension-only validation")
        return True
    except Exception as e:
        logger.error(f"Error validating file content: {e}")
        return False

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

def validate_project_id(project_id):
    """Validate project ID to prevent path traversal attacks"""
    import re
    # Allow only alphanumeric characters, hyphens, and underscores
    # Typical UUID format or similar safe identifiers
    if not project_id or not isinstance(project_id, str):
        return False
    if len(project_id) > 100:  # Reasonable length limit
        return False
    # Only allow safe characters
    if not re.match(r'^[a-zA-Z0-9_-]+$', project_id):
        return False
    # Prevent obvious path traversal attempts
    if '..' in project_id or '/' in project_id or '\\' in project_id:
        return False
    return True

def validate_filename_for_download(filename):
    """Validate filename for download to prevent path traversal"""
    if not filename or not isinstance(filename, str):
        return False
    # Use secure_filename and additional checks
    safe_name = secure_filename(filename)
    if safe_name != filename:
        return False
    if '..' in filename or '/' in filename or '\\' in filename:
        return False
    return True

def sanitize_error_message(error_msg, expose_details=False):
    """Sanitize error messages to prevent information disclosure"""
    if not expose_details:
        # In production, return generic messages
        if 'not found' in error_msg.lower() or '404' in error_msg:
            return 'Resource not found'
        elif 'permission' in error_msg.lower() or 'forbidden' in error_msg.lower():
            return 'Access denied'
        elif 'invalid' in error_msg.lower() or 'bad request' in error_msg.lower():
            return 'Invalid request'
        else:
            return 'An error occurred while processing your request'
    return error_msg

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

# JWT error handlers
@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    return jsonify({'success': False, 'error': 'Token has expired'}), 401

@jwt.invalid_token_loader
def invalid_token_callback(error):
    return jsonify({'success': False, 'error': 'Invalid token'}), 401

@jwt.unauthorized_loader
def missing_token_callback(error):
    return jsonify({'success': False, 'error': 'Authorization token is required'}), 401

# Helper function to get current user
def get_current_user():
    """Get current authenticated user"""
    user_id = get_jwt_identity()
    if user_id:
        return User.query.get(user_id)
    return None

# Register API blueprints
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(api_bp, url_prefix='/api')
app.register_blueprint(user_bp, url_prefix='/api')

# Note: File upload endpoint is handled by api_bp blueprint in src/routes/api.py

# File download endpoint
@app.route('/api/projects/<project_id>/download/<filename>', methods=['GET'])
@jwt_required()
def download_file(project_id, filename):
    """Handle file downloads with security validation"""
    try:
        # Validate project ID to prevent path traversal
        if not validate_project_id(project_id):
            logger.warning(f"Invalid project ID attempted: {project_id}")
            return jsonify({'success': False, 'error': 'Invalid project identifier'}), 400
        
        # Validate filename to prevent directory traversal
        if not validate_filename_for_download(filename):
            logger.warning(f"Invalid filename attempted: {filename}")
            return jsonify({'success': False, 'error': 'Invalid filename'}), 400
        
        # Use validated inputs
        safe_filename = secure_filename(filename)
        project_folder = os.path.join(app.config['UPLOAD_FOLDER'], f'project_{project_id}')
        
        # Ensure project folder exists and is within upload directory
        upload_folder_real = os.path.realpath(app.config['UPLOAD_FOLDER'])
        project_folder_real = os.path.realpath(project_folder)
        if not project_folder_real.startswith(upload_folder_real):
            logger.error(f"Path traversal attempt blocked: {project_folder}")
            return jsonify({'success': False, 'error': 'Invalid path'}), 403
        
        # Check if file exists
        filepath = os.path.join(project_folder, safe_filename)
        filepath_real = os.path.realpath(filepath)
        
        # Ensure file is within the project folder
        if not filepath_real.startswith(project_folder_real):
            logger.error(f"File access outside project folder blocked: {filepath}")
            return jsonify({'success': False, 'error': 'Access denied'}), 403
        
        if not os.path.exists(filepath):
            return jsonify({'success': False, 'error': 'File not found'}), 404
        
        # Send file
        return send_from_directory(project_folder, safe_filename, as_attachment=True)
        
    except Exception as e:
        logger.error(f"Error downloading file: {str(e)}")
        is_debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
        error_msg = sanitize_error_message(str(e), expose_details=is_debug)
        return jsonify({
            'success': False,
            'error': error_msg
        }), 500

# Delete file endpoint
@app.route('/api/projects/<project_id>/evidence/<evidence_id>', methods=['DELETE'])
@jwt_required()
def delete_evidence(project_id, evidence_id):
    """Delete evidence file"""
    try:
        # Validate project ID
        if not validate_project_id(project_id):
            logger.warning(f"Invalid project ID attempted: {project_id}")
            return jsonify({'success': False, 'error': 'Invalid project identifier'}), 400
        
        # Validate evidence ID
        if not validate_project_id(evidence_id):  # Same validation logic applies
            logger.warning(f"Invalid evidence ID attempted: {evidence_id}")
            return jsonify({'success': False, 'error': 'Invalid evidence identifier'}), 400
        
        # Check if evidence exists in database
        evidence = Evidence.query.filter_by(id=evidence_id, project_id=project_id).first()
        if not evidence:
            return jsonify({'success': False, 'error': 'Evidence not found'}), 404
        
        # Delete the physical file
        if evidence.file_path:
            full_file_path = os.path.join(app.config['UPLOAD_FOLDER'], evidence.file_path)
            if os.path.exists(full_file_path):
                try:
                    os.remove(full_file_path)
                    logger.info(f"Deleted file: {full_file_path}")
                except OSError as e:
                    logger.error(f"Error deleting file {full_file_path}: {e}")
                    # Continue with database deletion even if file deletion fails
        
        # Remove the database record
        db.session.delete(evidence)
        db.session.commit()
        
        logger.info(f"Evidence {evidence_id} deleted from project {project_id}")
        return jsonify({
            'success': True,
            'message': 'Evidence deleted successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting evidence: {str(e)}")
        is_debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
        error_msg = sanitize_error_message(str(e), expose_details=is_debug)
        return jsonify({
            'success': False,
            'error': error_msg
        }), 500

# Timeline endpoints
@app.route('/api/projects/<project_id>/timeline', methods=['POST'])
@jwt_required()
def add_timeline_entry(project_id):
    """Add a new timeline entry to a project"""
    try:
        # Validate project ID to prevent path traversal
        if not validate_project_id(project_id):
            logger.warning(f"Invalid project ID attempted: {project_id}")
            return jsonify({'success': False, 'error': 'Invalid project identifier'}), 400
        
        # Get JSON data from request
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        # Validate required fields
        required_fields = ['timestamp', 'type', 'description']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    'success': False, 
                    'error': f'Missing required field: {field}'
                }), 400
        
        # Validate timestamp format
        try:
            from datetime import datetime
            datetime.fromisoformat(data['timestamp'])
        except (ValueError, TypeError):
            return jsonify({
                'success': False, 
                'error': 'Invalid timestamp format. Use ISO format (YYYY-MM-DDTHH:MM:SS)'
            }), 400
        
        # Create timeline entry in database
        entry = TimelineEntry(
            id=secrets.token_urlsafe(16),
            timestamp=datetime.fromisoformat(data['timestamp']),
            entry_type=str(data['type'])[:50],
            description=str(data['description'])[:1000],
            confidence_level=data.get('confidence_level', 'medium'),
            is_initiating_event=data.get('is_initiating_event', False),
            project_id=project_id
        )
        
        # Set assumptions if provided
        if data.get('assumptions'):
            entry.assumptions_list = data['assumptions']
        
        # Set personnel if provided  
        if data.get('personnel_involved'):
            entry.personnel_involved_list = data['personnel_involved']
        
        db.session.add(entry)
        db.session.commit()
        
        logger.info(f"Timeline entry created for project {project_id}: {entry.entry_type}")
        
        return jsonify({
            'success': True,
            'entry': entry.to_dict(),
            'message': 'Timeline entry added successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error adding timeline entry: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Error adding timeline entry: {str(e)}'
        }), 500

# Update timeline entry endpoint
@app.route('/api/projects/<project_id>/timeline/<entry_id>', methods=['PUT'])
@jwt_required()
def update_timeline_entry(project_id, entry_id):
    """Update an existing timeline entry"""
    try:
        # Validate project ID to prevent path traversal
        if not validate_project_id(project_id):
            logger.warning(f"Invalid project ID attempted: {project_id}")
            return jsonify({'success': False, 'error': 'Invalid project identifier'}), 400
        
        # Validate entry ID
        if not validate_project_id(entry_id):  # Same validation logic applies
            logger.warning(f"Invalid entry ID attempted: {entry_id}")
            return jsonify({'success': False, 'error': 'Invalid entry identifier'}), 400
        # Get JSON data from request
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        # Validate timestamp format if provided
        if 'timestamp' in data:
            try:
                from datetime import datetime
                datetime.fromisoformat(data['timestamp'])
            except (ValueError, TypeError):
                return jsonify({
                    'success': False, 
                    'error': 'Invalid timestamp format. Use ISO format (YYYY-MM-DDTHH:MM:SS)'
                }), 400
        
        # Check if the timeline entry exists in the database
        entry = TimelineEntry.query.filter_by(id=entry_id, project_id=project_id).first()
        if not entry:
            return jsonify({'success': False, 'error': 'Timeline entry not found'}), 404
        
        # Update the entry with the new data
        if 'timestamp' in data:
            entry.timestamp = datetime.fromisoformat(data['timestamp'])
        if 'type' in data:
            entry.entry_type = str(data['type'])[:50]
        if 'description' in data:
            entry.description = str(data['description'])[:1000]
        if 'confidence_level' in data:
            entry.confidence_level = data['confidence_level']
        if 'is_initiating_event' in data:
            entry.is_initiating_event = data['is_initiating_event']
        if 'assumptions' in data:
            entry.assumptions_list = data['assumptions']
        if 'personnel_involved' in data:
            entry.personnel_involved_list = data['personnel_involved']
        
        entry.updated_at = datetime.now()
        
        # Save to database
        db.session.commit()
        
        logger.info(f"Timeline entry updated for project {project_id}: {entry_id}")
        
        return jsonify({
            'success': True,
            'entry': entry.to_dict(),
            'message': 'Timeline entry updated successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating timeline entry: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Error updating timeline entry: {str(e)}'
        }), 500

# Delete timeline entry endpoint
@app.route('/api/projects/<project_id>/timeline/<entry_id>', methods=['DELETE'])
@jwt_required()
def delete_timeline_entry(project_id, entry_id):
    """Delete timeline entry"""
    try:
        # Validate project ID to prevent path traversal
        if not validate_project_id(project_id):
            logger.warning(f"Invalid project ID attempted: {project_id}")
            return jsonify({'success': False, 'error': 'Invalid project identifier'}), 400
        
        # Validate entry ID
        if not validate_project_id(entry_id):  # Same validation logic applies
            logger.warning(f"Invalid entry ID attempted: {entry_id}")
            return jsonify({'success': False, 'error': 'Invalid entry identifier'}), 400
        # Check if the timeline entry exists
        entry = TimelineEntry.query.filter_by(id=entry_id, project_id=project_id).first()
        if not entry:
            return jsonify({'success': False, 'error': 'Timeline entry not found'}), 404
        
        # Remove it from the database
        db.session.delete(entry)
        db.session.commit()
        
        logger.info(f"Timeline entry {entry_id} deleted from project {project_id}")
        return jsonify({
            'success': True,
            'message': 'Timeline entry deleted successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
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
    
    # Apply CSP for all environments to allow required resources
    response.headers['Content-Security-Policy'] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; "
        "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com https://fonts.googleapis.com; "
        "font-src 'self' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com https://fonts.gstatic.com; "
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
    if db_path:
        db_dir = os.path.dirname(db_path)
        os.makedirs(db_dir, exist_ok=True)
    else:
        logger.warning("db_path not set, skipping directory creation")
    
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
    print("🚀 IOAgent starting up...")
    logger.info("IOAgent application starting")
    
    # Configuration from environment variables
    # Render provides PORT environment variable - no default needed
    port = int(os.environ.get('PORT', 10000))
    logger.info(f"Environment PORT={os.environ.get('PORT', 'NOT_SET')}, using port={port}")
    debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    
    # Don't use debug mode in production
    if os.environ.get('FLASK_ENV') == 'production':
        debug_mode = False
    
    logger.info(f"Starting application on host=0.0.0.0 port={port} (debug={debug_mode})")
    
    try:
        # Run the application
        app.run(
            host='0.0.0.0',
            port=port,
            debug=debug_mode,
            use_reloader=debug_mode
        )
    except Exception as e:
        logger.error(f"Failed to start Flask application: {e}")
        import traceback
        traceback.print_exc()
        raise