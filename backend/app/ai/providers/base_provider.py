from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseAIProvider(ABC):
    """Abstract Base Class for AI Model Providers (Gemini, Groq, Mock)."""

    @abstractmethod
    def generate(self, prompt: str, system_instruction: str = "") -> str:
        """Execute raw AI prompt and return text/JSON response string."""
        pass

    def supports_structured_output(self) -> bool:
        """Capability check for structured JSON output."""
        return True

    def supports_function_calling(self) -> bool:
        """Capability check for function/tool calling."""
        return False
