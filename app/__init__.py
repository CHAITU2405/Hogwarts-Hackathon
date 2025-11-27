from flask import Flask, send_from_directory, send_file, render_template
from app.config import Config
from app.models import db, Sponsor
from app.routes import register_blueprints
from pathlib import Path
import os

def create_app():
    # Get project root directory
    BASE_DIR = Path(__file__).parent.parent
    
    # Don't use static_folder for root - we'll serve files manually
    # This prevents static file serving from intercepting API routes
    app = Flask(__name__, template_folder=str(BASE_DIR))
    app.config.from_object(Config)
    
    # Initialize database
    db.init_app(app)
    
    # Create tables
    with app.app_context():
        db.create_all()
    
    # Serve HTML files - register these BEFORE the catch-all route
    @app.route('/')
    @app.route('/main.html')  # Also handle direct access to main.html
    def index():
        # Get sponsors from database
        try:
            sponsors = Sponsor.query.order_by(Sponsor.display_order, Sponsor.created_at).all()
            sponsors_data = [sponsor.to_dict() for sponsor in sponsors]
            print(f"[INDEX ROUTE] Found {len(sponsors_data)} sponsors to display")  # Debug log
            for s in sponsors_data:
                print(f"  - {s.get('name')}: {s.get('logo_path')}")
        except Exception as e:
            import traceback
            print(f"[INDEX ROUTE] Error fetching sponsors: {e}")
            print(traceback.format_exc())
            sponsors_data = []
        
        # Render main.html as template with sponsors data
        try:
            print(f"[INDEX ROUTE] Rendering template with {len(sponsors_data)} sponsors")
            rendered = render_template('main.html', sponsors=sponsors_data)
            print(f"[INDEX ROUTE] Template rendered successfully, length: {len(rendered)}")
            return rendered
        except Exception as e:
            import traceback
            print(f"[INDEX ROUTE] Error rendering template: {e}")
            print(traceback.format_exc())
            # Fallback: try to serve the file directly if template rendering fails
            main_path = BASE_DIR / 'main.html'
            if main_path.exists():
                print("[INDEX ROUTE] Falling back to send_file")
                return send_file(str(main_path))
            return {'error': 'Template rendering failed'}, 500
    
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
        
        # Don't serve main.html as static file - it should be rendered as template
        if filename == 'main.html':
            # Re-route to index to render as template
            return index()
        
        file_path = BASE_DIR / filename
        # Serve files if they exist
        if file_path.exists() and file_path.is_file():
            return send_file(str(file_path))
        return {'error': 'File not found'}, 404
    
    return app

# Expose app instance for gunicorn compatibility
# This allows 'gunicorn app:app' to work
app = create_app()

