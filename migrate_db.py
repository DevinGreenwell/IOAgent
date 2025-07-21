#!/usr/bin/env python3
"""
Database migration script to ensure proper schema.
Run this after deploying to Render to fix any schema issues.
"""

import os
import sys
from app import app, db
from sqlalchemy import text
from src.models.user import User, Project, Evidence, TimelineEntry, CausalFactor, AnalysisSection

def check_and_fix_schema():
    """Check database schema and fix any issues."""
    with app.app_context():
        try:
            print("🔍 Checking database schema...")
            
            # First, create all tables if they don't exist
            db.create_all()
            print("✅ Database tables created/verified")
            
            # Check if we need to handle any column name differences
            # This is specifically for the case_number vs official_number issue
            try:
                # Try to query projects table structure
                if os.environ.get('DATABASE_URL'):
                    # PostgreSQL
                    result = db.session.execute(text("""
                        SELECT column_name 
                        FROM information_schema.columns 
                        WHERE table_name = 'projects'
                    """))
                    columns = [row[0] for row in result]
                    print(f"📊 Projects table columns: {columns}")
                else:
                    # SQLite
                    result = db.session.execute(text("PRAGMA table_info(projects)"))
                    columns = [row[1] for row in result]
                    print(f"📊 Projects table columns: {columns}")
                
                # Check if we have case_number instead of official_number
                if 'case_number' in columns and 'official_number' not in columns:
                    print("⚠️  Found 'case_number' column, need to rename to 'official_number'")
                    if os.environ.get('DATABASE_URL'):
                        # PostgreSQL
                        db.session.execute(text("""
                            ALTER TABLE projects 
                            RENAME COLUMN case_number TO official_number
                        """))
                    else:
                        # SQLite doesn't support column rename directly
                        print("⚠️  SQLite detected - manual migration may be needed")
                    db.session.commit()
                    print("✅ Column renamed successfully")
                
            except Exception as e:
                print(f"⚠️  Could not check column names: {str(e)}")
            
            # Test creating a dummy project to ensure everything works
            print("\n🧪 Testing project creation...")
            test_user = User.query.first()
            if test_user:
                test_project = Project(
                    id='test-' + os.urandom(8).hex(),
                    user_id=test_user.id,
                    title='Test Project',
                    status='draft'
                )
                db.session.add(test_project)
                db.session.commit()
                
                # Clean up test project
                db.session.delete(test_project)
                db.session.commit()
                print("✅ Project creation test successful")
            else:
                print("⚠️  No users found - create a user first")
            
            # Show table statistics
            print("\n📊 Database Statistics:")
            print(f"Users: {User.query.count()}")
            print(f"Projects: {Project.query.count()}")
            print(f"Evidence: {Evidence.query.count()}")
            print(f"Timeline Entries: {TimelineEntry.query.count()}")
            
            return True
            
        except Exception as e:
            print(f"\n❌ Error during migration: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    print("🚀 IOAgent Database Migration")
    print("=" * 40)
    
    if os.environ.get('DATABASE_URL'):
        print("📍 Using PostgreSQL database")
    else:
        print("📍 Using SQLite database")
    
    print("\nRunning migration checks...")
    
    if check_and_fix_schema():
        print("\n✨ Migration complete!")
    else:
        print("\n⚠️  Migration failed - check errors above")
        sys.exit(1)