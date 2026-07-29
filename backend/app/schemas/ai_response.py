from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from datetime import datetime

class AIResponseMetadata(BaseModel):
    provider: str = "WanderWise AI"
    model: str = "gemini-2.5-flash"
    generation_time_ms: int = 1200
    retry_count: int = 0
    fallback_used: bool = False
    generated_at: Optional[str] = None

class AIResponse(BaseModel):
    schema_version: str = "1.0"
    metadata: AIResponseMetadata = Field(default_factory=AIResponseMetadata)
    trip: Dict[str, Any] = Field(default_factory=dict)
