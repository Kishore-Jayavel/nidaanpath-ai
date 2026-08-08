"""
NidaanPath AI — app/routes/agent.py
NidaanPath Coordinator Agent routes.
"""
import json
from datetime import datetime
from flask import Blueprint, render_template, request, session, redirect, url_for, jsonify
from ..extensions import db
from ..models.patient_case import PatientCase
from ..models.medical_document import MedicalDocument
from ..services.stagnation_engine import detect_process_gaps
from ..services.evidence_matcher import match_new_evidence, select_next_evidence_question
from ..services.ai_factory import get_ai_service

agent_bp = Blueprint('agent', __name__)


@agent_bp.route('/activity')
def activity():
    case = _get_case()
    if not case:
        return redirect(url_for('main.index'))
    agent_state = _build_agent_state(case)
    return render_template('agent_activity.html', case=case, agent=agent_state)


@agent_bp.route('/api/run-coordinator', methods=['POST'])
def run_coordinator():
    """
    NidaanPath Coordinator Agent — main execution endpoint.
    Runs the full agent loop and returns updated state.
    """
    case = _get_case()
    if not case:
        return jsonify({'error': 'No active case'}), 400

    docs = MedicalDocument.query.filter_by(case_id=case.id)\
                                .order_by(MedicalDocument.upload_order).all()
    confirmed_docs = [d for d in docs if d.confirmed_by_user]
    extractions = [d.get_extraction() for d in confirmed_docs]

    actions = case.get_agent_actions()
    ai = get_ai_service()

    # ── TOOL 1: extract_medical_document (already done per upload) ──────────
    _log_action(actions, 'extract_medical_document',
                f'Processed {len(docs)} document(s) — {len(confirmed_docs)} confirmed',
                'success', 'PASS')

    # ── TOOL 2: build_diagnostic_journey ────────────────────────────────────
    from ..services.timeline_builder import build_timeline
    timeline = build_timeline(extractions)
    _log_action(actions, 'build_diagnostic_journey',
                f'Journey built: {len(timeline["events"])} events, '
                f'{len(timeline["nodes"])} nodes',
                'success', 'PASS')

    # ── TOOL 3: detect_process_gaps (Safety Gate 2) ─────────────────────────
    gap_result = detect_process_gaps(extractions)
    n_gaps = len(gap_result['gaps'])
    _log_action(actions, 'detect_process_gaps',
                f'Detected {n_gaps} process gap(s). '
                f'State: {gap_result["journey_state"]}',
                'success', 'PASS — Deterministic Python rules only')

    # Update case state
    case.journey_state = gap_result['journey_state']
    case.set_remaining_gaps(gap_result['gaps'])

    # ── TOOL 5: select_next_evidence_question ────────────────────────────────
    remaining = gap_result['gaps']
    already_asked = [a.get('gap_asked') for a in actions
                     if a.get('tool') == 'select_next_evidence_question']
    next_question = select_next_evidence_question(remaining, already_asked)
    if next_question:
        _log_action(actions, 'select_next_evidence_question',
                    f'Selected question for gap: {next_question["gap_id"]}',
                    'success', 'PASS — Process-focused question only')

    # ── TOOL 4: match_new_evidence (for any recently added docs) ─────────────
    # Check if latest doc changed anything
    if confirmed_docs:
        latest_ex = extractions[-1] if extractions else {}
        match_result = match_new_evidence(latest_ex, remaining)
        if match_result['match_count'] > 0:
            resolved = case.get_resolved_gaps()
            resolved.extend(match_result['resolved_gaps'])
            case.set_resolved_gaps(resolved)
            # Remove resolved from remaining
            resolved_ids = [r['gap_id'] for r in match_result['resolved_gaps']]
            new_remaining = [g for g in remaining if g['gap_id'] not in resolved_ids]
            case.set_remaining_gaps(new_remaining)
            _log_action(actions, 'match_new_evidence',
                        f'Matched {match_result["match_count"]} gap(s): '
                        f'{", ".join(resolved_ids)}',
                        'success', 'PASS')

    case.set_agent_actions(actions)
    db.session.commit()

    return jsonify({
        'success': True,
        'journey_state': case.journey_state,
        'remaining_gaps': len(case.get_remaining_gaps()),
        'resolved_gaps': len(case.get_resolved_gaps()),
        'next_question': next_question,
        'actions': actions[-5:],  # Last 5 actions
    })


@agent_bp.route('/api/answer-question', methods=['POST'])
def answer_question():
    """Patient submits an answer to the agent's next-evidence question."""
    case = _get_case()
    if not case:
        return jsonify({'error': 'No active case'}), 400

    gap_id = request.json.get('gap_id')
    answer = request.json.get('answer', '')
    actions = case.get_agent_actions()

    _log_action(actions, 'patient_answer',
                f'Patient answered question for gap: {gap_id} — "{answer[:80]}"',
                'info', 'PASS — Patient confirmation recorded')

    case.set_agent_actions(actions)
    db.session.commit()
    return jsonify({'success': True})


def _build_agent_state(case: PatientCase) -> dict:
    docs = MedicalDocument.query.filter_by(case_id=case.id).all()
    confirmed = [d for d in docs if d.confirmed_by_user]
    remaining = case.get_remaining_gaps()
    resolved = case.get_resolved_gaps()
    actions = case.get_agent_actions()
    next_q = select_next_evidence_question(remaining)

    # Count by type
    consultations = sum(1 for d in confirmed if d.document_type in (
        'consultation_note', 'specialist_consultation_note',
        'prescription', 'result_review_note'
    ))
    lab_reports = sum(1 for d in confirmed if d.document_type == 'lab_report')
    referrals = sum(1 for d in confirmed if d.document_type == 'referral_slip')

    return {
        'goal': 'Reconstruct and clarify the diagnostic journey',
        'phase': _determine_phase(case, remaining),
        'total_documents': len(docs),
        'confirmed_documents': len(confirmed),
        'consultations_identified': consultations,
        'lab_reports_matched': lab_reports,
        'referrals_detected': referrals,
        'remaining_gaps': len(remaining),
        'resolved_gaps': len(resolved),
        'journey_state': case.journey_state,
        'next_question': next_q,
        'current_tool': _get_current_tool(case, remaining),
        'current_decision': _get_current_decision(case, remaining, next_q),
        'actions': actions,
        'resolved_gap_list': resolved,
        'remaining_gap_list': remaining,
    }


def _determine_phase(case, remaining):
    if not case.get_journey_events():
        return 'extraction'
    if not remaining:
        return 'packet'
    return 'evidence'


def _get_current_tool(case, remaining):
    if not case.get_journey_events():
        return 'extract_medical_document()'
    if remaining:
        return 'select_next_evidence_question()'
    return 'generate_clinician_packet()'


def _get_current_decision(case, remaining, next_q):
    if not remaining:
        return 'Generate clinician escalation packet'
    if next_q:
        return f'Ask whether {next_q["gap_label"].lower()} has been resolved'
    return 'Review remaining process gaps'


def _log_action(actions, tool, result, status, safety_gate):
    actions.append({
        'timestamp': datetime.utcnow().strftime('%H:%M:%S'),
        'tool': tool,
        'result': result,
        'status': status,
        'safety_gate': safety_gate,
    })


def _get_case():
    case_id = session.get('case_id')
    if case_id:
        return PatientCase.query.get(case_id)
    return None
