"""
NidaanPath AI — app/__init__.py
Application factory with all blueprints and setup.
"""
import os
import zipfile

from flask import Flask
from .config import config_map
from .extensions import db


def create_app(config_name=None):
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')

    app = Flask(__name__, instance_relative_config=True)
    cfg = config_map.get(config_name, config_map['default'])
    app.config.from_object(cfg)

    # Ensure required directories exist
    for folder in [app.config['UPLOAD_FOLDER'],
                   app.config['DEMO_REPORTS_FOLDER'],
                   app.config['GENERATED_REPORTS_FOLDER'],
                   app.instance_path]:
        os.makedirs(folder, exist_ok=True)

    # Auto-extract demo dataset if ZIP is present
    _extract_demo_dataset(app)

    # Init extensions
    db.init_app(app)

    # Register blueprints
    from .routes.main import main_bp
    from .routes.intake import intake_bp
    from .routes.documents import documents_bp
    from .routes.journey import journey_bp
    from .routes.agent import agent_bp
    from .routes.reports import reports_bp
    from .routes.demo import demo_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(intake_bp, url_prefix='/intake')
    app.register_blueprint(documents_bp, url_prefix='/documents')
    app.register_blueprint(journey_bp, url_prefix='/journey')
    app.register_blueprint(agent_bp, url_prefix='/agent')
    app.register_blueprint(reports_bp, url_prefix='/reports')
    app.register_blueprint(demo_bp, url_prefix='/demo')

    # Create database tables
    with app.app_context():
        db.create_all()

    return app


def _extract_demo_dataset(app):
    """Detect and extract the synthetic medical reports ZIP."""
    root = os.path.dirname(os.path.dirname(__file__))
    zip_path = os.path.join(root, 'NidaanPath_10_Synthetic_Medical_Reports.zip')
    demo_dir = app.config['DEMO_REPORTS_FOLDER']

    if os.path.exists(zip_path):
        with zipfile.ZipFile(zip_path, 'r') as z:
            z.extractall(demo_dir)
