"""
WSGI entry point for Gunicorn
"""
from app import create_app

# Create the Flask application instance
application = create_app()

# Also expose as 'app' for compatibility
app = application

if __name__ == '__main__':
    application.run(debug=True, host='0.0.0.0', port=5000)

