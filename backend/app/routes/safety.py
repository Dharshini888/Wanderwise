from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.ai_service import analyze_travel_risk, get_scam_alerts
import json

router = APIRouter(prefix="/api/safety", tags=["Safety"])


class RiskRequest(BaseModel):
    destination: str
    travel_dates: str = "upcoming"
    budget: float = 1000.0


class ScamRequest(BaseModel):
    destination: str


def _parse_json(raw: str):
    try:
        text = raw.strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        return json.loads(text.strip())
    except Exception:
        return {"raw": raw}


@router.post("/risk-score")
def risk_score(data: RiskRequest):
    try:
        raw = analyze_travel_risk(data.destination, data.travel_dates, data.budget)
        return _parse_json(raw)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/scam-alerts")
def scam_alerts(data: ScamRequest):
    try:
        raw = get_scam_alerts(data.destination)
        return _parse_json(raw)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{destination}")
def get_safety_hub_info(destination: str):
    risk_raw = analyze_travel_risk(destination, "upcoming", 1000.0)
    scam_raw = get_scam_alerts(destination)
    
    risk_data = _parse_json(risk_raw)
    scam_data = _parse_json(scam_raw)
    
    # Merge for frontend Safety.jsx
    return {
        "overall_score": risk_data.get("overall_score", 50),
        "overall_risk": risk_data.get("overall_label", "Moderate Risk"),
        "weather_risk": risk_data.get("weather_risk", 30),
        "crowd_risk": risk_data.get("crowd_risk", 40),
        "safety_risk": risk_data.get("safety_risk", 20),
        "emergency_numbers": risk_data.get("emergency_numbers", {"police": "112", "ambulance": "112", "fire": "112"}),
        "common_scams": [s.get("name", "Be cautious") + ": " + s.get("description", "") for s in scam_data.get("scams", [])] if "scams" in scam_data else ["Pickpocketing in crowded areas", "Overpriced taxis"],
        "recommended_actions": risk_data.get("top_recommendations", ["Stay hydrated", "Keep emergency contacts handy", "Register with your embassy"])
    }
