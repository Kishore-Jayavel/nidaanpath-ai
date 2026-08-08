"""
NidaanPath AI — app/models/schemas.py
Pydantic schemas for structured AI extraction output.
"""
from __future__ import annotations
from typing import Optional, List, Any
from pydantic import BaseModel, Field


class ExtractedFinding(BaseModel):
    value: Any
    source_document: str
    source_fragment: str
    confidence: float = Field(ge=0.0, le=1.0)
    confirmed: bool = False


class MedicalDocumentExtraction(BaseModel):
    document_id: str
    document_type: str  # consultation_note, lab_report, prescription, referral, etc.
    document_date: Optional[str] = None
    provider: Optional[str] = None

    symptoms: List[ExtractedFinding] = []
    symptom_duration: Optional[str] = None
    tests_ordered: List[str] = []
    tests_completed: List[str] = []
    reports_available: List[str] = []
    referrals: List[str] = []
    referral_specialty: Optional[str] = None
    medication_mentions: List[str] = []
    treatment_response: Optional[str] = None
    follow_up_instructions: Optional[str] = None
    result_review_status: Optional[str] = None   # reviewed / not_reviewed / unknown
    diagnostic_closure_documented: bool = False
    source_fragments: List[str] = []
    uncertain_fields: List[str] = []
    extraction_confidence: float = Field(default=0.85, ge=0.0, le=1.0)


class PatientNarrationExtraction(BaseModel):
    main_concern: str
    symptom_duration: Optional[str] = None
    consultations_remembered: int = 0
    tests_remembered: List[str] = []
    referral_remembered: bool = False
    treatment_response: Optional[str] = None
    medication_concerns: List[str] = []
    preferred_language: str = 'en'
    extraction_confidence: float = 0.8
