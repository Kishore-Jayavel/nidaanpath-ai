"""
NidaanPath AI — tests/test_timeline_builder.py
Tests for timeline construction.
"""
import pytest
from app.services.timeline_builder import build_timeline
from app.services.mock_ai_service import DEMO_EXTRACTIONS


def get_extractions(nums):
    return [{**DEMO_EXTRACTIONS[i], 'document_id': f'report_{i:02d}.pdf'} for i in nums]


def test_empty_extractions():
    result = build_timeline([])
    assert result['events'] == []
    assert result['total_events'] == 0


def test_chronological_order():
    exs = get_extractions([1, 2, 3, 4, 5, 6, 7, 8])
    result = build_timeline(exs)
    dates = [e['date'] for e in result['events'] if e['date'] and e['date'] != 'Unknown date']
    assert dates == sorted(dates), "Timeline events must be in chronological order"


def test_all_8_events_present():
    exs = get_extractions([1, 2, 3, 4, 5, 6, 7, 8])
    result = build_timeline(exs)
    assert result['total_events'] == 8


def test_out_of_order_reports():
    """Reports uploaded out of order must still produce chronological timeline."""
    exs = get_extractions([8, 3, 1, 5, 2])
    result = build_timeline(exs)
    dates = [e['date'] for e in result['events'] if e['date'] and e['date'] != 'Unknown date']
    assert dates == sorted(dates)


def test_each_event_has_required_fields():
    exs = get_extractions([1])
    result = build_timeline(exs)
    for event in result['events']:
        assert 'id' in event
        assert 'date' in event
        assert 'event_type' in event
        assert 'icon' in event
        assert 'provider' in event


def test_nodes_and_edges_generated():
    exs = get_extractions([1, 2, 6])
    result = build_timeline(exs)
    assert len(result['nodes']) >= 3
    # Edges connect sequential events
    timeline_edges = [e for e in result['edges'] if e['type'] == 'timeline_link']
    assert len(timeline_edges) >= 2


def test_referral_node_created():
    exs = get_extractions([6])  # ENT referral
    result = build_timeline(exs)
    referral_nodes = [n for n in result['nodes'] if n['type'] == 'referral']
    assert len(referral_nodes) >= 1


def test_specialist_event_type():
    exs = get_extractions([9])
    result = build_timeline(exs)
    event = result['events'][0]
    assert event['event_type'] == 'Specialist Consultation'
