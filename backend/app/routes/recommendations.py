from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.ai_service import get_recommendations, get_hidden_gems, get_language_guide, personalized_destinations, translate_text
import json
from typing import List

router = APIRouter(prefix="/api/recommendations", tags=["Recommendations"])


class RecommendRequest(BaseModel):
    destination: str
    budget_level: str = "mid-range"
    interests: str = ""

class LanguageRequest(BaseModel):
    destination: str

class TranslateRequest(BaseModel):
    text: str
    destination: str

class PersonalizedRequest(BaseModel):
    past_destinations: List[str]


def _parse_json(raw: str):
    try:
        text = raw.strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        return json.loads(text.strip())
    except Exception:
        return []


@router.post("/attractions")
def attractions(data: RecommendRequest):
    try:
        raw = get_recommendations(data.destination, "attractions", data.budget_level, data.interests)
        return {"items": _parse_json(raw)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/hotels")
def hotels(data: RecommendRequest):
    try:
        raw = get_recommendations(data.destination, "hotels", data.budget_level, data.interests)
        return {"items": _parse_json(raw)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/restaurants")
def restaurants(data: RecommendRequest):
    try:
        raw = get_recommendations(data.destination, "restaurants", data.budget_level, data.interests)
        return {"items": _parse_json(raw)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/hidden-gems")
def hidden_gems(data: RecommendRequest):
    try:
        raw = get_hidden_gems(data.destination, data.interests)
        items = _parse_json(raw)
        return {"items": items}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/language-guide")
def language_guide(data: LanguageRequest):
    try:
        raw = get_language_guide(data.destination)
        return _parse_json(raw)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/personalized")
def personalized(data: PersonalizedRequest):
    try:
        raw = personalized_destinations(data.past_destinations)
        return {"recommendations": _parse_json(raw)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/translate")
def translate_spoken(data: TranslateRequest):
    try:
        raw = translate_text(data.text, data.destination)
        return _parse_json(raw)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
