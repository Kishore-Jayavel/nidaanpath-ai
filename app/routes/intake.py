"""
NidaanPath AI — app/routes/intake.py
Patient story / narration intake routes.
"""
import json
from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify
from ..extensions import db
from ..models.patient_case import PatientCase
from ..services.ai_factory import get_ai_service

intake_bp = Blueprint('intake', __name__)

DEMO_NARRATION = (
    "I have had dizziness for about one month. I visited several doctors, "
    "completed two blood tests and received an ENT referral. "
    "I am not sure whether the reports were reviewed, and I do not know "
    "whether my earlier medicine should continue."
)


@intake_bp.route('/', methods=['GET', 'POST'])
def patient_story():
    case = _get_case()
    if not case:
        return redirect(url_for('main.index'))

    extracted = None
    if request.method == 'POST':
        narration = request.form.get('narration', '').strip()
        if narration:
            ai = get_ai_service()
            extracted = ai.extract_patient_narration(narration)
            case.patient_narration = narration
            case.narration_extraction_json = json.dumps(extracted)
            case.main_concern = extracted.get('main_concern', '')
            case.symptom_duration = extracted.get('symptom_duration', '')
            db.session.commit()

    narration_data = None
    if case.narration_extraction_json:
        try:
            narration_data = json.loads(case.narration_extraction_json)
        except Exception:
            pass

    return render_template(
        'intake.html',
        case=case,
        demo_narration=DEMO_NARRATION,
        extracted=narration_data,
    )


@intake_bp.route('/confirm', methods=['POST'])
def confirm_narration():
    case = _get_case()
    if not case:
        return redirect(url_for('main.index'))

    # Patient Safety Gate 1: confirmed fields from form
    case.main_concern = request.form.get('main_concern', case.main_concern or '')
    case.symptom_duration = request.form.get('symptom_duration', case.symptom_duration or '')
    case.language = request.form.get('preferred_language', case.language)
    db.session.commit()
    return redirect(url_for('documents.upload'))


@intake_bp.route('/load-demo-narration', methods=['POST'])
def load_demo_narration():
    case = _get_case()
    if not case:
        return jsonify({'error': 'No active case'}), 400
    ai = get_ai_service()
    extracted = ai.extract_patient_narration(DEMO_NARRATION)
    case.patient_narration = DEMO_NARRATION
    case.narration_extraction_json = json.dumps(extracted)
    case.main_concern = extracted.get('main_concern', 'Persistent dizziness')
    case.symptom_duration = extracted.get('symptom_duration', 'approximately 1 month')
    db.session.commit()
    return jsonify({'success': True, 'narration': DEMO_NARRATION, 'extracted': extracted})


def _get_case():
    case_id = session.get('case_id')
    if case_id:
        return PatientCase.query.get(case_id)
    return None
