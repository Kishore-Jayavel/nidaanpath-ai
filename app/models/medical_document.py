"""
NidaanPath AI — app/models/medical_document.py
SQLAlchemy model for uploaded medical documents.
"""
import json
import uuid
from datetime import datetime
from ..extensions import db


class MedicalDocument(db.Model):
    __tablename__ = 'medical_documents'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    case_id = db.Column(db.String(36), db.ForeignKey('patient_cases.id'), nullable=False)

    filename = db.Column(db.String(500), nullable=False)
    original_filename = db.Column(db.String(500), nullable=False)
    file_path = db.Column(db.String(1000), nullable=True)
    file_size = db.Column(db.Integer, default=0)
    mime_type = db.Column(db.String(100), nullable=True)
    demo_report_number = db.Column(db.Integer, nullable=True)  # 1-10 for demo docs

    # Extraction state
    document_type = db.Column(db.String(100), nullable=True)
    document_date = db.Column(db.String(50), nullable=True)
    provider = db.Column(db.String(200), nullable=True)
    extraction_status = db.Column(db.String(30), default='pending')
    # pending, extracting, extracted, confirmed, rejected, unreadable
    extraction_json = db.Column(db.Text, nullable=True)
    extraction_confidence = db.Column(db.Float, default=0.0)
    confirmed_by_user = db.Column(db.Boolean, default=False)
    raw_text = db.Column(db.Text, nullable=True)

    upload_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def get_extraction(self):
        if self.extraction_json:
            return json.loads(self.extraction_json)
        return {}

    def set_extraction(self, data: dict):
        self.extraction_json = json.dumps(data)

    def to_dict(self):
        return {
            'id': self.id,
            'case_id': self.case_id,
            'filename': self.filename,
            'original_filename': self.original_filename,
            'demo_report_number': self.demo_report_number,
            'document_type': self.document_type,
            'document_date': self.document_date,
            'provider': self.provider,
            'extraction_status': self.extraction_status,
            'extraction_confidence': self.extraction_confidence,
            'confirmed_by_user': self.confirmed_by_user,
            'upload_order': self.upload_order,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
