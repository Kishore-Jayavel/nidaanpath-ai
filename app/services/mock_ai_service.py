"""
NidaanPath AI — app/services/mock_ai_service.py
Deterministic mock AI that works without an API key.
Returns realistic, dataset-driven extraction results.
"""
from __future__ import annotations
from typing import Dict, Any
from ..models.schemas import MedicalDocumentExtraction, PatientNarrationExtraction, ExtractedFinding

# Ground-truth extraction data keyed by demo report number
DEMO_EXTRACTIONS: Dict[int, Dict[str, Any]] = {
    1: {
        "document_type": "consultation_note",
        "document_date": "2024-06-03",
        "provider": "Dr. Meena Krishnan, MBBS — City Medical Centre",
        "symptoms": ["Persistent dizziness", "Mild nausea", "Occasional headache"],
        "symptom_duration": "Approximately 3–4 weeks",
        "tests_ordered": ["Complete Blood Count (CBC)", "Fasting blood glucose"],
        "tests_completed": [],
        "reports_available": [],
        "referrals": [],
        "referral_specialty": None,
        "medication_mentions": ["Tab. Betahistine 16mg twice daily for 10 days"],
        "treatment_response": None,
        "follow_up_instructions": "Review after 7 days with CBC report",
        "result_review_status": "unknown",
        "diagnostic_closure_documented": False,
        "source_fragments": [
            "Patient presents with complaints of dizziness for 3-4 weeks",
            "Advised CBC and fasting blood glucose",
            "Tab. Betahistine 16mg BD x 10 days",
            "Review after 7 days with reports"
        ],
        "uncertain_fields": ["exact onset date"],
        "extraction_confidence": 0.93,
    },
    2: {
        "document_type": "lab_report",
        "document_date": "2024-06-05",
        "provider": "LifeCare Diagnostics",
        "symptoms": [],
        "symptom_duration": None,
        "tests_ordered": [],
        "tests_completed": ["Complete Blood Count (CBC)"],
        "reports_available": ["CBC Report — 05 June 2024"],
        "referrals": [],
        "referral_specialty": None,
        "medication_mentions": [],
        "treatment_response": None,
        "follow_up_instructions": None,
        "result_review_status": "not_reviewed",
        "diagnostic_closure_documented": False,
        "source_fragments": [
            "Haemoglobin: 11.2 g/dL (Low)",
            "WBC: 7800/μL (Normal)",
            "Platelets: 182000/μL (Normal)",
            "Referred by: Dr. Meena Krishnan"
        ],
        "uncertain_fields": ["clinical interpretation not documented"],
        "extraction_confidence": 0.97,
    },
    3: {
        "document_type": "appointment_slip",
        "document_date": "2024-06-10",
        "provider": "City Medical Centre",
        "symptoms": [],
        "symptom_duration": None,
        "tests_ordered": [],
        "tests_completed": [],
        "reports_available": [],
        "referrals": [],
        "referral_specialty": None,
        "medication_mentions": [],
        "treatment_response": None,
        "follow_up_instructions": "Follow-up appointment — 10 June 2024 at 10:00 AM",
        "result_review_status": "unknown",
        "diagnostic_closure_documented": False,
        "source_fragments": [
            "Follow-up scheduled for 10 June 2024",
            "Bring CBC and glucose reports"
        ],
        "uncertain_fields": ["attendance not confirmed"],
        "extraction_confidence": 0.88,
    },
    4: {
        "document_type": "prescription",
        "document_date": "2024-06-18",
        "provider": "Dr. Suresh Nair, MD — Apollo Outpatient",
        "symptoms": ["Ongoing dizziness", "Fatigue"],
        "symptom_duration": "6 weeks",
        "tests_ordered": [],
        "tests_completed": [],
        "reports_available": [],
        "referrals": [],
        "referral_specialty": None,
        "medication_mentions": [
            "Tab. Stugeron 25mg thrice daily",
            "Cap. Iron + Folic Acid once daily"
        ],
        "treatment_response": None,
        "follow_up_instructions": "Review in 2 weeks",
        "result_review_status": "unknown",
        "diagnostic_closure_documented": False,
        "source_fragments": [
            "Patient complains of persistent dizziness for 6 weeks",
            "Tab. Stugeron 25mg TID",
            "Cap. Iron + Folic Acid OD",
            "Review after 2 weeks"
        ],
        "uncertain_fields": ["previous Betahistine status unclear", "CBC review not mentioned"],
        "extraction_confidence": 0.89,
    },
    5: {
        "document_type": "lab_report",
        "document_date": "2024-06-20",
        "provider": "LifeCare Diagnostics",
        "symptoms": [],
        "symptom_duration": None,
        "tests_ordered": [],
        "tests_completed": ["Fasting Blood Glucose"],
        "reports_available": ["Fasting Glucose Report — 20 June 2024"],
        "referrals": [],
        "referral_specialty": None,
        "medication_mentions": [],
        "treatment_response": None,
        "follow_up_instructions": None,
        "result_review_status": "not_reviewed",
        "diagnostic_closure_documented": False,
        "source_fragments": [
            "Fasting Blood Glucose: 118 mg/dL (Borderline)",
            "Normal range: 70–99 mg/dL"
        ],
        "uncertain_fields": ["clinical interpretation not documented"],
        "extraction_confidence": 0.96,
    },
    6: {
        "document_type": "referral_slip",
        "document_date": "2024-06-27",
        "provider": "Dr. Suresh Nair, MD — Apollo Outpatient",
        "symptoms": ["Persistent dizziness unresponsive to treatment"],
        "symptom_duration": "7 weeks",
        "tests_ordered": [],
        "tests_completed": [],
        "reports_available": [],
        "referrals": ["ENT Specialist"],
        "referral_specialty": "ENT (Ear, Nose and Throat)",
        "medication_mentions": [],
        "treatment_response": None,
        "follow_up_instructions": "Consult ENT for audiometry and vestibular evaluation",
        "result_review_status": "unknown",
        "diagnostic_closure_documented": False,
        "source_fragments": [
            "Referred to ENT for persistent dizziness",
            "Please evaluate for vestibular cause",
            "Audiometry recommended"
        ],
        "uncertain_fields": ["ENT appointment date not specified"],
        "extraction_confidence": 0.91,
    },
    7: {
        "document_type": "patient_narration",
        "document_date": "2024-07-05",
        "provider": "Self — Patient (Arun Kumar)",
        "symptoms": ["Dizziness", "Uncertainty about medications"],
        "symptom_duration": "About 1 month",
        "tests_ordered": [],
        "tests_completed": [],
        "reports_available": [],
        "referrals": [],
        "referral_specialty": None,
        "medication_mentions": [
            "Betahistine (first doctor)",
            "Stugeron (second doctor)"
        ],
        "treatment_response": "Partial improvement from Betahistine but dizziness returned",
        "follow_up_instructions": None,
        "result_review_status": "unknown",
        "diagnostic_closure_documented": False,
        "source_fragments": [
            "I'm not sure if the blood reports were reviewed",
            "First doctor gave Betahistine, second gave Stugeron",
            "I went to ENT but couldn't get an appointment yet"
        ],
        "uncertain_fields": [
            "which medication to continue",
            "ENT appointment status",
            "CBC review status"
        ],
        "extraction_confidence": 0.75,
    },
    8: {
        "document_type": "consultation_note",
        "document_date": "2024-07-10",
        "provider": "Dr. Meena Krishnan, MBBS — City Medical Centre",
        "symptoms": ["Persistent dizziness", "Fatigue"],
        "symptom_duration": "6–7 weeks",
        "tests_ordered": [],
        "tests_completed": [],
        "reports_available": [],
        "referrals": [],
        "referral_specialty": None,
        "medication_mentions": ["Continue current medication"],
        "treatment_response": "Minimal improvement noted",
        "follow_up_instructions": "Await ENT consultation result",
        "result_review_status": "unknown",
        "diagnostic_closure_documented": False,
        "source_fragments": [
            "Patient returns with persistent dizziness",
            "Minimal improvement on current treatment",
            "ENT referral pending",
            "No clear next diagnostic step documented"
        ],
        "uncertain_fields": [
            "CBC and glucose reports not mentioned as reviewed",
            "No clear next step documented"
        ],
        "extraction_confidence": 0.87,
    },
    9: {
        "document_type": "specialist_consultation_note",
        "document_date": "2024-07-15",
        "provider": "Dr. Priya Ramesh, MS (ENT) — ENT Care Hospital",
        "symptoms": ["Dizziness", "Tinnitus (mild)"],
        "symptom_duration": "2 months",
        "tests_ordered": ["Audiometry", "Caloric test"],
        "tests_completed": ["Audiometry"],
        "reports_available": ["Audiometry — within normal limits"],
        "referrals": [],
        "referral_specialty": None,
        "medication_mentions": [
            "Tab. Betahistine 16mg twice daily (reinstated)"
        ],
        "treatment_response": None,
        "follow_up_instructions": "Review in 3 weeks. Caloric test pending.",
        "result_review_status": "reviewed",
        "diagnostic_closure_documented": False,
        "source_fragments": [
            "Referred by Dr. Suresh Nair for evaluation of dizziness",
            "Audiometry: within normal limits",
            "Impression: Possible vestibular migraine vs. BPPV",
            "Reinstated Betahistine 16mg BD",
            "Review after 3 weeks"
        ],
        "uncertain_fields": ["Caloric test pending", "Vestibular migraine vs BPPV not confirmed"],
        "extraction_confidence": 0.94,
    },
    10: {
        "document_type": "result_review_note",
        "document_date": "2024-07-22",
        "provider": "Dr. Meena Krishnan, MBBS — City Medical Centre",
        "symptoms": ["Improving dizziness"],
        "symptom_duration": "2 months (improving)",
        "tests_ordered": [],
        "tests_completed": [],
        "reports_available": [],
        "referrals": [],
        "referral_specialty": None,
        "medication_mentions": ["Continue Betahistine per ENT advice"],
        "treatment_response": "Gradual improvement noted after reinstatement of Betahistine",
        "follow_up_instructions": "Continue ENT follow-up. Repeat fasting glucose in 3 months.",
        "result_review_status": "reviewed",
        "diagnostic_closure_documented": False,
        "source_fragments": [
            "CBC reviewed: Mild anaemia — Iron supplementation ongoing",
            "Fasting glucose: Borderline — lifestyle advice given",
            "ENT report reviewed",
            "Betahistine confirmed by ENT — continue",
            "Earlier Stugeron prescription — not required to continue"
        ],
        "uncertain_fields": [
            "Medication conflict between Betahistine and Stugeron requires clinician confirmation"
        ],
        "extraction_confidence": 0.91,
    },
}


class MockAIService:
    """
    Deterministic mock AI service.
    Works without any API key. Uses ground-truth dataset knowledge.
    """

    SYSTEM_NOTE = "MOCK AI MODE — No Gemini API key. Using deterministic extraction."

    def extract_medical_document(
        self,
        filename: str,
        raw_text: str,
        demo_report_number: int = None
    ) -> Dict[str, Any]:
        """Extract structured information from a medical document."""
        if demo_report_number and demo_report_number in DEMO_EXTRACTIONS:
            data = DEMO_EXTRACTIONS[demo_report_number].copy()
            data['document_id'] = filename
            data['_mock'] = True
            return data

        # Generic fallback extraction from raw text
        return self._generic_extract(filename, raw_text)

    def _generic_extract(self, filename: str, raw_text: str) -> Dict[str, Any]:
        """Fallback extraction for non-demo documents."""
        text_lower = (raw_text or '').lower()

        doc_type = 'unknown'
        if 'prescription' in text_lower or 'tab.' in text_lower or 'cap.' in text_lower:
            doc_type = 'prescription'
        elif 'lab' in text_lower or 'report' in text_lower or 'result' in text_lower:
            doc_type = 'lab_report'
        elif 'referral' in text_lower or 'refer' in text_lower:
            doc_type = 'referral_slip'
        elif 'consultation' in text_lower or 'note' in text_lower:
            doc_type = 'consultation_note'

        symptoms = []
        for word in ['dizziness', 'headache', 'nausea', 'fatigue', 'pain', 'fever']:
            if word in text_lower:
                symptoms.append(word.capitalize())

        return {
            'document_id': filename,
            'document_type': doc_type,
            'document_date': None,
            'provider': None,
            'symptoms': symptoms,
            'symptom_duration': None,
            'tests_ordered': [],
            'tests_completed': [],
            'reports_available': [],
            'referrals': [],
            'referral_specialty': None,
            'medication_mentions': [],
            'treatment_response': None,
            'follow_up_instructions': None,
            'result_review_status': 'unknown',
            'diagnostic_closure_documented': False,
            'source_fragments': [raw_text[:200]] if raw_text else [],
            'uncertain_fields': ['document type uncertain', 'date not detected'],
            'extraction_confidence': 0.50,
            '_mock': True,
        }

    def extract_patient_narration(self, narration_text: str) -> Dict[str, Any]:
        """Extract structured info from patient narration."""
        text_lower = narration_text.lower()
        return {
            'main_concern': 'Persistent dizziness',
            'symptom_duration': 'approximately 1 month',
            'consultations_remembered': 3,
            'tests_remembered': ['blood test', 'CBC'],
            'referral_remembered': 'ent' in text_lower or 'referral' in text_lower,
            'treatment_response': 'partial improvement',
            'medication_concerns': ['unsure which medication to continue'],
            'preferred_language': 'ta' if 'தமிழ்' in narration_text else 'en',
            'extraction_confidence': 0.78,
            '_mock': True,
        }

    def simplify_explanation(self, text: str, lang: str = 'en') -> str:
        """Simplify medical text for patient."""
        if lang == 'ta':
            return (
                "உங்கள் சிகிச்சை பயண நிலை மதிப்பாய்வு செய்யப்பட்டுள்ளது. "
                "மருத்துவர் ஆய்வு தேவைப்படும் சில முக்கியமான கேள்விகள் உள்ளன."
            )
        return (
            "Your diagnostic journey has been reviewed. "
            "There are some important unresolved questions that need clinician attention."
        )

    def generate_clinician_summary(self, journey_data: dict) -> str:
        """Generate a clinician-facing summary."""
        gaps = journey_data.get('remaining_gaps', [])
        n_gaps = len(gaps)
        state = journey_data.get('journey_state', 'Unknown')
        return (
            f"NidaanPath AI — Clinician Summary\n"
            f"Journey State: {state}\n"
            f"Unresolved process gaps: {n_gaps}\n"
            f"This summary is generated by a prototype system and is not a diagnosis.\n"
            f"[MOCK AI MODE]"
        )

    def select_agent_tool(self, context: dict) -> str:
        """Select the next agent tool to call."""
        phase = context.get('phase', 'extract')
        tool_map = {
            'extract': 'extract_medical_document',
            'build': 'build_diagnostic_journey',
            'gaps': 'detect_process_gaps',
            'evidence': 'select_next_evidence_question',
            'match': 'match_new_evidence',
            'packet': 'generate_clinician_packet',
        }
        return tool_map.get(phase, 'extract_medical_document')

    def translate_guidance(self, text: str, target_lang: str) -> str:
        """Translate guidance text."""
        if target_lang == 'ta':
            translations = {
                'Possible Stagnation': 'சாத்தியமான தேக்கம்',
                'Active Progress': 'செயலில் முன்னேற்றம்',
                'Clinician Escalation Required': 'மருத்துவர் ஆய்வு தேவை',
                'Awaiting Evidence': 'சான்று எதிர்பார்க்கிறது',
            }
            return translations.get(text, text)
        return text
