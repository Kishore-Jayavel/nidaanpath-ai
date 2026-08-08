"""
NidaanPath AI — app/config.py
Configuration loaded from environment variables.
"""
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.environ.get('FLASK_SECRET_KEY', 'nidaanpath-fallback-key')

    # Use absolute path so DB is always in the project root, not instance folder
    _BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    _DEFAULT_DB = 'sqlite:///' + os.path.join(_BASE_DIR, 'nidaanpath.db')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', _DEFAULT_DB)
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')
    GEMINI_MODEL = os.environ.get('GEMINI_MODEL', 'gemini-1.5-flash')
    USE_MOCK_LLM = os.environ.get('USE_MOCK_LLM', 'true').lower() == 'true'

    MAX_UPLOAD_MB = int(os.environ.get('MAX_UPLOAD_MB', 10))
    MAX_CONTENT_LENGTH = MAX_UPLOAD_MB * 1024 * 1024

    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads')
    DEMO_REPORTS_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'demo_reports')
    GENERATED_REPORTS_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'generated_reports')

    ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}
    ALLOWED_MIMETYPES = {'application/pdf', 'image/png', 'image/jpeg'}


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False


config_map = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig,
}
