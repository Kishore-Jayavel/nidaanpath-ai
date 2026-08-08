"""
NidaanPath AI — app/services/timeline_builder.py
Builds a chronological diagnostic journey from confirmed extractions.
"""
from __future__ import annotations
from typing import List, Dict, Any
from datetime import datetime


EVENT_TYPE_MAP = {
    'consultation_note': 'Consultation',
    'lab_report': 'Test Result',
    'appointment_slip': 'Appointment',
    'prescription': 'Prescription',
    'referral_slip': 'Referral',
    'patient_narration': 'Patient Narration',
    'specialist_consultation_note': 'Specialist Consultation',
    'result_review_note': 'Result Review',
    'unknown': 'Document',
}

EVENT_ICON_MAP = {
    'Consultation': '🩺',
    'Test Result': '🧪',
    'Appointment': '📅',
    'Prescription': '💊',
    'Referral': '📋',
    'Patient Narration': '💬',
    'Specialist Consultation': '👨‍⚕️',
    'Result Review': '✅',
    'Document': '📄',
}

NODE_TYPE_MAP = {
    'consultation_note': 'consultation',
    'lab_report': 'test_result',
    'appointment_slip': 'followup',
    'prescription': 'prescription',
    'referral_slip': 'referral',
    'patient_narration': 'patient_voice',
    'specialist_consultation_note': 'specialist',
    'result_review_note': 'result_review',
}


def build_timeline(confirmed_extractions: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Convert confirmed document extractions into a chronological journey timeline.
    Returns nodes, edges, and ordered events for display.
    """
    events = []
    nodes = []
    edges = []

    # Sort by document date
    def parse_date(ex):
        date_str = ex.get('document_date') or '2099-12-31'
        try:
            return datetime.strptime(date_str[:10], '%Y-%m-%d')
        except Exception:
            return datetime.max

    sorted_extractions = sorted(confirmed_extractions, key=parse_date)

    prev_node_id = None
    for idx, ex in enumerate(sorted_extractions):
        doc_type = ex.get('document_type', 'unknown')
        event_type = EVENT_TYPE_MAP.get(doc_type, 'Document')
        node_type = NODE_TYPE_MAP.get(doc_type, 'document')
        node_id = f"node_{idx}"

        # Build event
        event = {
            'id': node_id,
            'index': idx,
            'date': ex.get('document_date', 'Unknown date'),
            'event_type': event_type,
            'icon': EVENT_ICON_MAP.get(event_type, '📄'),
            'provider': ex.get('provider', 'Unknown provider'),
            'document_id': ex.get('document_id', ''),
            'symptoms': ex.get('symptoms', []),
            'tests_ordered': ex.get('tests_ordered', []),
            'tests_completed': ex.get('tests_completed', []),
            'referrals': ex.get('referrals', []),
            'referral_specialty': ex.get('referral_specialty'),
            'medication_mentions': ex.get('medication_mentions', []),
            'follow_up_instructions': ex.get('follow_up_instructions'),
            'result_review_status': ex.get('result_review_status', 'unknown'),
            'treatment_response': ex.get('treatment_response'),
            'source_fragments': ex.get('source_fragments', []),
            'uncertain_fields': ex.get('uncertain_fields', []),
            'extraction_confidence': ex.get('extraction_confidence', 0.8),
            'confirmed': ex.get('_confirmed', True),
        }
        events.append(event)

        # Build graph node
        node = {
            'id': node_id,
            'label': f"{ex.get('document_date', '?')} — {event_type}",
            'type': node_type,
            'date': ex.get('document_date', ''),
            'provider': ex.get('provider', ''),
            'data': event,
        }
        nodes.append(node)

        # Add symptom nodes for repeated symptoms
        for symptom in ex.get('symptoms', []):
            s_node_id = f"symptom_{idx}_{symptom[:10].replace(' ', '_')}"
            nodes.append({
                'id': s_node_id,
                'label': symptom,
                'type': 'symptom',
                'date': ex.get('document_date', ''),
                'data': {'symptom': symptom},
            })
            edges.append({
                'source': node_id,
                'target': s_node_id,
                'label': 'reports',
                'type': 'symptom_link',
            })

        # Add referral nodes
        if ex.get('referral_specialty'):
            r_node_id = f"referral_{idx}"
            nodes.append({
                'id': r_node_id,
                'label': f"Referral: {ex['referral_specialty']}",
                'type': 'referral',
                'date': ex.get('document_date', ''),
                'data': {'specialty': ex['referral_specialty']},
            })
            edges.append({
                'source': node_id,
                'target': r_node_id,
                'label': 'refers to',
                'type': 'referral_link',
            })

        # Link sequential consultations
        if prev_node_id:
            edges.append({
                'source': prev_node_id,
                'target': node_id,
                'label': 'next',
                'type': 'timeline_link',
            })
        prev_node_id = node_id

    # Add gap nodes for unresolved issues
    gap_nodes = _add_gap_nodes(nodes, edges, sorted_extractions)

    return {
        'events': events,
        'nodes': nodes + gap_nodes,
        'edges': edges,
        'total_events': len(events),
    }


def _add_gap_nodes(
    nodes: list, edges: list, extractions: list
) -> List[Dict]:
    gap_nodes = []

    # Check for unreviewed results
    reviewed_docs = [ex for ex in extractions
                     if ex.get('result_review_status') == 'reviewed']
    if not reviewed_docs:
        for idx, ex in enumerate(extractions):
            if ex.get('tests_completed'):
                gap_id = f"gap_unreviewed_{idx}"
                gap_nodes.append({
                    'id': gap_id,
                    'label': '⚠ Unreviewed Result',
                    'type': 'process_gap',
                    'date': ex.get('document_date', ''),
                    'data': {'gap': 'Result not confirmed reviewed'},
                })
                edges.append({
                    'source': f"node_{idx}",
                    'target': gap_id,
                    'label': 'gap',
                    'type': 'gap_link',
                })
                break  # Add once

    return gap_nodes
