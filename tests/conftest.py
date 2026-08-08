"""
NidaanPath AI — tests/conftest.py
Shared test fixtures.
"""
import pytest
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import create_app
from app.extensions import db as _db


@pytest.fixture(scope='session')
def app():
    """Create application for testing."""
    os.environ['USE_MOCK_LLM'] = 'true'
    os.environ['FLASK_SECRET_KEY'] = 'test-secret'
    os.environ['DATABASE_URL'] = 'sqlite:///test_nidaanpath.db'

    app = create_app('development')
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    app.config['USE_MOCK_LLM'] = True

    with app.app_context():
        _db.create_all()
        yield app
        _db.drop_all()


@pytest.fixture(scope='function')
def client(app):
    """Test client."""
    return app.test_client()


@pytest.fixture(scope='function')
def db(app):
    """Database fixture."""
    with app.app_context():
        yield _db
        _db.session.rollback()


@pytest.fixture
def demo_extractions():
    """Standard 8-report extraction set (produces Possible Stagnation)."""
    from app.services.mock_ai_service import DEMO_EXTRACTIONS
    return [
        {**DEMO_EXTRACTIONS[i], 'document_id': f'report_{i:02d}.pdf'}
        for i in range(1, 9)
    ]


@pytest.fixture
def full_extractions():
    """All 10 report extractions."""
    from app.services.mock_ai_service import DEMO_EXTRACTIONS
    return [
        {**DEMO_EXTRACTIONS[i], 'document_id': f'report_{i:02d}.pdf'}
        for i in range(1, 11)
    ]
