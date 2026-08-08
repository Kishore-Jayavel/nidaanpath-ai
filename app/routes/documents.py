"""
NidaanPath AI — app/routes/documents.py
Document upload, extraction, and confirmation routes.
"""
import os
import json
from flask import (Blueprint, render_template, request, redirect, url_for,
                   session, jsonify, current_app)
from ..extensions import db
from ..models.patient_case import PatientCase
from ..models.medical_document import MedicalDocument
from ..services.document_extractor import (
    allowed_file, extract_text, get_demo_report_number, secure_save_file
)
from ..services.ai_factory import get_ai_service

documents_bp = Blueprint('documents', __name__)


@documents_bp.route('/', methods=['GET'])
def upload():
    case = _get_case()
    if not case:
        return redirect(url_for('main.index'))
    docs = MedicalDocument.query.filter_by(case_id=case.id)\
                                .order_by(MedicalDocument.upload_order).all()
    return render_template('documents.html', case=case, documents=docs)


@documents_bp.route('/upload', methods=['POST'])
def do_upload():
    """Handle file upload, extraction and initial AI processing."""
    case = _get_case()
    if not case:
        return jsonify({'error': 'No active case'}), 400

    if 'files' not in request.files:
        return jsonify({'error': 'No files provided'}), 400

    files = request.files.getlist('files')
    results = []

    for file_obj in files:
        if not file_obj or not file_obj.filename:
            continue
        if not allowed_file(file_obj.filename):
            results.append({'filename': file_obj.filename, 'error': 'File type not allowed'})
            continue

        # Save file
        try:
            secure_name, full_path = secure_save_file(
                file_obj, current_app.config['UPLOAD_FOLDER']
            )
        except Exception as e:
            results.append({'filename': file_obj.filename, 'error': str(e)})
            continue

        # Extract text
        raw_text, ok = extract_text(full_path)

        # Detect demo report number
        demo_num = get_demo_report_number(file_obj.filename)

        # AI extraction
        ai = get_ai_service()
        extraction = ai.extract_medical_document(
            filename=file_obj.filename,
            raw_text=raw_text,
            demo_report_number=demo_num,
        )

        # Count existing docs for upload order
        order = MedicalDocument.query.filter_by(case_id=case.id).count()

        doc = MedicalDocument(
            case_id=case.id,
            filename=secure_name,
            original_filename=file_obj.filename,
            file_path=full_path,
            demo_report_number=demo_num,
            document_type=extraction.get('document_type'),
            document_date=extraction.get('document_date'),
            provider=extraction.get('provider'),
            extraction_status='extracted',
            extraction_confidence=extraction.get('extraction_confidence', 0.8),
            raw_text=raw_text[:5000],
            upload_order=order,
        )
        doc.set_extraction(extraction)
        db.session.add(doc)

    db.session.commit()
    return jsonify({'success': True, 'message': f'{len(files)} file(s) processed'})


@documents_bp.route('/load-demo/<int:report_num>', methods=['POST'])
def load_demo_report(report_num: int):
    """Load a specific demo report from the demo_reports folder."""
    case = _get_case()
    if not case:
        return jsonify({'error': 'No active case'}), 400

    if report_num < 1 or report_num > 10:
        return jsonify({'error': 'Invalid report number'}), 400

    demo_folder = current_app.config['DEMO_REPORTS_FOLDER']
    # Find matching file
    matching = None
    for f in os.listdir(demo_folder):
        if f.startswith(f'{report_num:02d}_') and f.endswith('.pdf'):
            matching = f
            break
    if not matching:
        # Try single digit
        for f in os.listdir(demo_folder):
            if f.startswith(f'0{report_num}_') and f.endswith('.pdf'):
                matching = f
                break

    if not matching:
        return jsonify({'error': f'Demo report {report_num} not found'}), 404

    file_path = os.path.join(demo_folder, matching)

    # Check if already loaded
    existing = MedicalDocument.query.filter_by(
        case_id=case.id, demo_report_number=report_num
    ).first()
    if existing:
        return jsonify({
            'success': True,
            'message': f'Report {report_num} already loaded',
            'doc_id': existing.id,
            'already_existed': True,
        })

    # Extract text
    raw_text, ok = extract_text(file_path)

    # AI extraction
    ai = get_ai_service()
    extraction = ai.extract_medical_document(
        filename=matching,
        raw_text=raw_text,
        demo_report_number=report_num,
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
        extraction_status='extracted',
        extraction_confidence=extraction.get('extraction_confidence', 0.85),
        raw_text=raw_text[:5000],
        upload_order=order,
        confirmed_by_user=True,  # Auto-confirm demo docs for judge flow
    )
    doc.set_extraction(extraction)
    db.session.add(doc)
    db.session.commit()

    return jsonify({
        'success': True,
        'doc_id': doc.id,
        'filename': matching,
        'document_type': doc.document_type,
        'document_date': doc.document_date,
        'provider': doc.provider,
        'extraction_confidence': doc.extraction_confidence,
        'already_existed': False,
    })


@documents_bp.route('/confirm/<doc_id>', methods=['POST'])
def confirm_document(doc_id: str):
    """Patient Safety Gate 1: Confirm extracted document data."""
    case = _get_case()
    doc = MedicalDocument.query.filter_by(id=doc_id, case_id=case.id if case else None).first()
    if not doc:
        return jsonify({'error': 'Document not found'}), 404

    # Allow patient to correct fields
    action = request.form.get('action', 'confirm')
    if action == 'confirm':
        doc.confirmed_by_user = True
        doc.extraction_status = 'confirmed'
    elif action == 'reject':
        doc.extraction_status = 'rejected'
    elif action == 'unreadable':
        doc.extraction_status = 'unreadable'
    else:
        doc.confirmed_by_user = True
        doc.extraction_status = 'confirmed'

    db.session.commit()
    return jsonify({'success': True, 'status': doc.extraction_status})


@documents_bp.route('/extraction-review')
def extraction_review():
    case = _get_case()
    if not case:
        return redirect(url_for('main.index'))
    docs = MedicalDocument.query.filter_by(case_id=case.id)\
                                .order_by(MedicalDocument.upload_order).all()
    docs_data = []
    for doc in docs:
        d = doc.to_dict()
        d['extraction'] = doc.get_extraction()
        docs_data.append(d)
    return render_template('extraction_review.html', case=case, documents=docs_data)


@documents_bp.route('/api/list')
def list_documents():
    case = _get_case()
    if not case:
        return jsonify({'documents': []})
    docs = MedicalDocument.query.filter_by(case_id=case.id)\
                                .order_by(MedicalDocument.upload_order).all()
    return jsonify({'documents': [d.to_dict() for d in docs]})


def _get_case():
    case_id = session.get('case_id')
    if case_id:
        return PatientCase.query.get(case_id)
    return None
