"""
NidaanPath AI — app/services/stagnation_engine.py
SAFETY GATE 2: Deterministic Python-only stagnation detection.
Gemini never determines journey state — only these transparent rules do.
"""
from __future__ import annotations
from typing import List, Dict, Any
from dataclasses import dataclass, field


@dataclass
class StagnationSignal:
    signal_type: str          # repeated_symptom, unreviewed_result, etc.
    description: str
    severity: str             # high, medium, low
    source_documents: List[str] = field(default_factory=list)
    is_active: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            'signal_type': self.signal_type,
            'description': self.description,
            'severity': self.severity,
            'source_documents': self.source_documents,
            'is_active': self.is_active,
        }


# Journey state constants
STATE_AWAITING_EVIDENCE = "Awaiting Evidence"
STATE_ACTIVE_PROGRESS = "Active Progress"
STATE_POSSIBLE_STAGNATION = "Possible Stagnation"
STATE_CLARIFICATION_REQUIRED = "Clarification Required"
STATE_CLINICIAN_ESCALATION = "Clinician Escalation Required"
STATE_DIAGNOSTIC_CLOSURE = "Diagnostic Closure Documented"


def detect_process_gaps(extractions: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    DETERMINISTIC stagnation detection from extracted document data.
    Gemini has no role in this function — pure Python rule evaluation.

    Returns:
        {
            'signals': [StagnationSignal, ...],
            'journey_state': str,
            'metrics': {...},
            'gaps': [...],
        }
    """
    if not extractions:
        return {
            'signals': [],
            'journey_state': STATE_AWAITING_EVIDENCE,
            'metrics': _empty_metrics(),
            'gaps': [],
        }

    signals: List[StagnationSignal] = []

    # ── Rule 1: repeated_symptom ─────────────────────────────────────────────
    # True when same/equivalent symptom appears in ≥ 3 encounters
    symptom_encounters: Dict[str, int] = {}
    for ex in extractions:
        for symptom in ex.get('symptoms', []):
            key = _normalise_symptom(symptom)
            symptom_encounters[key] = symptom_encounters.get(key, 0) + 1

    repeated = [s for s, count in symptom_encounters.items() if count >= 3]
    if repeated:
        signals.append(StagnationSignal(
            signal_type='repeated_symptom',
            description=(
                f"Symptom(s) '{', '.join(repeated)}' detected across "
                f"{max(symptom_encounters[s] for s in repeated)} encounters "
                f"without documented resolution."
            ),
            severity='high',
            source_documents=[ex.get('document_id', '') for ex in extractions
                               if any(_normalise_symptom(s) in repeated
                                      for s in ex.get('symptoms', []))],
        ))

    # ── Rule 2: unreviewed_result ────────────────────────────────────────────
    # True when a report exists but no later review evidence is found
    reports_completed = []
    reviews_documented = []
    for ex in extractions:
        for r in ex.get('tests_completed', []):
            reports_completed.append(r)
        if ex.get('result_review_status') == 'reviewed':
            for r in ex.get('reports_available', []):
                reviews_documented.append(r)

    unreviewed = [r for r in reports_completed
                  if not any(_fuzzy_match(r, rev) for rev in reviews_documented)]
    if unreviewed:
        signals.append(StagnationSignal(
            signal_type='unreviewed_result',
            description=(
                f"{len(unreviewed)} test result(s) completed but no documented "
                f"review found: {', '.join(unreviewed[:3])}"
            ),
            severity='high',
            source_documents=[ex.get('document_id', '') for ex in extractions
                               if ex.get('result_review_status') == 'not_reviewed'],
        ))

    # ── Rule 3: incomplete_referral ──────────────────────────────────────────
    # True when a referral exists but no matching specialist consultation
    referral_specialties = []
    specialist_consultations = []
    for ex in extractions:
        sp = ex.get('referral_specialty')
        if sp:
            referral_specialties.append(sp)
        if ex.get('document_type') == 'specialist_consultation_note':
            specialist_consultations.append(ex.get('document_id', ''))

    open_referrals = len(referral_specialties) - len(specialist_consultations)
    if open_referrals > 0:
        signals.append(StagnationSignal(
            signal_type='incomplete_referral',
            description=(
                f"Referral to {', '.join(referral_specialties)} issued but "
                f"no specialist consultation record found."
            ),
            severity='high',
            source_documents=[ex.get('document_id', '') for ex in extractions
                               if ex.get('referral_specialty')],
        ))

    # ── Rule 4: missing_treatment_response ──────────────────────────────────
    # True when medication changes but response not documented
    has_medication_change = False
    has_treatment_response = False
    medications_seen = set()
    for ex in extractions:
        for med in ex.get('medication_mentions', []):
            medications_seen.add(_normalise_symptom(med))
        if ex.get('treatment_response'):
            has_treatment_response = True

    if len(medications_seen) > 1 and not has_treatment_response:
        signals.append(StagnationSignal(
            signal_type='missing_treatment_response',
            description=(
                f"Multiple medications mentioned ({len(medications_seen)}) "
                f"but treatment response not documented."
            ),
            severity='medium',
            source_documents=[ex.get('document_id', '') for ex in extractions
                               if ex.get('medication_mentions')],
        ))

    # ── Rule 5: missed_followup ──────────────────────────────────────────────
    # True when a follow-up was advised but no corresponding visit found
    followup_advised = sum(
        1 for ex in extractions
        if ex.get('follow_up_instructions') and 'review' in
        (ex.get('follow_up_instructions') or '').lower()
    )
    consultations_total = sum(
        1 for ex in extractions
        if ex.get('document_type') in ('consultation_note', 'specialist_consultation_note',
                                        'prescription', 'result_review_note')
    )
    # If more follow-ups advised than consultations minus the first one
    if followup_advised >= 2 and consultations_total <= followup_advised:
        signals.append(StagnationSignal(
            signal_type='missed_followup',
            description=(
                f"Follow-up visits advised in {followup_advised} records "
                f"but only {consultations_total} consultation(s) found."
            ),
            severity='medium',
            source_documents=[ex.get('document_id', '') for ex in extractions
                               if ex.get('follow_up_instructions')],
        ))

    # ── Rule 6: no_documented_next_step ─────────────────────────────────────
    # True when latest consultation has persistent symptoms but no clear action
    if extractions:
        latest = extractions[-1]
        has_symptoms = bool(latest.get('symptoms'))
        no_next_step = not latest.get('follow_up_instructions') and \
                       not latest.get('referral_specialty') and \
                       not latest.get('diagnostic_closure_documented')
        if has_symptoms and no_next_step:
            signals.append(StagnationSignal(
                signal_type='no_documented_next_step',
                description=(
                    "Latest record shows persistent symptoms but no clearly "
                    "documented next diagnostic or follow-up action."
                ),
                severity='high',
                source_documents=[latest.get('document_id', '')],
            ))

    # ── Rule 7: record_contradiction ────────────────────────────────────────
    # True when contradictory medication instructions found
    med_list = []
    for ex in extractions:
        for med in ex.get('medication_mentions', []):
            med_list.append((ex.get('document_id', ''), med))

    # Detect potentially conflicting meds (same drug class, different doses/stops)
    uncertain_meds = [ex for ex in extractions if 'medication' in ex.get('uncertain_fields', [])]
    if len(med_list) > 2:  # simplified contradiction detection
        # Check if any extraction explicitly flags medication uncertainty
        med_uncertain = [
            ex for ex in extractions
            if any('medication' in f.lower() or 'betahistine' in f.lower() or
                   'stugeron' in f.lower()
                   for f in ex.get('uncertain_fields', []))
        ]
        if med_uncertain:
            signals.append(StagnationSignal(
                signal_type='record_contradiction',
                description=(
                    "Potentially conflicting medication instructions detected across records. "
                    "Clinician review required to confirm current medication."
                ),
                severity='high',
                source_documents=[ex.get('document_id', '') for ex in med_uncertain],
            ))

    # ── Compute journey state ────────────────────────────────────────────────
    journey_state = _compute_journey_state(signals, extractions)

    # ── Build gap list ───────────────────────────────────────────────────────
    gaps = _build_gap_list(signals, extractions)

    # ── Metrics ─────────────────────────────────────────────────────────────
    metrics = _compute_metrics(extractions, signals, unreviewed, open_referrals)

    return {
        'signals': [s.to_dict() for s in signals],
        'journey_state': journey_state,
        'metrics': metrics,
        'gaps': gaps,
    }


def _compute_journey_state(
    signals: List[StagnationSignal],
    extractions: List[Dict[str, Any]]
) -> str:
    if not extractions:
        return STATE_AWAITING_EVIDENCE

    high_signals = [s for s in signals if s.severity == 'high' and s.is_active]
    medium_signals = [s for s in signals if s.severity == 'medium' and s.is_active]

    # Check for diagnostic closure
    if any(ex.get('diagnostic_closure_documented') for ex in extractions):
        return STATE_DIAGNOSTIC_CLOSURE

    # Check for clinician escalation requirement
    if any(s.signal_type == 'record_contradiction' for s in signals):
        pass  # escalation required but still compute below

    # Three or more high signals → Possible Stagnation
    if len(high_signals) >= 3:
        return STATE_POSSIBLE_STAGNATION

    # One or two high signals → Clarification Required or Active Progress
    if len(high_signals) >= 1:
        # Check if latest doc shows progress (specialist note added recently)
        latest_type = extractions[-1].get('document_type', '') if extractions else ''
        if latest_type in ('specialist_consultation_note', 'result_review_note'):
            return STATE_ACTIVE_PROGRESS
        return STATE_CLARIFICATION_REQUIRED

    # Only medium signals
    if medium_signals:
        return STATE_AWAITING_EVIDENCE

    return STATE_ACTIVE_PROGRESS


def _build_gap_list(
    signals: List[StagnationSignal],
    extractions: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    gaps = []
    priority_map = {
        'incomplete_referral': 1,
        'unreviewed_result': 2,
        'missing_treatment_response': 3,
        'record_contradiction': 4,
        'missed_followup': 5,
        'repeated_symptom': 6,
        'no_documented_next_step': 7,
    }
    signal_labels = {
        'incomplete_referral': 'Incomplete Referral',
        'unreviewed_result': 'Unreviewed Test Result',
        'missing_treatment_response': 'Missing Treatment Response',
        'record_contradiction': 'Medication Contradiction',
        'missed_followup': 'Missed Follow-Up',
        'repeated_symptom': 'Repeated Symptom (Unresolved)',
        'no_documented_next_step': 'No Documented Next Step',
    }
    for sig in sorted(signals, key=lambda s: priority_map.get(s.signal_type, 99)):
        gaps.append({
            'gap_id': sig.signal_type,
            'label': signal_labels.get(sig.signal_type, sig.signal_type),
            'description': sig.description,
            'severity': sig.severity,
            'status': 'open',
            'source_documents': sig.source_documents,
            'next_action': _gap_next_action(sig.signal_type),
        })
    return gaps


def _gap_next_action(signal_type: str) -> str:
    actions = {
        'incomplete_referral': 'Provide specialist consultation record',
        'unreviewed_result': 'Confirm test result was reviewed by clinician',
        'missing_treatment_response': 'Document patient response to treatment',
        'record_contradiction': 'Clinician to confirm which medication is current',
        'missed_followup': 'Confirm follow-up visit took place',
        'repeated_symptom': 'Document resolution or new diagnostic direction',
        'no_documented_next_step': 'Record planned next diagnostic step',
    }
    return actions.get(signal_type, 'Review and update record')


def _compute_metrics(
    extractions: List[Dict[str, Any]],
    signals: List[StagnationSignal],
    unreviewed: List[str],
    open_referrals: int,
) -> Dict[str, Any]:
    consultations = sum(
        1 for ex in extractions
        if ex.get('document_type') in (
            'consultation_note', 'specialist_consultation_note',
            'prescription', 'result_review_note'
        )
    )
    reports = sum(
        1 for ex in extractions
        if ex.get('document_type') in ('lab_report',)
    )
    referrals = sum(
        1 for ex in extractions
        if ex.get('referral_specialty')
    )
    specialist_notes = sum(
        1 for ex in extractions
        if ex.get('document_type') == 'specialist_consultation_note'
    )
    has_persistent_symptom = any(
        s.signal_type == 'repeated_symptom' for s in signals
    )
    med_uncertainty = any(
        s.signal_type == 'record_contradiction' for s in signals
    )
    missed_followup = any(
        s.signal_type == 'missed_followup' for s in signals
    )

    return {
        'consultations_detected': consultations,
        'reports_detected': reports,
        'persistent_symptom': has_persistent_symptom,
        'unreviewed_results': len(unreviewed),
        'incomplete_referrals': max(0, referrals - specialist_notes),
        'missed_followup': missed_followup,
        'medication_uncertainty': med_uncertainty,
        'total_documents': len(extractions),
        'total_gaps': sum(1 for s in signals if s.is_active),
    }


def _empty_metrics() -> Dict[str, Any]:
    return {
        'consultations_detected': 0,
        'reports_detected': 0,
        'persistent_symptom': False,
        'unreviewed_results': 0,
        'incomplete_referrals': 0,
        'missed_followup': False,
        'medication_uncertainty': False,
        'total_documents': 0,
        'total_gaps': 0,
    }


def _normalise_symptom(s: str) -> str:
    return s.lower().strip().replace('persistent ', '').replace('ongoing ', '')


def _fuzzy_match(a: str, b: str, threshold: int = 70) -> bool:
    try:
        from rapidfuzz import fuzz
        return fuzz.partial_ratio(a.lower(), b.lower()) >= threshold
    except ImportError:
        return a.lower() in b.lower() or b.lower() in a.lower()
