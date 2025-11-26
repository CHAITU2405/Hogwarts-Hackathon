from flask import Flask, send_from_directory, send_file
from app.config import Config
from app.models import db, Admin
from app.routes import register_blueprints
from pathlib import Path
from werkzeug.security import generate_password_hash
import os

def create_app():
    # Get project root directory
    BASE_DIR = Path(__file__).parent.parent
    
    app = Flask(__name__, 
                static_folder=str(BASE_DIR), 
                static_url_path='')
    app.config.from_object(Config)
    
    # Initialize database
    db.init_app(app)
    
    # Register blueprints
    register_blueprints(app)
    
    # Create tables and initialize default admin
    with app.app_context():
        db.create_all()
        
        # Create default admin if it doesn't exist
        default_admin_username = 'harry potter'
        default_admin = Admin.query.filter_by(username=default_admin_username).first()
        if not default_admin:
            default_admin = Admin(
                username=default_admin_username,
                password_hash=generate_password_hash('hogwarts house cup')
            )
            db.session.add(default_admin)
            db.session.commit()
            print(f"Default admin '{default_admin_username}' created successfully")
    
    # Serve HTML files
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
    
    @app.route('/<path:filename>')
    def serve_file(filename):
        file_path = BASE_DIR / filename
        # Serve files if they exist
        if file_path.exists() and file_path.is_file():
            return send_file(str(file_path))
        return {'error': 'File not found'}, 404
    
    return app


# Expose a top-level WSGI application callable so servers can import
# the package `app` and find `app` (e.g. `gunicorn app:app`).
# This will initialize the app at import-time which is suitable for
# typical deployment environments like Render.
app = create_app()

