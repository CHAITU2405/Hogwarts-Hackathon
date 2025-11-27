import os
from pathlib import Path

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'hogwarts-hackathon-secret-key-2025'
    
    # Get base directory
    BASE_DIR = Path(__file__).parent.parent
    INSTANCE_DIR = BASE_DIR / 'instance'
    INSTANCE_DIR.mkdir(exist_ok=True)
    
    # Database URI with absolute path
    DATABASE_PATH = INSTANCE_DIR / 'hogwarts_hackathon.db'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or f'sqlite:///{DATABASE_PATH}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # File upload settings
    UPLOAD_FOLDER = BASE_DIR / 'uploads'
    UPLOAD_FOLDER.mkdir(exist_ok=True)
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf'}
    
    # Email configuration - use environment variables for security
    SENDER_EMAIL = os.environ.get('SENDER_EMAIL') or 'hogwartshackathon@gmail.com'
    SENDER_PASSWORD = os.environ.get('SENDER_PASSWORD') or ''
    SMTP_SERVER = os.environ.get('SMTP_SERVER') or 'smtp.gmail.com'
    SMTP_PORT = int(os.environ.get('SMTP_PORT') or '587')  # 587 for TLS, 465 for SSL
    
    # Ensure directories exist
    @staticmethod
    def init_app(app):
        # Directories are already created in class definition
        pass

