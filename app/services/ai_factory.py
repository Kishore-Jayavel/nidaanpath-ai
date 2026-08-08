"""
NidaanPath AI — app/services/ai_factory.py
Factory that selects MockAIService or GeminiAIService based on config.
"""
from flask import current_app
from .mock_ai_service import MockAIService
from .gemini_ai_service import GeminiAIService

_service_cache = {}


def get_ai_service():
    """Return the appropriate AI service based on app config."""
    use_mock = current_app.config.get('USE_MOCK_LLM', True)
    api_key = current_app.config.get('GEMINI_API_KEY', '')
    model = current_app.config.get('GEMINI_MODEL', 'gemini-1.5-flash')

    if use_mock or not api_key:
        return MockAIService()
    return GeminiAIService(api_key=api_key, model_name=model)
