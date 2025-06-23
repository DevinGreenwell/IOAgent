#!/usr/bin/env python3
"""
Database initialization script for production PostgreSQL on Render
Run this once after deployment to create tables and admin user
"""
import os
import sys

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'IOAgent-backend'))

from flask import Flask
from src.models.user import db, User, Project, Evidence, TimelineEntry, CausalFactor

def init_database():
    # Create Flask app
    app = Flask(__name__)
    
    # Use environment variable or internal Render URL
    database_url = os.environ.get('DATABASE_URL', 
        'postgresql://ioagent_user:uOXBZaleReg83smdsLXM371fT6vpVF4C@dpg-d1cbuv6uk2gs73aii0d0-a/ioagent')
    
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
        'pool_size': 5,
        'max_overflow': 10
    }
    
    # Initialize database
    db.init_app(app)
    
    with app.app_context():
        try:
            print("🔄 Creating database tables...")
            db.create_all()
            print("✅ Database tables created successfully")
            
            # Create admin user if doesn't exist
            admin = User.query.filter_by(username='admin').first()
            if not admin:
                print("🔄 Creating admin user...")
                admin = User(
                    username='admin', 
                    email='admin@ioagent.com', 
                    role='admin',
                    is_active=True
                )
                admin.set_password('AdminPass123!')
                db.session.add(admin)
                db.session.commit()
                print("✅ Admin user created successfully")
                print("📋 Admin credentials:")
                print("   Username: admin")
                print("   Password: AdminPass123!")
            else:
                print("ℹ️  Admin user already exists")
                
            # Test database connection
            user_count = User.query.count()
            print(f"📊 Total users in database: {user_count}")
            
            print("🎉 Database initialization completed successfully!")
            return True
            
        except Exception as e:
            print(f"❌ Database initialization failed: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    print("🚀 Initializing PostgreSQL database for IOAgent...")
    success = init_database()
    sys.exit(0 if success else 1)