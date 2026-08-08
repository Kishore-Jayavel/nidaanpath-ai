"""
NidaanPath AI — tests/test_safety.py
Safety gate tests — ensures NidaanPath never produces
diagnostic, prescriptive, or accusatory output.
"""
import pytest
from app.services.stagnation_engine import detect_process_gaps
from app.services.evidence_matcher import select_next_evidence_question
from app.services.mock_ai_service import MockAIService, DEMO_EXTRACTIONS

FORBIDDEN_DIAGNOSTIC = [
    'diagnosis', 'diagnose', 'cancer', 'diabetes', 'hypertension',
    'vestibular migraine', 'bppv', 'negligence', 'malpractice',
    'wrong', 'incorrect doctor', 'prescribe', 'take medication',
    'stop treatment', 'recommend test', 'medical error'
]


def get_exs(nums):
    return [{**DEMO_EXTRACTIONS[i], 'document_id': f'{i:02d}.pdf'} for i in nums]


def test_journey_state_not_diagnostic():
    result = detect_process_gaps(get_exs(range(1, 9)))
    state = result['journey_state'].lower()
    for word in FORBIDDEN_DIAGNOSTIC:
        assert word not in state, f"Forbidden word in state: {word}"


def test_signal_descriptions_not_diagnostic():
    result = detect_process_gaps(get_exs(range(1, 9)))
    for sig in result['signals']:
        desc = sig['description'].lower()
        for word in ['diagnos', 'disease', 'cancer', 'prescri', 'negligence']:
            assert word not in desc, \
                f"Forbidden word '{word}' in signal: {desc}"


def test_gaps_not_diagnostic():
    result = detect_process_gaps(get_exs(range(1, 9)))
    # Gaps may reference 'diagnostic' in process context (e.g. 'diagnostic direction')
    # but must NOT claim to diagnose a disease or prescribe treatment
    forbidden_in_gaps = [
        'you have', 'cancer', 'diabetes', 'hypertension', 'prescribe',
        'take this medicine', 'stop treatment', 'negligence', 'malpractice'
    ]
    for gap in result['gaps']:
        for text in [gap.get('label', ''), gap.get('description', ''), gap.get('next_action', '')]:
            for word in forbidden_in_gaps:
                assert word not in text.lower(), \
                    f"Forbidden word '{word}' in gap text: {text}"


def test_agent_questions_not_diagnostic():
    gaps = [
        {'gap_id': 'incomplete_referral', 'label': 'Incomplete Referral'},
        {'gap_id': 'unreviewed_result', 'label': 'Unreviewed Result'},
        {'gap_id': 'missing_treatment_response', 'label': 'Missing Treatment Response'},
    ]
    for gap_list in [gaps, gaps[1:], gaps[2:]]:
        q = select_next_evidence_question(gap_list)
        if q:
            q_text = q['question_en'].lower()
            for word in ['diagnos', 'cancer', 'disease name', 'prescribe', 'recommend medication']:
                assert word not in q_text, \
                    f"Diagnostic language in question: {word}"


def test_mock_ai_no_diagnosis():
    ai = MockAIService()
    for num in range(1, 11):
        result = ai.extract_medical_document(f'{num:02d}.pdf', '', demo_report_number=num)
        # Result must not contain a disease diagnosis
        fragments = result.get('source_fragments', [])
        for frag in fragments:
            # Source fragments can mention symptoms but not diagnose
            assert 'diagnosis:' not in frag.lower(), \
                f"Source fragment contains diagnosis: {frag}"


def test_clinician_summary_no_diagnosis():
    ai = MockAIService()
    summary = ai.generate_clinician_summary({
        'journey_state': 'Possible Stagnation',
        'remaining_gaps': [{'label': 'Unreviewed result'}],
    })
    # 'diagnosis' in disclaimer ('is not a diagnosis') is acceptable — block active claims
    forbidden_active_claims = ['you have', 'cancer', 'diabetes', 'prescribe', 'take medication']
    for word in forbidden_active_claims:
        assert word not in summary.lower(), \
            f"Clinician summary contains forbidden claim: {word}"


def test_extraction_confidence_not_fabricated():
    """Confidence must reflect actual extraction quality, not be fabricated at 100%."""
    ai = MockAIService()
    # Patient narration should have lower confidence than a clean lab report
    narration_result = ai.extract_medical_document('07.pdf', '', demo_report_number=7)
    lab_result = ai.extract_medical_document('02.pdf', '', demo_report_number=2)
    # Lab report should have higher or equal confidence
    assert lab_result['extraction_confidence'] >= narration_result['extraction_confidence']


def test_uncertain_fields_never_silently_resolved():
    """Fields marked as uncertain must appear in uncertain_fields list."""
    ai = MockAIService()
    result = ai.extract_medical_document('07.pdf', '', demo_report_number=7)
    uncertain = result.get('uncertain_fields', [])
    assert len(uncertain) > 0, \
        "Patient narration (report 7) must have uncertain fields — not silently resolved"
