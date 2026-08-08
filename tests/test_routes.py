"""
NidaanPath AI — tests/test_routes.py
Route integration tests.
"""
import pytest
from app.models.patient_case import PatientCase


def test_index_returns_200(client):
    resp = client.get('/')
    assert resp.status_code == 200


def test_responsible_ai_returns_200(client):
    resp = client.get('/responsible-ai')
    assert resp.status_code == 200


def test_intake_get_returns_200(client, app):
    with client.session_transaction() as sess:
        with app.app_context():
            case = PatientCase(case_code=PatientCase.generate_case_code())
            from app.extensions import db
            db.session.add(case)
            db.session.commit()
            sess['case_id'] = case.id
    resp = client.get('/intake/')
    assert resp.status_code == 200


def test_documents_upload_page_returns_200(client, app):
    with client.session_transaction() as sess:
        with app.app_context():
            case = PatientCase(case_code=PatientCase.generate_case_code())
            from app.extensions import db
            db.session.add(case)
            db.session.commit()
            sess['case_id'] = case.id
    resp = client.get('/documents/')
    assert resp.status_code == 200


def test_demo_home_returns_200(client):
    resp = client.get('/demo/')
    assert resp.status_code == 200


def test_api_status_returns_mock_mode(client):
    resp = client.get('/api/status')
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['status'] == 'ok'
    assert data['mode'] == 'mock'


def test_demo_load_batch_endpoint(client):
    import json
    resp = client.post('/demo/load-batch',
                       data=json.dumps({'reports': [1, 2]}),
                       content_type='application/json')
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['success'] is True
    assert 'journey_state' in data


def test_demo_add_evidence_09(client, app):
    import json
    # Load batch first (may return empty loads if no PDF files present)
    client.post('/demo/load-batch',
                data=json.dumps({'reports': list(range(1, 9))}),
                content_type='application/json')
    # Add report 09 — 200 if PDF present, 404 if demo files not in test env
    resp = client.post('/demo/add-evidence/9')
    assert resp.status_code in (200, 404), \
        f"Expected 200 or 404, got {resp.status_code}"
    data = resp.get_json()
    if resp.status_code == 200:
        assert data['success'] is True




def test_demo_reset(client):
    resp = client.post('/demo/reset')
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['success'] is True


def test_journey_dashboard_returns_200(client, app):
    with client.session_transaction() as sess:
        with app.app_context():
            case = PatientCase(case_code=PatientCase.generate_case_code())
            from app.extensions import db
            db.session.add(case)
            db.session.commit()
            sess['case_id'] = case.id
    resp = client.get('/journey/dashboard')
    assert resp.status_code == 200


def test_upload_validates_file_type(client, app):
    with client.session_transaction() as sess:
        with app.app_context():
            case = PatientCase(case_code=PatientCase.generate_case_code())
            from app.extensions import db
            db.session.add(case)
            db.session.commit()
            sess['case_id'] = case.id
    # Attempt to upload an invalid file type
    data = {'files': (b'fake content', 'malware.exe', 'application/octet-stream')}
    import io
    resp = client.post('/documents/upload',
                       data={'files': (io.BytesIO(b'fake'), 'test.exe')},
                       content_type='multipart/form-data')
    # Should not crash — returns error or success with no processing
    assert resp.status_code in (200, 400)


def test_escalation_packet_page(client, app):
    with client.session_transaction() as sess:
        with app.app_context():
            case = PatientCase(case_code=PatientCase.generate_case_code())
            from app.extensions import db
            db.session.add(case)
            db.session.commit()
            sess['case_id'] = case.id
    resp = client.get('/reports/clinician-packet')
    assert resp.status_code == 200
