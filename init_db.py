#!/usr/bin/env python3
"""Initialize database tables for IOAgent application."""

import os
import sys
from app import app, db
from src.models.user import User, Project, Evidence, TimelineEntry, CausalFactor, AnalysisSection

def init_database():
    """Initialize database tables."""
    with app.app_context():
        try:
            # Create all tables
            db.create_all()
            print("✅ Database tables created successfully!")
            
            # Check if tables exist
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            
            print("\n📊 Tables created:")
            for table in tables:
                print(f"  - {table}")
            
            # Check for existing users
            user_count = User.query.count()
            print(f"\n👥 Existing users: {user_count}")
            
            if user_count == 0:
                print("\n💡 No users found. You can now register through the web interface.")
            
            return True
            
        except Exception as e:
            print(f"\n❌ Error initializing database: {str(e)}")
            return False

if __name__ == "__main__":
    print("🚀 IOAgent Database Initialization")
    print("=" * 40)
    
    # Check for DATABASE_URL
    if os.environ.get('DATABASE_URL'):
        print(f"📍 Using PostgreSQL database")
    else:
        print(f"📍 Using SQLite database (development mode)")
    
    print("\nInitializing database tables...")
    
    if init_database():
        print("\n✨ Database initialization complete!")
        print("\nYou can now:")
        print("1. Register users through the web interface")
        print("2. Start creating projects and investigations")
    else:
        print("\n⚠️  Database initialization failed.")
        print("Please check your database configuration and try again.")
        sys.exit(1)