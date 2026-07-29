import os
from typing import Optional
from app.config.ai_config import ai_settings
from app.ai.providers.base_provider import BaseAIProvider
from app.ai.providers.gemini_provider import GeminiProvider
from app.ai.providers.groq_provider import GroqProvider
from app.ai.providers.mock_provider import MockProvider

class AIProviderFactory:
    """Factory to retrieve AI providers with configuration and fallback support."""

    @staticmethod
    def get_provider(provider_name: Optional[str] = None) -> BaseAIProvider:
        name = (provider_name or ai_settings.DEFAULT_PROVIDER or "gemini").lower().strip()
        
        if name == "gemini":
            if os.getenv("GEMINI_API_KEY"):
                return GeminiProvider()
            elif os.getenv("GROQ_API_KEY"):
                return GroqProvider()
            else:
                return MockProvider()
        elif name == "groq":
            if os.getenv("GROQ_API_KEY"):
                return GroqProvider()
            elif os.getenv("GEMINI_API_KEY"):
                return GeminiProvider()
            else:
                return MockProvider()
        elif name == "mock":
            return MockProvider()
        else:
            return MockProvider()
