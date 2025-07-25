# Authentication routes for IOAgent

from flask import Blueprint, request, jsonify, current_app, session
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, create_refresh_token
from datetime import timedelta
import re
import os
import secrets

from src.models.user import db, User
from src.utils.security import validate_password_strength, generate_csrf_token, validate_csrf_token
from src.utils.rate_limit import rate_limit, AUTH_RATE_LIMIT

# Create blueprint
auth_bp = Blueprint('auth', __name__)

def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password(password):
    """Validate password strength - wrapper for backward compatibility"""
    result = validate_password_strength(password)
    if result['valid']:
        return True, "Password is valid"
    else:
        return False, "; ".join(result['errors'])

@auth_bp.route('/register', methods=['POST'])
@rate_limit(*AUTH_RATE_LIMIT)
def register():
    """Register a new user"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        # Validate required fields
        required_fields = ['username', 'email', 'password']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'success': False, 'error': f'Missing required field: {field}'}), 400
        
        username = data['username'].strip()
        email = data['email'].strip().lower()
        password = data['password']
        
        # Validate username
        if len(username) < 3 or len(username) > 80:
            return jsonify({'success': False, 'error': 'Username must be between 3 and 80 characters'}), 400
        
        if not re.match(r'^[a-zA-Z0-9_-]+$', username):
            return jsonify({'success': False, 'error': 'Username can only contain letters, numbers, hyphens, and underscores'}), 400
        
        # Validate email
        if not validate_email(email):
            return jsonify({'success': False, 'error': 'Invalid email format'}), 400
        
        # Validate password
        is_valid, password_msg = validate_password(password)
        if not is_valid:
            return jsonify({'success': False, 'error': password_msg}), 400
        
        # Check if user already exists
        if User.query.filter_by(username=username).first():
            return jsonify({'success': False, 'error': 'Username already exists'}), 409
        
        if User.query.filter_by(email=email).first():
            return jsonify({'success': False, 'error': 'Email already registered'}), 409
        
        # Create new user
        user = User(username=username, email=email)
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        # Create access token with shorter expiry
        access_token = create_access_token(
            identity=str(user.id),
            expires_delta=timedelta(minutes=15)
        )
        
        # Create refresh token
        refresh_token = create_refresh_token(
            identity=str(user.id),
            expires_delta=timedelta(days=7)
        )
        
        return jsonify({
            'success': True,
            'message': 'User registered successfully',
            'access_token': access_token,
            'refresh_token': refresh_token,
            'user': user.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error registering user: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to register user'}), 500

@auth_bp.route('/login', methods=['POST'])
@rate_limit(*AUTH_RATE_LIMIT)
def login():
    """Authenticate user and return JWT token"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        # Get credentials
        username_or_email = data.get('username', '').strip()
        password = data.get('password', '')
        
        if not username_or_email or not password:
            return jsonify({'success': False, 'error': 'Username/email and password are required'}), 400
        
        # Find user by username or email
        user = None
        if '@' in username_or_email:
            user = User.query.filter_by(email=username_or_email.lower()).first()
        else:
            user = User.query.filter_by(username=username_or_email).first()
        
        # Verify user exists and password is correct
        if not user or not user.check_password(password):
            return jsonify({'success': False, 'error': 'Invalid credentials'}), 401
        
        # Check if user is active
        if not user.is_active:
            return jsonify({'success': False, 'error': 'Account is deactivated'}), 401
        
        # Create access token with shorter expiry
        access_token = create_access_token(
            identity=str(user.id),
            expires_delta=timedelta(minutes=15)
        )
        
        # Create refresh token
        refresh_token = create_refresh_token(
            identity=str(user.id),
            expires_delta=timedelta(days=7)
        )
        
        return jsonify({
            'success': True,
            'message': 'Login successful',
            'access_token': access_token,
            'refresh_token': refresh_token,
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error during login: {str(e)}")
        return jsonify({'success': False, 'error': 'Login failed'}), 500

@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """Get current user information"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(int(user_id))
        
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        if not user.is_active:
            return jsonify({'success': False, 'error': 'Account is deactivated'}), 401
        
        return jsonify({
            'success': True,
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error getting current user: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to get user information'}), 500

@auth_bp.route('/change-password', methods=['POST'])
@jwt_required()
def change_password():
    """Change user password"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(int(user_id))
        
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        current_password = data.get('current_password', '')
        new_password = data.get('new_password', '')
        
        if not current_password or not new_password:
            return jsonify({'success': False, 'error': 'Current and new passwords are required'}), 400
        
        # Verify current password
        if not user.check_password(current_password):
            return jsonify({'success': False, 'error': 'Current password is incorrect'}), 401
        
        # Validate new password
        is_valid, password_msg = validate_password(new_password)
        if not is_valid:
            return jsonify({'success': False, 'error': password_msg}), 400
        
        # Update password
        user.set_password(new_password)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Password changed successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error changing password: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to change password'}), 500

@auth_bp.route('/refresh', methods=['POST'])
@jwt_required()
def refresh_token():
    """Refresh JWT token"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(int(user_id))
        
        if not user or not user.is_active:
            return jsonify({'success': False, 'error': 'Invalid user'}), 401
        
        # Create new access token
        access_token = create_access_token(
            identity=str(user.id),
            expires_delta=timedelta(hours=24)
        )
        
        return jsonify({
            'success': True,
            'access_token': access_token
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error refreshing token: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to refresh token'}), 500

@auth_bp.route('/bootstrap', methods=['POST'])
@rate_limit(1, 3600)  # Only 1 attempt per hour
def bootstrap_admin():
    """Create admin user if no users exist"""
    try:
        # Check if any users exist
        user_count = User.query.count()
        if user_count > 0:
            return jsonify({'success': False, 'error': 'Users already exist'}), 409
        
        # Get admin credentials from environment or generate secure ones
        admin_username = os.environ.get('ADMIN_USERNAME', 'admin')
        admin_email = os.environ.get('ADMIN_EMAIL', 'admin@ioagent.local')
        admin_password = os.environ.get('ADMIN_PASSWORD')
        
        if not admin_password:
            # Generate a secure random password if not provided
            admin_password = secrets.token_urlsafe(16)
            current_app.logger.warning(f"Generated admin password: {admin_password}")
            current_app.logger.warning("Please save this password securely and set ADMIN_PASSWORD in your environment!")
        
        # Validate admin password strength
        password_validation = validate_password_strength(admin_password)
        if not password_validation['valid']:
            return jsonify({
                'success': False,
                'error': 'Admin password does not meet security requirements',
                'requirements': password_validation['errors']
            }), 400
        
        # Create admin user
        admin = User(
            username=admin_username,
            email=admin_email,
            role='admin'
        )
        admin.set_password(admin_password)
        
        db.session.add(admin)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Admin user created successfully',
            'username': 'admin'
        }), 201
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error creating admin user: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to create admin user'}), 500

@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """Refresh access token using refresh token"""
    try:
        user_id = get_jwt_identity()
        
        # Verify user still exists and is active
        user = User.query.get(int(user_id))
        if not user or not user.is_active:
            return jsonify({'success': False, 'error': 'Invalid user'}), 401
        
        # Create new access token
        access_token = create_access_token(
            identity=str(user.id),
            expires_delta=timedelta(minutes=15)
        )
        
        return jsonify({
            'success': True,
            'access_token': access_token
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error refreshing token: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to refresh token'}), 500