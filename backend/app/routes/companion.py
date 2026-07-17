from fastapi import APIRouter
from pydantic import BaseModel
from app.services.ai_service import companion_suggestions
import json

router = APIRouter(prefix="/api/companion", tags=["Companion"])


class CompanionRequest(BaseModel):
    destination: str
    current_day: int = 1
    total_days: int = 1
    itinerary_snippet: str = ""
    weather: str = ""


def _parse_json(raw: str):
    try:
        text = raw.strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        return json.loads(text.strip())
    except Exception:
        return {"greeting": raw, "suggestions": [], "reminders": []}


@router.post("/suggest")
def get_suggestions(data: CompanionRequest):
    raw = companion_suggestions(
        destination=data.destination,
        current_day=data.current_day,
        total_days=data.total_days,
        itinerary_snippet=data.itinerary_snippet,
        weather=data.weather,
    )
    return _parse_json(raw)
