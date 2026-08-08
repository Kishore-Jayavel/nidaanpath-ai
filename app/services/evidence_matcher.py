"""
NidaanPath AI — app/services/evidence_matcher.py
Matches newly uploaded documents to existing process gaps.
"""
from __future__ import annotations
from typing import List, Dict, Any, Optional


def match_new_evidence(
    new_extraction: Dict[str, Any],
    existing_gaps: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Attempt to match a new document extraction to open process gaps.
    Returns match results and list of resolved gap IDs.
    """
    resolved = []
    partial = []
    unmatched_gaps = []

    doc_type = new_extraction.get('document_type', '')
    referral_specialty = new_extraction.get('referral_specialty')
    review_status = new_extraction.get('result_review_status', 'unknown')
    tests_completed = new_extraction.get('tests_completed', [])
    medication_mentions = new_extraction.get('medication_mentions', [])

    for gap in existing_gaps:
        gap_id = gap.get('gap_id', '')
        resolved_this = False

        if gap_id == 'incomplete_referral':
            # Report 09: Specialist consultation closes referral gap
            if doc_type in ('specialist_consultation_note', 'consultation_note'):
                resolved.append({
                    'gap_id': gap_id,
                    'label': gap.get('label', ''),
                    'resolved_by': new_extraction.get('document_id', ''),
                    'resolution_note': (
                        f"Specialist consultation note from "
                        f"{new_extraction.get('provider', 'specialist')} "
                        f"matches the open referral."
                    ),
                })
                resolved_this = True

        elif gap_id == 'unreviewed_result':
            # Report 10: Result review note closes unreviewed gap
            if doc_type in ('result_review_note',) or review_status == 'reviewed':
                resolved.append({
                    'gap_id': gap_id,
                    'label': gap.get('label', ''),
                    'resolved_by': new_extraction.get('document_id', ''),
                    'resolution_note': 'Laboratory results confirmed as reviewed by clinician.',
                })
                resolved_this = True

        elif gap_id == 'missed_followup':
            if doc_type in ('consultation_note', 'specialist_consultation_note',
                            'result_review_note', 'prescription'):
                resolved.append({
                    'gap_id': gap_id,
                    'label': gap.get('label', ''),
                    'resolved_by': new_extraction.get('document_id', ''),
                    'resolution_note': 'Follow-up visit documented.',
                })
                resolved_this = True

        elif gap_id == 'record_contradiction':
            # Only a clinician can resolve medication contradiction
            partial.append({
                'gap_id': gap_id,
                'label': gap.get('label', ''),
                'note': (
                    'Medication conflict remains. '
                    'Clinician confirmation required. '
                    'This gap cannot be auto-resolved by NidaanPath.'
                ),
                'requires_clinician': True,
            })
            resolved_this = True  # Remove from active gaps (escalated)

        if not resolved_this:
            unmatched_gaps.append(gap)

    return {
        'resolved_gaps': resolved,
        'partial_matches': partial,
        'remaining_gaps': unmatched_gaps,
        'match_count': len(resolved),
    }


def select_next_evidence_question(
    remaining_gaps: List[Dict[str, Any]],
    already_asked: List[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Safety-bounded next-best-evidence selection.
    Returns the single highest-priority question.
    The agent may NOT ask questions that could diagnose, prescribe or predict.
    """
    already_asked = already_asked or []

    # Priority order of gap types
    priority = [
        'incomplete_referral',
        'unreviewed_result',
        'missing_treatment_response',
        'missed_followup',
        'no_documented_next_step',
        'repeated_symptom',
        'record_contradiction',
    ]

    # Questions for each gap type (process-focused only)
    questions = {
        'incomplete_referral': {
            'question_en': (
                'Did you complete the ENT specialist consultation? '
                'If yes, do you have the specialist\'s consultation note or report?'
            ),
            'question_ta': (
                'நீங்கள் ENT நிபுணர் ஆலோசனையை முடித்தீர்களா? '
                'ஆம் எனில், நிபுணரின் குறிப்பு அல்லது அறிக்கை உங்களிடம் உள்ளதா?'
            ),
            'upload_hint': 'Upload the ENT specialist consultation note (PDF or image)',
            'safety_cleared': True,
        },
        'unreviewed_result': {
            'question_en': (
                'Was your CBC blood report and fasting glucose report reviewed '
                'by a doctor? Do you have any written notes or consultation '
                'records from that review?'
            ),
            'question_ta': (
                'உங்கள் CBC இரத்த அறிக்கை மற்றும் உண்ணாவிரத குளூக்கோஸ் அறிக்கை '
                'மருத்துவரால் மதிப்பாய்வு செய்யப்பட்டதா?'
            ),
            'upload_hint': 'Upload any result review note or consultation note mentioning the reports',
            'safety_cleared': True,
        },
        'missing_treatment_response': {
            'question_en': (
                'Did the dizziness improve, stay the same, or worsen '
                'after starting the medication? '
                'Please describe what you noticed.'
            ),
            'question_ta': (
                'மருந்து சாப்பிட்ட பிறகு மயக்கம் குறைந்ததா, அப்படியே இருந்ததா, '
                'அல்லது அதிகமானதா?'
            ),
            'upload_hint': None,
            'safety_cleared': True,
        },
        'missed_followup': {
            'question_en': (
                'Was the recommended 7-day follow-up visit completed? '
                'If so, do you have any record or slip from that visit?'
            ),
            'question_ta': (
                'பரிந்துரைக்கப்பட்ட 7 நாள் மறுவருகை பரிசோதனை முடிந்ததா?'
            ),
            'upload_hint': 'Upload any appointment slip or consultation note from the follow-up',
            'safety_cleared': True,
        },
        'no_documented_next_step': {
            'question_en': (
                'After your most recent consultation, were you given any instructions '
                'or a plan for what should happen next in your care?'
            ),
            'question_ta': (
                'கடைசி ஆலோசனைக்கு பிறகு, அடுத்தது என்ன செய்ய வேண்டும் என்று '
                'மருத்துவர் சொன்னார்களா?'
            ),
            'upload_hint': None,
            'safety_cleared': True,
        },
        'repeated_symptom': {
            'question_en': (
                'The dizziness appears in multiple records. Has it changed in character '
                'or severity since you first saw a doctor for it? '
                'Do you have any recent record documenting this?'
            ),
            'question_ta': (
                'மயக்கம் பல பதிவுகளில் தெரிகிறது. முதலில் மருத்துவரிடம் சென்றதில் இருந்து '
                'அது மாறியுள்ளதா?'
            ),
            'upload_hint': None,
            'safety_cleared': True,
        },
        'record_contradiction': {
            'question_en': (
                'Two different medications have been prescribed across your records. '
                'Can you confirm which one you are currently taking? '
                'This will be escalated to your clinician — NidaanPath cannot resolve this.'
            ),
            'question_ta': (
                'உங்கள் பதிவுகளில் இரண்டு வெவ்வேறு மருந்துகள் பரிந்துரைக்கப்பட்டுள்ளன. '
                'தற்போது எதை சாப்பிடுகிறீர்கள்? இது மருத்துவரிடம் அனுப்பப்படும்.'
            ),
            'upload_hint': None,
            'safety_cleared': True,
            'escalate': True,
        },
    }

    for gap_type in priority:
        # Find gap in remaining list
        matching_gap = next(
            (g for g in remaining_gaps if g.get('gap_id') == gap_type),
            None
        )
        if matching_gap and gap_type not in already_asked:
            q = questions.get(gap_type, {})
            return {
                'gap_id': gap_type,
                'gap_label': matching_gap.get('label', ''),
                'question_en': q.get('question_en', ''),
                'question_ta': q.get('question_ta', ''),
                'upload_hint': q.get('upload_hint'),
                'safety_cleared': q.get('safety_cleared', True),
                'escalate': q.get('escalate', False),
            }

    return None  # All gaps addressed
