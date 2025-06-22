#!/usr/bin/env python3
"""
Database initialization script for IOAgent
Run this script to create the database tables and optionally add sample data.
"""

import os
import sys

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from IOAgent-backend.app import app
from src.models.user import db, User, Project, Evidence, TimelineEntry, CausalFactor

def init_database():
    """Initialize the database with tables"""
    with app.app_context():
        print("Creating database tables...")
        
        # Drop all tables (optional - comment out for production)
        # db.drop_all()
        
        # Create all tables
        db.create_all()
        
        print("Database tables created successfully!")
        
        # Check if we need to create sample data
        if Project.query.count() == 0:
            print("Creating sample project...")
            create_sample_data()
        else:
            print("Database already contains data.")

def create_sample_data():
    """Create sample data for testing"""
    try:
        # Create a sample project
        sample_project = Project(
            id="sample-project-001",
            title="Sample Investigation",
            investigating_officer="Officer Smith",
            status="draft",
            incident_location="Main Street Intersection",
            incident_type="Traffic Incident"
        )
        
        db.session.add(sample_project)
        db.session.commit()
        
        print(f"Sample project created with ID: {sample_project.id}")
        
    except Exception as e:
        db.session.rollback()
        print(f"Error creating sample data: {e}")

def reset_database():
    """Reset the database (drop all tables and recreate)"""
    with app.app_context():
        print("WARNING: This will delete all data!")
        response = input("Are you sure you want to reset the database? (yes/no): ")
        
        if response.lower() == 'yes':
            print("Dropping all tables...")
            db.drop_all()
            print("Creating new tables...")
            db.create_all()
            print("Database reset complete!")
        else:
            print("Database reset cancelled.")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "reset":
        reset_database()
    else:
        init_database()