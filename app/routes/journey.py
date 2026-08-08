"""
NidaanPath AI — app/routes/journey.py
Diagnostic Journey Twin routes.
"""
import json
from flask import Blueprint, render_template, session, redirect, url_for, jsonify
from ..extensions import db
from ..models.patient_case import PatientCase
from ..models.medical_document import MedicalDocument
from ..services.timeline_builder import build_timeline
from ..services.stagnation_engine import detect_process_gaps
from ..services.evidence_matcher import match_new_evidence, select_next_evidence_question
from ..services.escalation_packet import build_clinician_packet

journey_bp = Blueprint('journey', __name__)


@journey_bp.route('/dashboard')
def dashboard():
    case = _get_case()
    if not case:
        return redirect(url_for('main.index'))

    journey_data = _build_journey_for_case(case)

    return render_template(
        'journey_dashboard.html',
        case=case,
        journey=journey_data,
    )


@journey_bp.route('/uncertainty-ledger')
def uncertainty_ledger():
    case = _get_case()
    if not case:
        return redirect(url_for('main.index'))
    journey_data = _build_journey_for_case(case)
    return render_template(
        'uncertainty_ledger.html',
        case=case,
        journey=journey_data,
    )


@journey_bp.route('/simulation')
def simulation():
    case = _get_case()
    if not case:
        return redirect(url_for('main.index'))
    journey_data = _build_journey_for_case(case)
    has_report_09 = _case_has_report(case, 9)
    has_report_10 = _case_has_report(case, 10)
    return render_template(
        'simulation.html',
        case=case,
        journey=journey_data,
        has_report_09=has_report_09,
        has_report_10=has_report_10,
    )


@journey_bp.route('/api/state')
def api_state():
    case = _get_case()
    if not case:
        return jsonify({'error': 'No active case'}), 400
    journey_data = _build_journey_for_case(case)
    return jsonify(journey_data)


@journey_bp.route('/api/rebuild', methods=['POST'])
def api_rebuild():
    """Rebuild journey after new evidence added."""
    case = _get_case()
    if not case:
        return jsonify({'error': 'No active case'}), 400
    journey_data = _build_journey_for_case(case)
    return jsonify({'success': True, 'journey_state': journey_data['journey_state'],
                    'metrics': journey_data['metrics'],
                    'remaining_gaps': journey_data['remaining_gaps']})


def _build_journey_for_case(case: PatientCase) -> dict:
    """
    Core journey builder: extractions → timeline → gaps → state.
    Updates case in DB.
    """
    docs = MedicalDocument.query.filter_by(case_id=case.id)\
                                .order_by(MedicalDocument.upload_order).all()
    confirmed_docs = [d for d in docs if d.confirmed_by_user]
    extractions = [d.get_extraction() for d in confirmed_docs]

    # Build timeline
    timeline_data = build_timeline(extractions)

    # Detect gaps (Safety Gate 2 — Python only)
    gap_result = detect_process_gaps(extractions)

    # Update case state
    case.journey_state = gap_result['journey_state']
    case.set_stagnation_signals(gap_result['signals'])
    case.set_remaining_gaps(gap_result['gaps'])
    case.set_journey_events(timeline_data['events'])

    # Build uncertainty items
    uncertainty_items = _build_uncertainty_items(extractions, gap_result, confirmed_docs)
    case.set_uncertainty_items(uncertainty_items)

    db.session.commit()

    # Next evidence question
    next_question = select_next_evidence_question(gap_result['gaps'])

    return {
        'events': timeline_data['events'],
        'nodes': timeline_data['nodes'],
        'edges': timeline_data['edges'],
        'journey_state': gap_result['journey_state'],
        'signals': gap_result['signals'],
        'metrics': gap_result['metrics'],
        'remaining_gaps': gap_result['gaps'],
        'resolved_gaps': case.get_resolved_gaps(),
        'uncertainty_items': uncertainty_items,
        'next_question': next_question,
        'total_documents': len(docs),
        'confirmed_documents': len(confirmed_docs),
    }


def _build_uncertainty_items(extractions, gap_result, confirmed_docs):
    """Build the Diagnostic Uncertainty Ledger items."""
    items = []

    # Persistent symptom
    symptom_count = sum(
        1 for ex in extractions if any('dizziness' in s.lower() for s in ex.get('symptoms', []))
    )
    if symptom_count > 0:
        src = [ex.get('document_id', '') for ex in extractions if ex.get('symptoms')][:3]
        items.append({
            'information': 'Persistent dizziness',
            'status': 'confirmed',
            'status_label': 'Confirmed from Record',
            'sources': src,
            'confidence': 0.95,
            'required_action': None,
        })

    # CBC report
    cbc_docs = [ex for ex in extractions if 'CBC' in str(ex.get('tests_completed', []))]
    if cbc_docs:
        cbc_reviewed = any(ex.get('result_review_status') == 'reviewed' for ex in extractions)
        items.append({
            'information': 'CBC (Complete Blood Count) completed',
            'status': 'confirmed',
            'status_label': 'Confirmed from Record',
            'sources': [ex.get('document_id', '') for ex in cbc_docs],
            'confidence': 0.97,
            'required_action': None if cbc_reviewed else 'Confirm result was reviewed by clinician',
        })
        items.append({
            'information': 'CBC result reviewed by clinician',
            'status': 'reviewed' if cbc_reviewed else 'missing',
            'status_label': 'Confirmed' if cbc_reviewed else 'Missing',
            'sources': [],
            'confidence': 0.0 if not cbc_reviewed else 0.9,
            'required_action': None if cbc_reviewed else 'No review evidence found',
        })

    # ENT referral
    ent_referral = any(ex.get('referral_specialty') and 'ENT' in ex.get('referral_specialty', '')
                       for ex in extractions)
    ent_consultation = any(ex.get('document_type') == 'specialist_consultation_note'
                           for ex in extractions)
    if ent_referral:
        items.append({
            'information': 'ENT referral issued',
            'status': 'confirmed',
            'status_label': 'Confirmed from Record',
            'sources': [ex.get('document_id', '') for ex in extractions
                        if ex.get('referral_specialty')],
            'confidence': 0.91,
            'required_action': None,
        })
        items.append({
            'information': 'ENT specialist consultation completed',
            'status': 'confirmed' if ent_consultation else 'missing',
            'status_label': 'Confirmed' if ent_consultation else 'Missing',
            'sources': [ex.get('document_id', '') for ex in extractions
                        if ex.get('document_type') == 'specialist_consultation_note'],
            'confidence': 0.94 if ent_consultation else 0.0,
            'required_action': None if ent_consultation else 'Specialist note not found',
        })

    # Medication uncertainty
    all_meds = []
    for ex in extractions:
        all_meds.extend(ex.get('medication_mentions', []))
    if len(set(m.split()[0].lower() for m in all_meds if m)) > 2:
        items.append({
            'information': 'Multiple medication instructions across records',
            'status': 'clinician_review',
            'status_label': '⚠ Clinician Review Required',
            'sources': [ex.get('document_id', '') for ex in extractions
                        if ex.get('medication_mentions')],
            'confidence': 0.6,
            'required_action': 'Clinician to confirm current valid prescription',
        })

    # Fasting glucose
    glucose_docs = [ex for ex in extractions
                    if any('glucose' in t.lower() or 'fasting' in t.lower()
                           for t in ex.get('tests_completed', []))]
    glucose_reviewed = any(ex.get('result_review_status') == 'reviewed' and
                           any('glucose' in str(ex.get('source_fragments', [])).lower())
                           for ex in extractions)
    if glucose_docs:
        items.append({
            'information': 'Fasting glucose report completed',
            'status': 'confirmed',
            'status_label': 'Confirmed from Record',
            'sources': [ex.get('document_id', '') for ex in glucose_docs],
            'confidence': 0.96,
            'required_action': None,
        })

    return items


def _case_has_report(case: PatientCase, report_num: int) -> bool:
    return MedicalDocument.query.filter_by(
        case_id=case.id,
        demo_report_number=report_num,
        confirmed_by_user=True,
    ).first() is not None


def _get_case():
    case_id = session.get('case_id')
    if case_id:
        return PatientCase.query.get(case_id)
    return None
