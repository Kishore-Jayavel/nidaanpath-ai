"""
NidaanPath AI — app/routes/reports.py
Clinician packet, PDF download, and evaluation routes.
"""
import os
import json
from flask import (Blueprint, render_template, session, redirect, url_for,
                   jsonify, send_file, current_app)
from ..extensions import db
from ..models.patient_case import PatientCase
from ..models.medical_document import MedicalDocument
from ..services.escalation_packet import build_clinician_packet, generate_pdf_packet

reports_bp = Blueprint('reports', __name__)


@reports_bp.route('/clinician-packet')
def clinician_packet():
    case = _get_case()
    if not case:
        return redirect(url_for('main.index'))

    docs = MedicalDocument.query.filter_by(case_id=case.id)\
                                .order_by(MedicalDocument.upload_order).all()
    packet = build_clinician_packet(case, docs)
    return render_template('escalation_packet.html', case=case, packet=packet)


@reports_bp.route('/download-pdf')
def download_pdf():
    case = _get_case()
    if not case:
        return redirect(url_for('main.index'))

    docs = MedicalDocument.query.filter_by(case_id=case.id)\
                                .order_by(MedicalDocument.upload_order).all()
    packet = build_clinician_packet(case, docs)

    out_dir = current_app.config['GENERATED_REPORTS_FOLDER']
    pdf_path = os.path.join(out_dir, f'clinician_packet_{case.case_code}.pdf')

    success = generate_pdf_packet(packet, pdf_path)
    if not success:
        return jsonify({'error': 'PDF generation failed'}), 500

    return send_file(
        pdf_path,
        as_attachment=True,
        download_name=f'NidaanPath_Clinician_Packet_{case.case_code}.pdf',
        mimetype='application/pdf',
    )


@reports_bp.route('/evaluation')
def evaluation():
    case = _get_case()
    if not case:
        return redirect(url_for('main.index'))

    ground_truth = _load_ground_truth()
    docs = MedicalDocument.query.filter_by(case_id=case.id).all()
    eval_results = _run_evaluation(docs, ground_truth)

    return render_template(
        'evaluation.html',
        case=case,
        ground_truth=ground_truth,
        eval_results=eval_results,
    )


def _load_ground_truth() -> dict:
    """Load ground_truth_manifest.json from demo_reports/."""
    from flask import current_app
    gt_path = os.path.join(
        current_app.config['DEMO_REPORTS_FOLDER'],
        'ground_truth_manifest.json'
    )
    if os.path.exists(gt_path):
        try:
            with open(gt_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    # Fallback ground truth
    return _fallback_ground_truth()


def _fallback_ground_truth() -> dict:
    return {
        "patient": {
            "name": "Arun Kumar",
            "main_concern": "Persistent dizziness",
            "symptom_duration": "approximately 2 months"
        },
        "documents": [
            {"number": 1, "type": "consultation_note", "date": "2024-06-03",
             "expected_symptoms": ["dizziness"], "expected_tests_ordered": ["CBC"]},
            {"number": 2, "type": "lab_report", "date": "2024-06-05",
             "expected_tests_completed": ["CBC"], "expected_review": False},
            {"number": 3, "type": "appointment_slip", "date": "2024-06-10"},
            {"number": 4, "type": "prescription", "date": "2024-06-18"},
            {"number": 5, "type": "lab_report", "date": "2024-06-20",
             "expected_tests_completed": ["Fasting Blood Glucose"]},
            {"number": 6, "type": "referral_slip", "date": "2024-06-27",
             "expected_referral": "ENT"},
            {"number": 7, "type": "patient_narration", "date": "2024-07-05"},
            {"number": 8, "type": "consultation_note", "date": "2024-07-10"},
            {"number": 9, "type": "specialist_consultation_note", "date": "2024-07-15",
             "resolves_gap": "incomplete_referral"},
            {"number": 10, "type": "result_review_note", "date": "2024-07-22",
             "resolves_gap": "unreviewed_result"},
        ],
        "expected_journey_states": {
            "reports_01_08": "Possible Stagnation",
            "after_report_09": "Active Progress",
            "after_report_10": "Active Progress",
        },
        "expected_gaps": [
            "incomplete_referral", "unreviewed_result",
            "missing_treatment_response", "record_contradiction"
        ]
    }


def _run_evaluation(docs, ground_truth) -> list:
    """Compare detected results against ground truth."""
    results = []
    gt_docs = {d['number']: d for d in ground_truth.get('documents', [])}

    for doc in docs:
        num = doc.demo_report_number
        if not num or num not in gt_docs:
            continue
        gt = gt_docs[num]
        ex = doc.get_extraction()

        # Type match
        detected_type = doc.document_type or ''
        expected_type = gt.get('type', '')
        type_match = detected_type == expected_type or \
                     detected_type.replace('_', '') == expected_type.replace('_', '')

        # Date match
        detected_date = doc.document_date or ''
        expected_date = gt.get('date', '')
        date_match = detected_date[:10] == expected_date[:10] if detected_date and expected_date else False

        results.append({
            'document': doc.original_filename,
            'report_number': num,
            'expected_type': expected_type,
            'detected_type': detected_type,
            'type_matched': type_match,
            'expected_date': expected_date,
            'detected_date': detected_date,
            'date_matched': date_match,
            'extraction_confidence': doc.extraction_confidence,
            'confirmed': doc.confirmed_by_user,
        })

    return results


def _get_case():
    case_id = session.get('case_id')
    if case_id:
        return PatientCase.query.get(case_id)
    return None
