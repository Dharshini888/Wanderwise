from fastapi import APIRouter
from pydantic import BaseModel
from app.services.ai_service import transit_guide
import json

router = APIRouter(prefix="/api/transit", tags=["Transit"])


class TransitRequest(BaseModel):
    from_location: str
    to_location: str
    city: str


@router.post("/navigate")
def navigate(data: TransitRequest):
    raw = transit_guide(
        from_location=data.from_location,
        to_location=data.to_location,
        city=data.city,
    )
    try:
        text = raw.strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        result = json.loads(text.strip())
    except Exception:
        result = {"summary": raw, "steps": [], "tips": [], "alternatives": []}
    return result
