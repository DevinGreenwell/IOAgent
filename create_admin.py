#!/usr/bin/env python3
"""
Create admin user for IOAgent production deployment
Run this script once after first deployment to create an admin account
"""

import os
import sys

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from IOAgent_backend.app import app
from src.models.user import db, User

def create_admin():
    """Create admin user for production"""
    with app.app_context():
        # Check if admin already exists
        existing_admin = User.query.filter_by(username='admin').first()
        if existing_admin:
            print("❌ Admin user already exists!")
            print(f"   Username: {existing_admin.username}")
            print(f"   Email: {existing_admin.email}")
            print(f"   Created: {existing_admin.created_at}")
            return False
        
        # Create admin user
        admin = User(
            username='admin',
            email='admin@ioagent.onrender.com',
            role='admin'
        )
        admin.set_password('AdminPass123!')  # This should be changed immediately!
        
        try:
            db.session.add(admin)
            db.session.commit()
            
            print("✅ Admin user created successfully!")
            print("   Username: admin")
            print("   Email: admin@ioagent.onrender.com")
            print("   Password: AdminPass123!")
            print()
            print("⚠️  IMPORTANT: Change the password immediately after login!")
            print("   Use: POST /api/auth/change-password")
            print()
            print("🔗 Login at: https://ioagent.onrender.com/api/auth/login")
            
            return True
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error creating admin user: {str(e)}")
            return False

def create_test_user():
    """Create a test user for demonstration"""
    with app.app_context():
        # Check if test user already exists
        existing_user = User.query.filter_by(username='testuser').first()
        if existing_user:
            print("ℹ️  Test user already exists")
            return False
        
        # Create test user
        user = User(
            username='testuser',
            email='test@ioagent.onrender.com',
            role='user'
        )
        user.set_password('TestPass123!')
        
        try:
            db.session.add(user)
            db.session.commit()
            
            print("✅ Test user created successfully!")
            print("   Username: testuser")
            print("   Email: test@ioagent.onrender.com")
            print("   Password: TestPass123!")
            
            return True
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error creating test user: {str(e)}")
            return False

def list_users():
    """List all existing users"""
    with app.app_context():
        users = User.query.all()
        if not users:
            print("📝 No users found in database")
            return
        
        print(f"📝 Found {len(users)} user(s):")
        for user in users:
            print(f"   - {user.username} ({user.email}) - {user.role} - Created: {user.created_at}")

if __name__ == "__main__":
    print("🚀 IOAgent Admin User Setup")
    print("=" * 40)
    
    # Check if we're in the right environment
    flask_env = os.environ.get('FLASK_ENV', 'development')
    print(f"Environment: {flask_env}")
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == 'list':
            list_users()
        elif command == 'test':
            create_test_user()
        elif command == 'admin':
            create_admin()
        else:
            print("Usage: python create_admin.py [admin|test|list]")
            print("  admin - Create admin user")
            print("  test  - Create test user") 
            print("  list  - List all users")
    else:
        # Default: create admin user
        print()
        list_users()
        print()
        create_admin()
        print()
        
        # Optionally create test user
        response = input("Create test user as well? (y/N): ").lower()
        if response in ['y', 'yes']:
            create_test_user()
        
        print()
        print("🎉 Setup complete! Your IOAgent instance is ready for production use.")