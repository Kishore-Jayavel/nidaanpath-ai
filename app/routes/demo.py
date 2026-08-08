"""
NidaanPath AI — app/routes/demo.py
Judge Demo Mode routes — full sequenced demonstration.
"""
import json
from flask import Blueprint, render_template, session, redirect, url_for, jsonify, request
from ..extensions import db
from ..models.patient_case import PatientCase
from ..models.medical_document import MedicalDocument
from ..services.document_extractor import extract_text, get_demo_report_number
from ..services.ai_factory import get_ai_service
from ..services.stagnation_engine import detect_process_gaps
from ..services.evidence_matcher import match_new_evidence, select_next_evidence_question
import os
from flask import current_app

demo_bp = Blueprint('demo', __name__)


@demo_bp.route('/')
def demo_home():
    """Judge Demo landing page."""
    case = _get_or_create_demo_case()
    docs = MedicalDocument.query.filter_by(case_id=case.id)\
                                .order_by(MedicalDocument.upload_order).all()
    loaded_reports = [d.demo_report_number for d in docs if d.demo_report_number]
    journey_state = case.journey_state
    return render_template(
        'demo.html',
        case=case,
        loaded_reports=loaded_reports,
        journey_state=journey_state,
    )


@demo_bp.route('/load-batch', methods=['POST'])
def load_batch():
    """Load demo reports 01–08 (stagnation state)."""
    case = _get_or_create_demo_case()
    data = request.get_json() or {}
    reports = data.get('reports', list(range(1, 9)))  # Default 1-8

    demo_folder = current_app.config['DEMO_REPORTS_FOLDER']
    loaded = []
    ai = get_ai_service()

    for num in reports:
        # Skip if already loaded
        existing = MedicalDocument.query.filter_by(
            case_id=case.id, demo_report_number=num
        ).first()
        if existing:
            loaded.append({'number': num, 'status': 'already_loaded'})
            continue

        # Find file — fall back to mock-only extraction if PDF not present
        matching = _find_demo_file(demo_folder, num)
        if matching:
            file_path = os.path.join(demo_folder, matching)
            raw_text, ok = extract_text(file_path)
        else:
            # No PDF present: use mock AI extraction directly (judge demo mode)
            file_path = None
            raw_text = ''
            matching = f'{num:02d}_synthetic_report.pdf'

        extraction = ai.extract_medical_document(
            filename=matching, raw_text=raw_text, demo_report_number=num
        )

        order = MedicalDocument.query.filter_by(case_id=case.id).count()
        doc = MedicalDocument(
            case_id=case.id,
            filename=matching,
            original_filename=matching,
            file_path=file_path or '',
            demo_report_number=num,
            document_type=extraction.get('document_type'),
            document_date=extraction.get('document_date'),
            provider=extraction.get('provider'),
            extraction_status='confirmed',
            extraction_confidence=extraction.get('extraction_confidence', 0.85),
            raw_text=raw_text[:5000],
            upload_order=order,
            confirmed_by_user=True,
        )
        doc.set_extraction(extraction)
        db.session.add(doc)
        loaded.append({'number': num, 'status': 'loaded', 'filename': matching})

    db.session.commit()

    # Calculate journey state
    all_docs = MedicalDocument.query.filter_by(case_id=case.id)\
                                    .order_by(MedicalDocument.upload_order).all()
    extractions = [d.get_extraction() for d in all_docs if d.confirmed_by_user]
    gap_result = detect_process_gaps(extractions)

    case.journey_state = gap_result['journey_state']
    case.set_remaining_gaps(gap_result['gaps'])
    case.set_stagnation_signals(gap_result['signals'])
    db.session.commit()

    return jsonify({
        'success': True,
        'loaded': loaded,
        'journey_state': gap_result['journey_state'],
        'metrics': gap_result['metrics'],
        'remaining_gaps': len(gap_result['gaps']),
        'signals': [s['signal_type'] for s in gap_result['signals']],
    })


@demo_bp.route('/add-evidence/<int:report_num>', methods=['POST'])
def add_evidence(report_num: int):
    """Add a specific evidence report (09 or 10) and recalculate state."""
    if report_num not in (9, 10):
        return jsonify({'error': 'Only reports 09 and 10 supported here'}), 400

    case = _get_or_create_demo_case()
    demo_folder = current_app.config['DEMO_REPORTS_FOLDER']

    matching = _find_demo_file(demo_folder, report_num)
    if matching:
        file_path = os.path.join(demo_folder, matching)
        raw_text, ok = extract_text(file_path)
    else:
        file_path = ''
        raw_text = ''
        matching = f'{report_num:02d}_synthetic_report.pdf'

    # Check if already loaded
    existing = MedicalDocument.query.filter_by(
        case_id=case.id, demo_report_number=report_num
    ).first()

    if not existing:
        ai = get_ai_service()
        extraction = ai.extract_medical_document(
            filename=matching, raw_text=raw_text, demo_report_number=report_num
        )
        order = MedicalDocument.query.filter_by(case_id=case.id).count()
        doc = MedicalDocument(
            case_id=case.id,
            filename=matching,
            original_filename=matching,
            file_path=file_path,
            demo_report_number=report_num,
            document_type=extraction.get('document_type'),
            document_date=extraction.get('document_date'),
            provider=extraction.get('provider'),
            extraction_status='confirmed',
            extraction_confidence=extraction.get('extraction_confidence', 0.85),
            raw_text=raw_text[:5000],
            upload_order=order,
            confirmed_by_user=True,
        )
        doc.set_extraction(extraction)
        db.session.add(doc)
        db.session.commit()
        new_doc = doc
    else:
        new_doc = existing

    # Rebuild journey with all confirmed docs
    all_docs = MedicalDocument.query.filter_by(case_id=case.id)\
                                    .order_by(MedicalDocument.upload_order).all()
    extractions = [d.get_extraction() for d in all_docs if d.confirmed_by_user]
    gap_result = detect_process_gaps(extractions)

    # Match new evidence against remaining gaps (from BEFORE this upload)
    before_gaps = case.get_remaining_gaps()
    new_ex = new_doc.get_extraction()
    match_result = match_new_evidence(new_ex, before_gaps)

    # Update resolved/remaining
    resolved = case.get_resolved_gaps()
    resolved.extend(match_result['resolved_gaps'])
    case.set_resolved_gaps(resolved)

    # Effective remaining gaps = fresh gaps - ones just resolved
    resolved_ids = {r['gap_id'] for r in match_result['resolved_gaps']}
    remaining = [g for g in gap_result['gaps'] if g['gap_id'] not in resolved_ids]
    case.set_remaining_gaps(remaining)

    # Compute effective journey state based on remaining (not all) gaps
    from app.services.stagnation_engine import STATE_ACTIVE_PROGRESS, STATE_POSSIBLE_STAGNATION
    high_remaining = [g for g in remaining if g.get('severity') == 'high']
    if len(high_remaining) == 0:
        effective_state = STATE_ACTIVE_PROGRESS
    elif len(high_remaining) <= 2:
        # If latest doc is specialist or review note → Active Progress
        latest_type = extractions[-1].get('document_type', '') if extractions else ''
        if latest_type in ('specialist_consultation_note', 'result_review_note'):
            effective_state = STATE_ACTIVE_PROGRESS
        else:
            effective_state = STATE_POSSIBLE_STAGNATION
    else:
        effective_state = STATE_POSSIBLE_STAGNATION

    case.journey_state = effective_state
    case.set_stagnation_signals(gap_result['signals'])
    db.session.commit()

    return jsonify({
        'success': True,
        'report_number': report_num,
        'journey_state': effective_state,
        'metrics': gap_result['metrics'],
        'resolved_gaps': [r['gap_id'] for r in match_result['resolved_gaps']],
        'remaining_gaps': len(remaining),
        'partial_matches': match_result.get('partial_matches', []),
    })




@demo_bp.route('/reset', methods=['POST'])
def reset_demo():
    """Reset the judge demo to a fresh state."""
    case_id = session.get('case_id')
    if case_id:
        case = PatientCase.query.get(case_id)
        if case and case.demo_mode:
            db.session.delete(case)
            db.session.commit()
            session.pop('case_id', None)
    return jsonify({'success': True})


@demo_bp.route('/state')
def demo_state():
    """Return current demo state as JSON."""
    case = _get_or_create_demo_case()
    docs = MedicalDocument.query.filter_by(case_id=case.id).all()
    return jsonify({
        'case_code': case.case_code,
        'demo_mode': case.demo_mode,
        'journey_state': case.journey_state,
        'loaded_reports': sorted([d.demo_report_number for d in docs if d.demo_report_number]),
        'remaining_gaps': len(case.get_remaining_gaps()),
        'resolved_gaps': len(case.get_resolved_gaps()),
    })


def _find_demo_file(demo_folder: str, num: int) -> str:
    """Find demo file by report number."""
    if not os.path.exists(demo_folder):
        return None
    for f in sorted(os.listdir(demo_folder)):
        if f.startswith(f'{num:02d}_') and f.endswith('.pdf'):
            return f
    return None


def _get_or_create_demo_case() -> PatientCase:
    case_id = session.get('case_id')
    if case_id:
        case = PatientCase.query.get(case_id)
        if case:
            if not case.demo_mode:
                case.demo_mode = True
                case.patient_name = 'Arun Kumar'
                case.main_concern = 'Persistent dizziness for approximately one month'
                case.symptom_duration = 'Approximately 2 months'
                db.session.commit()
            return case

    case = PatientCase(
        case_code=PatientCase.generate_case_code(),
        demo_mode=True,
        language='en',
        patient_name='Arun Kumar',
        main_concern='Persistent dizziness for approximately one month',
        symptom_duration='Approximately 2 months',
    )
    db.session.add(case)
    db.session.commit()
    session['case_id'] = case.id
    return case
