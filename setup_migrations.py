#!/usr/bin/env python3
"""
Setup script for Flask-Migrate in IOAgent
Run this after installing dependencies to initialize database migrations
"""

import os
import sys

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def setup_migrations():
    """Initialize Flask-Migrate for the application"""
    
    print("Setting up Flask-Migrate for IOAgent...")
    print("Please ensure you have installed all dependencies first:")
    print("  pip install -r IOAgent-backend/requirements.txt")
    print()
    
    commands = [
        "export FLASK_APP=IOAgent-backend.app",
        "flask db init",
        "flask db migrate -m 'Initial migration with authentication'",
        "flask db upgrade"
    ]
    
    print("Run these commands in order from the project root:")
    for i, cmd in enumerate(commands, 1):
        print(f"{i}. {cmd}")
    
    print("\nNote: You may need to activate a virtual environment first:")
    print("  python3 -m venv venv")
    print("  source venv/bin/activate")
    print("  pip install -r IOAgent-backend/requirements.txt")

if __name__ == "__main__":
    setup_migrations()