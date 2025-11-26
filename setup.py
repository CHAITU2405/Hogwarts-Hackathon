#!/usr/bin/env python3
"""
Setup script for Hogwarts Hackathon backend
Creates necessary directories and initializes the database
"""

import os
from pathlib import Path

def setup_directories():
    """Create necessary directories if they don't exist"""
    directories = ['instance', 'uploads']
    
    for directory in directories:
        dir_path = Path(directory)
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {directory}/")
        else:
            print(f"Directory already exists: {directory}/")

def setup_database():
    """Initialize the database"""
    try:
        from app import create_app
        from app.models import db
        
        app = create_app()
        with app.app_context():
            db.create_all()
            print("Database initialized successfully!")
    except Exception as e:
        print(f"Error initializing database: {e}")

if __name__ == '__main__':
    print("Setting up Hogwarts Hackathon backend...")
    setup_directories()
    setup_database()
    print("\nSetup complete! You can now run: python app.py")

