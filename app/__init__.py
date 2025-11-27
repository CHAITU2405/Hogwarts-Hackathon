from flask import Flask, send_from_directory, send_file
from app.config import Config
from app.models import db
from app.routes import register_blueprints
from pathlib import Path
import os

def create_app():
    # Get project root directory
    BASE_DIR = Path(__file__).parent.parent
    
    # Don't use static_folder for root - we'll serve files manually
    # This prevents static file serving from intercepting API routes
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Initialize database
    db.init_app(app)
    
    # Create tables
    with app.app_context():
        db.create_all()
    
    # Serve HTML files - register these BEFORE the catch-all route
    @app.route('/')
    def index():
        main_path = BASE_DIR / 'main.html'
        if main_path.exists():
            return send_file(str(main_path))
        return {'error': 'main.html not found'}, 404
    
    # Admin login URL
    @app.route('/admin-login')
    def admin_login():
        login_path = BASE_DIR / 'login.html'
        if login_path.exists():
            return send_file(str(login_path))
        return {'error': 'login.html not found'}, 404
    
    # Register blueprints AFTER specific routes but BEFORE catch-all
    # This ensures API routes are matched before the catch-all route
    register_blueprints(app)
    
    @app.route('/<path:filename>')
    def serve_file(filename):
        # Don't serve API routes - let the blueprint handle them
        if filename.startswith('api/'):
            return {'error': 'API route not found'}, 404
        
        file_path = BASE_DIR / filename
        # Serve files if they exist
        if file_path.exists() and file_path.is_file():
            return send_file(str(file_path))
        return {'error': 'File not found'}, 404
    
    return app

