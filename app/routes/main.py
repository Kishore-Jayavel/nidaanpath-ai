"""
NidaanPath AI — app/routes/main.py
Landing page and utility routes.
"""
from flask import Blueprint, render_template, session, redirect, url_for, jsonify
from ..models.patient_case import PatientCase
from ..extensions import db

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    case = _get_or_create_case()
    return render_template('index.html', case=case)


@main_bp.route('/responsible-ai')
def responsible_ai():
    return render_template('responsible_ai.html')


@main_bp.route('/clear-case', methods=['POST'])
def clear_case():
    case_id = session.get('case_id')
    if case_id:
        case = PatientCase.query.get(case_id)
        if case:
            db.session.delete(case)
            db.session.commit()
        session.clear()
    return redirect(url_for('main.index'))


@main_bp.route('/api/status')
def status():
    from flask import current_app
    use_mock = current_app.config.get('USE_MOCK_LLM', True)
    return jsonify({
        'status': 'ok',
        'mode': 'mock' if use_mock else 'gemini',
        'version': '1.0.0-mvp',
    })


def _get_or_create_case() -> PatientCase:
    case_id = session.get('case_id')
    if case_id:
        case = PatientCase.query.get(case_id)
        if case:
            return case
    # Create new case
    case = PatientCase(
        case_code=PatientCase.generate_case_code(),
        language='en',
    )
    db.session.add(case)
    db.session.commit()
    session['case_id'] = case.id
    return case
