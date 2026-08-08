"""
NidaanPath AI — tests/test_document_extraction.py
Tests for document extraction and mock AI service.
"""
import pytest
from app.services.mock_ai_service import MockAIService, DEMO_EXTRACTIONS


def test_demo_report_1_type():
    ai = MockAIService()
    result = ai.extract_medical_document('01_initial.pdf', '', demo_report_number=1)
    assert result['document_type'] == 'consultation_note'


def test_demo_report_2_type():
    ai = MockAIService()
    result = ai.extract_medical_document('02_cbc.pdf', '', demo_report_number=2)
    assert result['document_type'] == 'lab_report'


def test_demo_report_6_referral():
    ai = MockAIService()
    result = ai.extract_medical_document('06_referral.pdf', '', demo_report_number=6)
    assert result['referral_specialty'] is not None
    assert 'ENT' in result['referral_specialty']


def test_demo_report_9_specialist():
    ai = MockAIService()
    result = ai.extract_medical_document('09_ent.pdf', '', demo_report_number=9)
    assert result['document_type'] == 'specialist_consultation_note'


def test_demo_report_10_reviewed():
    ai = MockAIService()
    result = ai.extract_medical_document('10_review.pdf', '', demo_report_number=10)
    assert result['result_review_status'] == 'reviewed'


def test_report_2_not_reviewed():
    ai = MockAIService()
    result = ai.extract_medical_document('02_cbc.pdf', '', demo_report_number=2)
    assert result['result_review_status'] == 'not_reviewed'


def test_empty_document_handled():
    ai = MockAIService()
    result = ai.extract_medical_document('empty.pdf', '', demo_report_number=None)
    assert isinstance(result, dict)
    assert 'document_type' in result


def test_invalid_text_handled():
    ai = MockAIService()
    result = ai.extract_medical_document('junk.pdf', '!!@@##$$%%', demo_report_number=None)
    assert isinstance(result, dict)
    assert result['extraction_confidence'] >= 0


def test_extraction_confidence_in_range():
    ai = MockAIService()
    for num in range(1, 11):
        result = ai.extract_medical_document(f'{num:02d}.pdf', '', demo_report_number=num)
        assert 0.0 <= result['extraction_confidence'] <= 1.0


def test_symptoms_are_lists():
    ai = MockAIService()
    result = ai.extract_medical_document('01.pdf', '', demo_report_number=1)
    assert isinstance(result['symptoms'], list)


def test_no_diagnosis_in_extraction():
    """Extraction must not contain disease names or diagnoses."""
    ai = MockAIService()
    for num in range(1, 11):
        result = ai.extract_medical_document(f'{num:02d}.pdf', '', demo_report_number=num)
        # document_type should not suggest a diagnosis
        doc_type = result.get('document_type', '')
        assert 'diagnosis' not in doc_type.lower()


def test_narration_extraction():
    ai = MockAIService()
    result = ai.extract_patient_narration(
        "I have dizziness for 1 month. Two blood tests done. ENT referral given."
    )
    assert 'main_concern' in result
    assert isinstance(result['consultations_remembered'], int)


def test_uncertain_fields_preserved():
    ai = MockAIService()
    result = ai.extract_medical_document('07.pdf', '', demo_report_number=7)
    assert isinstance(result['uncertain_fields'], list)
    # Report 7 (patient narration) should have uncertain fields
    assert len(result['uncertain_fields']) > 0
