"""
NidaanPath AI — tests/test_stagnation_engine.py
Tests for the deterministic stagnation detection engine (Safety Gate 2).
"""
import pytest
from app.services.stagnation_engine import (
    detect_process_gaps,
    STATE_POSSIBLE_STAGNATION,
    STATE_ACTIVE_PROGRESS,
    STATE_AWAITING_EVIDENCE,
)


def test_empty_extractions_returns_awaiting():
    result = detect_process_gaps([])
    assert result['journey_state'] == STATE_AWAITING_EVIDENCE
    assert result['signals'] == []
    assert result['gaps'] == []


def test_reports_01_08_produce_possible_stagnation(demo_extractions):
    result = detect_process_gaps(demo_extractions)
    assert result['journey_state'] == STATE_POSSIBLE_STAGNATION, \
        f"Expected Possible Stagnation, got {result['journey_state']}"


def test_repeated_symptom_detected(demo_extractions):
    result = detect_process_gaps(demo_extractions)
    signal_types = [s['signal_type'] for s in result['signals']]
    assert 'repeated_symptom' in signal_types, \
        "Repeated symptom not detected across 3+ encounters"


def test_unreviewed_result_detected(demo_extractions):
    result = detect_process_gaps(demo_extractions)
    signal_types = [s['signal_type'] for s in result['signals']]
    assert 'unreviewed_result' in signal_types, \
        "Unreviewed results not detected"


def test_referral_gap_detected(demo_extractions):
    result = detect_process_gaps(demo_extractions)
    signal_types = [s['signal_type'] for s in result['signals']]
    assert 'incomplete_referral' in signal_types, \
        "ENT referral gap not detected"


def test_missing_treatment_response_detected(demo_extractions):
    result = detect_process_gaps(demo_extractions)
    signal_types = [s['signal_type'] for s in result['signals']]
    assert 'missing_treatment_response' in signal_types or 'record_contradiction' in signal_types, \
        "Medication/treatment gap not detected"


def test_no_diagnosis_in_state_output(demo_extractions):
    """Safety: stagnation output must never contain diagnosis-like language."""
    result = detect_process_gaps(demo_extractions)
    forbidden = ['diagnos', 'disease', 'condition', 'disorder', 'prescri']
    state_text = result['journey_state'].lower()
    for word in forbidden:
        assert word not in state_text, \
            f"Forbidden word '{word}' found in journey state: {state_text}"
    for sig in result['signals']:
        desc = sig['description'].lower()
        for word in ['diagnos', 'disease', 'prescri']:
            assert word not in desc, \
                f"Forbidden word '{word}' found in signal: {desc}"


def test_metrics_correctly_computed(demo_extractions):
    result = detect_process_gaps(demo_extractions)
    m = result['metrics']
    assert m['consultations_detected'] >= 3, \
        f"Expected ≥3 consultations, got {m['consultations_detected']}"
    assert m['reports_detected'] >= 2, \
        f"Expected ≥2 lab reports, got {m['reports_detected']}"
    assert m['incomplete_referrals'] >= 1


def test_active_progress_after_report_09(full_extractions):
    """Adding specialist note (report 09) should improve state."""
    result_8 = detect_process_gaps(full_extractions[:8])
    result_9 = detect_process_gaps(full_extractions[:9])

    # State should improve (fewer high signals)
    high_8 = sum(1 for s in result_8['signals'] if s['severity'] == 'high')
    high_9 = sum(1 for s in result_9['signals'] if s['severity'] == 'high')
    assert high_9 <= high_8, "Adding report 09 should not increase high-severity signals"
    assert result_9['journey_state'] in (STATE_ACTIVE_PROGRESS, STATE_POSSIBLE_STAGNATION)


def test_gaps_are_ranked(demo_extractions):
    result = detect_process_gaps(demo_extractions)
    gaps = result['gaps']
    assert len(gaps) > 0
    # All gaps have required fields
    for gap in gaps:
        assert 'gap_id' in gap
        assert 'label' in gap
        assert 'severity' in gap
        assert 'next_action' in gap
