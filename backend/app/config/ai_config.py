import os
from pydantic import BaseModel

class AISettings(BaseModel):
    DEFAULT_PROVIDER: str = os.getenv("AI_DEFAULT_PROVIDER", "gemini")
    FALLBACK_PROVIDER: str = os.getenv("AI_FALLBACK_PROVIDER", "groq")
    ENABLE_RETRY: bool = True
    MAX_RETRIES: int = 1
    TIMEOUT: int = 45
    TEMPERATURE: float = 0.3
    PROMPT_VERSION: str = "v1"
    MAX_TOKENS: int = 16000
    ENABLE_FALLBACK: bool = True
    ENABLE_CACHE: bool = False
    LOG_PROMPTS: bool = False

ai_settings = AISettings()
