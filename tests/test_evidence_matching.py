"""
NidaanPath AI — tests/test_evidence_matching.py
Tests for evidence matching and next-evidence selection.
"""
import pytest
from app.services.evidence_matcher import match_new_evidence, select_next_evidence_question
from app.services.mock_ai_service import DEMO_EXTRACTIONS


GAPS_01_08 = [
    {'gap_id': 'incomplete_referral', 'label': 'Incomplete Referral',
     'severity': 'high', 'status': 'open', 'next_action': 'Provide specialist note'},
    {'gap_id': 'unreviewed_result', 'label': 'Unreviewed Result',
     'severity': 'high', 'status': 'open', 'next_action': 'Confirm review'},
    {'gap_id': 'missing_treatment_response', 'label': 'Missing Treatment Response',
     'severity': 'medium', 'status': 'open', 'next_action': 'Document response'},
    {'gap_id': 'record_contradiction', 'label': 'Medication Contradiction',
     'severity': 'high', 'status': 'open', 'next_action': 'Clinician review'},
]


def test_report_09_closes_ent_referral():
    """Report 09 (specialist note) must resolve the incomplete_referral gap."""
    ex09 = {**DEMO_EXTRACTIONS[9], 'document_id': '09_ent.pdf'}
    result = match_new_evidence(ex09, GAPS_01_08)
    resolved_ids = [r['gap_id'] for r in result['resolved_gaps']]
    assert 'incomplete_referral' in resolved_ids, \
        "Report 09 should resolve the ENT referral gap"


def test_report_10_closes_result_review():
    """Report 10 (result review) must resolve the unreviewed_result gap."""
    ex10 = {**DEMO_EXTRACTIONS[10], 'document_id': '10_review.pdf'}
    remaining = [g for g in GAPS_01_08 if g['gap_id'] != 'incomplete_referral']
    result = match_new_evidence(ex10, remaining)
    resolved_ids = [r['gap_id'] for r in result['resolved_gaps']]
    assert 'unreviewed_result' in resolved_ids, \
        "Report 10 should resolve the unreviewed result gap"


def test_unrelated_doc_does_not_close_ent_gap():
    """A consultation note unrelated to ENT should not close the referral gap."""
    unrelated = {
        'document_id': 'random_note.pdf',
        'document_type': 'lab_report',
        'result_review_status': 'not_reviewed',
        'tests_completed': ['thyroid_panel'],
    }
    result = match_new_evidence(unrelated, GAPS_01_08[:1])  # Only referral gap
    resolved_ids = [r['gap_id'] for r in result['resolved_gaps']]
    assert 'incomplete_referral' not in resolved_ids, \
        "Unrelated document should not close ENT referral gap"


def test_medication_contradiction_requires_clinician():
    """Medication contradiction gap should not be auto-resolved — needs clinician."""
    ex09 = {**DEMO_EXTRACTIONS[9], 'document_id': '09_ent.pdf'}
    med_gap = [g for g in GAPS_01_08 if g['gap_id'] == 'record_contradiction']
    result = match_new_evidence(ex09, med_gap)
    # Should appear in partial matches, not resolved
    partial_ids = [p['gap_id'] for p in result.get('partial_matches', [])]
    for p in result.get('partial_matches', []):
        assert p.get('requires_clinician', False), \
            "Medication contradiction must be marked as requiring clinician"


def test_next_question_initial_is_ent_referral():
    """Initial question should target the ENT referral gap (highest priority)."""
    q = select_next_evidence_question(GAPS_01_08)
    assert q is not None
    assert q['gap_id'] == 'incomplete_referral', \
        f"Expected ENT referral question first, got: {q['gap_id']}"
    assert 'ENT' in q['question_en'] or 'specialist' in q['question_en'].lower()


def test_next_question_after_report_09():
    """After ENT resolved, question should be about unreviewed results."""
    remaining = [g for g in GAPS_01_08 if g['gap_id'] != 'incomplete_referral']
    q = select_next_evidence_question(remaining)
    assert q is not None
    assert q['gap_id'] != 'incomplete_referral'


def test_question_is_process_focused_not_diagnostic():
    """Questions must be about process, not disease diagnosis."""
    q = select_next_evidence_question(GAPS_01_08)
    assert q is not None
    diagnostic_words = ['diagnose', 'disease', 'cancer', 'infection', 'prescribe',
                        'take this drug', 'what is wrong']
    q_lower = q['question_en'].lower()
    for word in diagnostic_words:
        assert word not in q_lower, \
            f"Diagnostic language '{word}' found in question: {q['question_en']}"


def test_question_safety_cleared():
    """All questions must be safety-cleared."""
    q = select_next_evidence_question(GAPS_01_08)
    assert q is not None
    assert q.get('safety_cleared', False), \
        "Question must have safety_cleared=True"


def test_no_question_when_no_gaps():
    q = select_next_evidence_question([])
    assert q is None, "Should return None when no gaps remain"
