from fastapi import APIRouter
from pydantic import BaseModel
from app.services.ai_service import generate_packing_list
import json

router = APIRouter(prefix="/api/packing", tags=["Packing"])


class PackingRequest(BaseModel):
    destination: str
    duration: int
    travel_type: str = "leisure"
    weather: str = ""


@router.post("/generate")
def generate_list(data: PackingRequest):
    raw = generate_packing_list(
        destination=data.destination,
        duration=data.duration,
        travel_type=data.travel_type,
        weather=data.weather,
    )
    # Try to parse JSON from Gemini
    try:
        # Strip markdown code fences if present
        text = raw.strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        checklist = json.loads(text.strip())
    except Exception:
        checklist = {"Raw": [raw]}
    return {"checklist": checklist}
