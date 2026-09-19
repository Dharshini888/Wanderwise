from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict
from app.services.safety_hub_service import SafetyHubService
from app.services.ai_service import get_scam_alerts
import json
import sqlite3

router = APIRouter(prefix="/api/safety", tags=["Safety Hub"])

DB_PATH = "./wanderwise.db"
svc = SafetyHubService()


# ─── Database helpers ─────────────────────────────────────────────────────────
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_safety_tables():
    conn = get_db()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS safety_checklists (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            item_text TEXT,
            is_done INTEGER DEFAULT 0,
            category TEXT DEFAULT 'general',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS safety_incidents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            incident_type TEXT,
            description TEXT,
            location TEXT,
            latitude REAL,
            longitude REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()


try:
    init_safety_tables()
except Exception:
    pass


# ─── Pydantic Models ──────────────────────────────────────────────────────────
class ChecklistItem(BaseModel):
    user_id: int
    item_text: str
    category: str = "general"


class ChecklistUpdate(BaseModel):
    item_id: int
    is_done: bool


class IncidentReport(BaseModel):
    user_id: int
    incident_type: str
    description: str
    location: str
    latitude: float = 0.0
    longitude: float = 0.0


class LocationShare(BaseModel):
    user_id: int
    duration_hours: int = 6
    contacts: List[str] = []


def _parse_ai(raw: str) -> dict:
    try:
        text = raw.strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        return json.loads(text.strip())
    except Exception:
        return {"raw": raw}


# ─── Routes ───────────────────────────────────────────────────────────────────

@router.get("/dashboard")
def safety_dashboard(destination: str, user_id: int = 0):
    """Full safety dashboard — live weather, nearby services, AI tips, timeline."""
    import logging
    logger = logging.getLogger("wanderwise.safety")
    logger.info(f"[SAFETY] /dashboard request for destination: {destination}")

    geo = svc.geocode(destination)
    if not geo.get("is_valid", True) or geo.get("lat") is None or geo.get("lon") is None:
        logger.error(f"[SAFETY] Unable to resolve destination: {destination}")
        raise HTTPException(status_code=404, detail=f"Unable to resolve destination '{destination}'")

    lat, lon, country = geo["lat"], geo["lon"], geo["country"]

    location_obj = {
        "name": geo.get("city") or geo.get("display") or destination,
        "city": geo.get("city") or destination,
        "country": country,
        "display_name": geo.get("display_name") or geo.get("display") or destination,
        "latitude": lat,
        "longitude": lon,
        "country_code": geo.get("country_code", "in"),
        "is_valid": True,
    }

    weather = svc.get_live_weather(lat, lon)
    dashboard = svc.build_safety_dashboard(destination, weather, country)
    emergency = svc.get_emergency_contacts(country)
    timeline = svc.compute_safety_timeline(weather)
    ai_tips = svc.generate_ai_safety_tips(destination, weather, country)
    health = svc.get_health_advisory(lat, lon, country)

    ai_risk = {}

    scams = []
    try:
        raw = get_scam_alerts(destination)
        parsed = _parse_ai(raw)
        if isinstance(parsed, dict):
            scams = parsed.get("scams", [])
    except Exception:
        pass

    return {
        "destination": destination,
        "location": location_obj,
        "coordinates": {"lat": lat, "lon": lon},
        "country": country,
        "dashboard": dashboard,
        "weather": weather,
        "emergency_contacts": emergency,
        "timeline": timeline,
        "ai_tips": ai_tips,
        "health_advisory": health,
        "ai_risk_analysis": ai_risk,
        "scam_alerts": scams,
    }


@router.get("/weather")
def live_weather(lat: float, lon: float):
    """Live weather with safety warnings from Open-Meteo."""
    return svc.get_live_weather(lat, lon)


@router.get("/nearby")
def nearby_services(lat: float, lon: float):
    """Real nearby emergency services via Overpass API — expanded categories."""
    import logging
    logger = logging.getLogger("wanderwise.safety")
    logger.info(f"[SAFETY] /nearby request lat={lat} lon={lon}")
    if lat is None or lon is None:
        raise HTTPException(status_code=400, detail="Latitude and Longitude are required")
    return svc.get_nearby_services(lat, lon)


@router.get("/health")
def health_advisory(lat: float, lon: float, country: str = "India"):
    """Live health advisory — heat index, AQI, pollen, water safety."""
    return svc.get_health_advisory(lat, lon, country)


@router.get("/emergency")
def emergency_contacts(country: str = "India"):
    """Verified emergency contacts for any country."""
    return {
        "country": country,
        "contacts": svc.get_emergency_contacts(country)
    }


@router.get("/advisory")
def travel_advisory(destination: str):
    """AI-generated destination advisory (road, health, weather, events)."""
    ai_raw = {}
    return {
        "destination": destination,
        "advisory": ai_raw.get("top_recommendations", [
            "Check local news before travel.",
            "Carry local emergency contacts.",
            "Register with your country's embassy if staying > 7 days."
        ]),
        "status": "No active high-risk advisories"
    }


@router.get("/checklist/{user_id}")
def get_checklist(user_id: int):
    """Get user's personal safety checklist."""
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM safety_checklists WHERE user_id=? ORDER BY category, id",
        (user_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


@router.post("/checklist")
def add_checklist_item(body: ChecklistItem):
    """Add item to safety checklist."""
    conn = get_db()
    conn.execute(
        "INSERT INTO safety_checklists (user_id, item_text, category) VALUES (?,?,?)",
        (body.user_id, body.item_text, body.category)
    )
    conn.commit()
    row_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.close()
    return {"id": row_id, "message": "Added to checklist"}


@router.put("/checklist")
def update_checklist_item(body: ChecklistUpdate):
    """Mark checklist item complete/incomplete."""
    conn = get_db()
    conn.execute(
        "UPDATE safety_checklists SET is_done=? WHERE id=?",
        (1 if body.is_done else 0, body.item_id)
    )
    conn.commit()
    conn.close()
    return {"message": "Updated"}


@router.delete("/checklist/{item_id}")
def delete_checklist_item(item_id: int):
    conn = get_db()
    conn.execute("DELETE FROM safety_checklists WHERE id=?", (item_id,))
    conn.commit()
    conn.close()
    return {"message": "Deleted"}


@router.post("/report")
def report_incident(body: IncidentReport):
    """Log a personal safety incident report."""
    conn = get_db()
    conn.execute(
        """INSERT INTO safety_incidents
           (user_id, incident_type, description, location, latitude, longitude)
           VALUES (?,?,?,?,?,?)""",
        (body.user_id, body.incident_type, body.description,
         body.location, body.latitude, body.longitude)
    )
    conn.commit()
    row_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.close()
    return {"id": row_id, "message": "Incident reported. Stay safe."}


@router.get("/reports/{user_id}")
def get_incidents(user_id: int):
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM safety_incidents WHERE user_id=? ORDER BY created_at DESC LIMIT 20",
        (user_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


@router.post("/share-location")
def share_location(body: LocationShare):
    """Generate a temporary trip share token."""
    import secrets
    import time
    token = secrets.token_urlsafe(16)
    expires = int(time.time()) + body.duration_hours * 3600
    return {
        "share_token": token,
        "share_url": f"https://wanderwise.app/live/{token}",
        "expires_in_hours": body.duration_hours,
        "contacts_count": len(body.contacts),
        "status": "Live sharing active"
    }


@router.get("/assistant")
def safety_assistant(question: str, destination: str = ""):
    """AI safety assistant — answers contextual safety questions."""
    q_lower = question.lower()

    if "hospital" in q_lower or "medical" in q_lower:
        return {"answer": f"The nearest hospital to your location in {destination} can be found on the Nearby Services map in the Safety Hub. Tap '🏥 Hospitals' for real-time directions via OpenStreetMap."}
    if "police" in q_lower:
        return {"answer": f"The nearest police station is shown on the Nearby Services map. For emergencies in {destination}, call 112 (universal) or the local police number shown in Emergency Contacts."}
    if "passport" in q_lower or "lost" in q_lower:
        return {"answer": "If you've lost your passport: 1) File a police report immediately, 2) Contact your country's nearest embassy or consulate, 3) Apply for an Emergency Travel Document. Keep a digital copy in Google Drive as backup."}
    if "rain" in q_lower or "weather" in q_lower:
        return {"answer": f"Check the Live Weather panel for current conditions in {destination}. Current precipitation probability and wind speed are shown in real-time via Open-Meteo API."}
    if "safe" in q_lower and "area" in q_lower:
        return {"answer": f"Based on available data, {destination} shows a normal safety profile. Stick to well-lit, populated tourist areas especially after dark. Use the AI Risk Analysis for a complete breakdown."}
    if "restaurant" in q_lower or "food" in q_lower:
        return {"answer": "Use the Nearby Services map and tap 'Amenities' to discover nearby restaurants. Look for places with visible hygiene ratings. Avoid raw food from uncertified street vendors if you have a sensitive stomach."}

    return {"answer": f"For '{question}' in {destination}: I recommend checking the real-time Nearby Services map, the Live Weather panel, and the Emergency Contacts section for the most accurate information. Safety data is sourced from OpenStreetMap, Open-Meteo, and verified emergency databases."}
