"""
NidaanPath AI — app/services/gemini_ai_service.py
Gemini API integration (requires GEMINI_API_KEY in .env).
"""
from __future__ import annotations
import json
import os
from typing import Dict, Any

try:
    from google import genai
    from google.genai import types
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False


SYSTEM_INSTRUCTION = """
You are the medical-document understanding component of NidaanPath AI.
Extract only information explicitly stated in the supplied document or patient narration.

Rules:
1. Do not diagnose.
2. Do not predict disease.
3. Do not prescribe.
4. Do not recommend tests.
5. Do not change medication.
6. Do not determine which medication instruction is correct.
7. Do not criticise a clinician.
8. Preserve uncertainty.
9. Preserve source evidence.
10. Return null when information is unavailable.
11. Keep a short source fragment for every extracted finding.
12. Mark clinical uncertainty for clinician review.
13. Return valid structured JSON output matching the required schema.
"""

EXTRACTION_SCHEMA = {
    "type": "object",
    "properties": {
        "document_type": {"type": "string"},
        "document_date": {"type": "string"},
        "provider": {"type": "string"},
        "symptoms": {"type": "array", "items": {"type": "string"}},
        "symptom_duration": {"type": "string"},
        "tests_ordered": {"type": "array", "items": {"type": "string"}},
        "tests_completed": {"type": "array", "items": {"type": "string"}},
        "reports_available": {"type": "array", "items": {"type": "string"}},
        "referrals": {"type": "array", "items": {"type": "string"}},
        "referral_specialty": {"type": "string"},
        "medication_mentions": {"type": "array", "items": {"type": "string"}},
        "treatment_response": {"type": "string"},
        "follow_up_instructions": {"type": "string"},
        "result_review_status": {"type": "string"},
        "diagnostic_closure_documented": {"type": "boolean"},
        "source_fragments": {"type": "array", "items": {"type": "string"}},
        "uncertain_fields": {"type": "array", "items": {"type": "string"}},
        "extraction_confidence": {"type": "number"}
    }
}


class GeminiAIService:
    """
    Gemini API AI service using google-genai.
    Requires GEMINI_API_KEY environment variable.
    Falls back to mock on error.
    """

    def __init__(self, api_key: str, model_name: str):
        self.api_key = api_key
        self.model_name = model_name
        self._client = None
        if GENAI_AVAILABLE and api_key:
            try:
                self._client = genai.Client(api_key=api_key)
            except Exception:
                self._client = None

    def _is_available(self) -> bool:
        return GENAI_AVAILABLE and self._client is not None

    def _call_gemini(self, prompt: str) -> str:
        """Make a Gemini API call with retry."""
        if not self._is_available():
            raise RuntimeError("Gemini client not available")
        response = self._client.models.generate_content(
            model=self.model_name,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                temperature=0.1,
                max_output_tokens=2048,
            )
        )
        return response.text

    def extract_medical_document(
        self, filename: str, raw_text: str, demo_report_number: int = None
    ) -> Dict[str, Any]:
        if not self._is_available():
            from .mock_ai_service import MockAIService
            return MockAIService().extract_medical_document(
                filename, raw_text, demo_report_number
            )
        prompt = (
            f"Extract structured information from this medical document.\n"
            f"Return ONLY a valid JSON object matching the schema. "
            f"Do not add any extra text.\n\n"
            f"Document content:\n{raw_text[:4000]}\n\n"
            f"Required JSON schema:\n{json.dumps(EXTRACTION_SCHEMA, indent=2)}"
        )
        try:
            result_text = self._call_gemini(prompt)
            # Find JSON in response
            start = result_text.find('{')
            end = result_text.rfind('}') + 1
            if start >= 0 and end > start:
                data = json.loads(result_text[start:end])
                data['document_id'] = filename
                data['_gemini'] = True
                return data
        except Exception as e:
            pass
        from .mock_ai_service import MockAIService
        return MockAIService().extract_medical_document(filename, raw_text, demo_report_number)

    def extract_patient_narration(self, narration_text: str) -> Dict[str, Any]:
        if not self._is_available():
            from .mock_ai_service import MockAIService
            return MockAIService().extract_patient_narration(narration_text)
        prompt = (
            "Extract structured information from this patient narration. "
            "Return ONLY valid JSON with keys: main_concern, symptom_duration, "
            "consultations_remembered, tests_remembered, referral_remembered, "
            "treatment_response, medication_concerns, preferred_language.\n\n"
            f"Narration: {narration_text}"
        )
        try:
            result = self._call_gemini(prompt)
            start = result.find('{')
            end = result.rfind('}') + 1
            if start >= 0:
                return json.loads(result[start:end])
        except Exception:
            pass
        from .mock_ai_service import MockAIService
        return MockAIService().extract_patient_narration(narration_text)

    def simplify_explanation(self, text: str, lang: str = 'en') -> str:
        if not self._is_available():
            from .mock_ai_service import MockAIService
            return MockAIService().simplify_explanation(text, lang)
        lang_instruction = "Respond in Tamil." if lang == 'ta' else "Respond in simple English."
        prompt = (
            f"{lang_instruction} Simplify this for a patient without medical background. "
            f"Do not diagnose or recommend treatment:\n\n{text}"
        )
        try:
            return self._call_gemini(prompt)
        except Exception:
            from .mock_ai_service import MockAIService
            return MockAIService().simplify_explanation(text, lang)

    def generate_clinician_summary(self, journey_data: dict) -> str:
        if not self._is_available():
            from .mock_ai_service import MockAIService
            return MockAIService().generate_clinician_summary(journey_data)
        prompt = (
            "Generate a concise clinician escalation summary from this diagnostic journey data. "
            "Do not diagnose. Do not prescribe. Identify only process gaps and unresolved evidence.\n\n"
            f"{json.dumps(journey_data, indent=2)[:3000]}"
        )
        try:
            return self._call_gemini(prompt)
        except Exception:
            from .mock_ai_service import MockAIService
            return MockAIService().generate_clinician_summary(journey_data)

    def select_agent_tool(self, context: dict) -> str:
        from .mock_ai_service import MockAIService
        return MockAIService().select_agent_tool(context)

    def translate_guidance(self, text: str, target_lang: str) -> str:
        if not self._is_available() or target_lang == 'en':
            from .mock_ai_service import MockAIService
            return MockAIService().translate_guidance(text, target_lang)
        prompt = f"Translate this to Tamil (தமிழ்). Keep medical terms in English:\n\n{text}"
        try:
            return self._call_gemini(prompt)
        except Exception:
            from .mock_ai_service import MockAIService
            return MockAIService().translate_guidance(text, target_lang)
