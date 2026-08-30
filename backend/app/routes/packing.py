from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.services.ai_service import generate_packing_list, AIServiceUnavailable, AIProviderAuthenticationError
from app.database.connection import get_db
from app.models.trip import Trip
from app.models.packing import PackingList
from app.services.packing_rules import ActivityGearMapper
from datetime import datetime
import json

router = APIRouter(prefix="/api/packing", tags=["Packing"])


class PackingRequest(BaseModel):
    destination: str
    start_date: str = ""
    end_date: str = ""
    duration: int
    travel_type: str = "leisure"
    weather: str = ""
    season: str = ""
    climate: str = ""
    activities: list = []


import re
import ast

def validate_packing_schema(data: dict) -> None:
    if not isinstance(data, dict):
        raise ValueError("Root must be a JSON object")
        
    context = data.get("context")
    if not isinstance(context, dict):
        raise ValueError("Missing or invalid 'context'")
    if "destination" not in context:
        raise ValueError("context.destination is missing")
    if "start_date" not in context:
        raise ValueError("context.start_date is missing")
    if "end_date" not in context:
        raise ValueError("context.end_date is missing")
    if "duration_days" not in context:
        raise ValueError("context.duration_days is missing")
    if not isinstance(context.get("activities"), list):
        raise ValueError("context.activities must be an array")
        
    categories = data.get("categories")
    if not isinstance(categories, list):
        raise ValueError("'categories' must be an array")
        
    for cat in categories:
        if "name" not in cat:
            raise ValueError("Category is missing 'name'")
        items = cat.get("items")
        if not isinstance(items, list):
            raise ValueError(f"Category {cat.get('name')} 'items' must be an array")
        for item in items:
            for field in ["name", "quantity", "weight_kg", "essential", "rationale", "packed"]:
                if field not in item:
                    raise ValueError(f"Item {item.get('name', 'Unknown')} is missing '{field}'")
                    
    warnings = data.get("warnings")
    if not isinstance(warnings, list):
        raise ValueError("'warnings' must be an array")
        
    missing = data.get("missing_essentials")
    if not isinstance(missing, list):
        raise ValueError("'missing_essentials' must be an array")
        
    score = data.get("packing_score")
    if not isinstance(score, (int, float)) or not (0 <= score <= 100):
        raise ValueError("'packing_score' must be numeric and between 0 and 100")
        
    daily_gear = data.get("daily_gear")
    if daily_gear is not None and not isinstance(daily_gear, list):
        raise ValueError("'daily_gear' must be an array")


def extract_json_from_ai(raw: str, trip_id=None) -> dict:
    try:
        text = raw.strip()
        
        # Remove Markdown code fences
        text = re.sub(r'^```[a-zA-Z]*\n', '', text)
        text = re.sub(r'\n```$', '', text)
        text = text.strip()
        
        # Extract the JSON object boundaries if necessary
        start_idx = text.find('{')
        end_idx = text.rfind('}')
        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
            text = text[start_idx:end_idx+1]
        
        parsed = None
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError as e:
            # Safe JSON repair fallback for single quotes
            try:
                parsed = ast.literal_eval(text)
                if not isinstance(parsed, dict):
                    raise ValueError("Evaluated object is not a dictionary")
            except Exception as ast_err:
                raise ValueError(f"Invalid JSON from AI (both json and ast failed). Decode error: {str(e)}")
        
        validate_packing_schema(parsed)
        return parsed
        
    except ValueError as ve:
        truncated = raw[:500] + "..." if len(raw) > 500 else raw
        if trip_id and 'logger' in globals():
            logger.error(f"[PACKING][ERROR] stage=schema_validate trip_id={trip_id} exception={str(ve)}. Raw response: {truncated}")
        raise ve
    except Exception as e:
        if trip_id and 'logger' in globals():
            logger.error(f"[PACKING][ERROR] stage=json_clean trip_id={trip_id} exception={str(e)}")
        raise ValueError(f"Failed to process AI response: {str(e)}")


@router.post("/generate")
def generate_list(data: PackingRequest):
    try:
        # Convert simple activities list to the daily_activities structure for the AI prompt
        custom_daily_activities = []
        if data.activities:
            activities_list = []
            for act_title in data.activities:
                # Still map gear using the rules engine for custom activities!
                mapped_gear = ActivityGearMapper.get_gear_for_activity(act_title)
                activities_list.append({
                    "name": act_title,
                    "recommended_gear": mapped_gear
                })
            custom_daily_activities.append({
                "day": 1,
                "date": data.start_date,
                "activities": activities_list
            })

        raw = generate_packing_list(
            destination=data.destination,
            start_date=data.start_date,
            end_date=data.end_date,
            duration=data.duration,
            travel_type=data.travel_type,
            daily_activities=custom_daily_activities,
            weather=data.weather,
            season=data.season,
            climate=data.climate
        )
        checklist = extract_json_from_ai(raw)
    except AIProviderAuthenticationError as e:
        raise HTTPException(
            status_code=401, 
            detail={
                "error": "AI_SERVICE_UNAVAILABLE",
                "message": "AI provider authentication failed. The configured AI provider rejected the API key.",
                "details": str(e)
            }
        )
    except AIServiceUnavailable as e:
        raise HTTPException(
            status_code=503, 
            detail={
                "error": "AI_SERVICE_UNAVAILABLE",
                "message": "AI provider temporarily unavailable.",
                "details": str(e)
            }
        )
    except ValueError as ve:
        raise HTTPException(
            status_code=502,
            detail={
                "error": "INVALID_AI_RESPONSE",
                "message": "AI provider returned an invalid packing response.",
                "details": str(ve)
            }
        )
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))
    return {"checklist": checklist}


import logging
logger = logging.getLogger(__name__)

@router.post("/generate-from-trip/{trip_id}")
def generate_from_trip(trip_id: int, db: Session = Depends(get_db)):
    logger.info(f"[PACKING] Starting generation trip_id={trip_id}")
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    if not trip:
        logger.error(f"[PACKING][ERROR] stage=trip_lookup trip_id={trip_id} exception=Trip not found")
        raise HTTPException(status_code=404, detail="Trip not found")

    # Calculate duration correctly
    duration = 1
    if trip.start_date and trip.end_date:
        delta = (trip.end_date - trip.start_date).days
        duration = max(1, delta + 1)
        
    start_str = trip.start_date.strftime("%Y-%m-%d") if trip.start_date else ""
    end_str = trip.end_date.strftime("%Y-%m-%d") if trip.end_date else ""
    
    # Simple seasonal/climate fallback
    month = trip.start_date.month if trip.start_date else datetime.now().month
    season_fallback = "Summer" if month in [6, 7, 8] else "Winter" if month in [12, 1, 2] else "Spring/Autumn"
    climate_fallback = "Variable"

    # Extract activities and map gear
    daily_activities = []
    if trip.itinerary_days:
        for day in trip.itinerary_days:
            day_data = {
                "day": day.day_number,
                "date": day.date.strftime("%Y-%m-%d") if day.date else "",
                "activities": []
            }
            for act in day.activities:
                if act.title:
                    mapped_gear = ActivityGearMapper.get_gear_for_activity(act.title, act.description)
                    day_data["activities"].append({
                        "name": act.title,
                        "recommended_gear": mapped_gear
                    })
            daily_activities.append(day_data)

    logger.info(f"[PACKING] Trip loaded")
    logger.info(f"[PACKING] Destination={trip.destination}")
    logger.info(f"[PACKING] Dates={start_str} → {end_str}")
    logger.info(f"[PACKING] Duration={duration}")
    logger.info(f"[PACKING] Activities Extracted={sum(len(d['activities']) for d in daily_activities)}")
    logger.info(f"[PACKING] Fetching weather...")
    logger.info(f"[PACKING] Weather source={climate_fallback}")
    logger.info(f"[PACKING] Calling AI packing service...")

    try:
        raw = generate_packing_list(
            destination=trip.destination,
            start_date=start_str,
            end_date=end_str,
            duration=duration,
            travel_type=trip.travel_style,
            daily_activities=daily_activities,
            season=season_fallback,
            climate=climate_fallback
        )
        logger.info(f"[PACKING] AI response received")
        logger.info(f"[PACKING] Parsing AI response...")
        checklist = extract_json_from_ai(raw, trip_id=trip_id)
    except Exception as e:
        logger.error(f"[PACKING][ERROR] stage=ai_generation trip_id={trip_id} exception={str(e)}")
        # Generate fallback using ActivityGearMapper
        fallback_categories = {
            "Essentials": ["Passport", "Wallet", "Phone", "Charger", "Medications"],
            "Clothing": ["Underwear", "Socks", "T-Shirts", "Pants", "Sleepwear"]
        }
        
        mapped_gear_all = set()
        for day in daily_activities:
            for act in day["activities"]:
                for item in act.get("recommended_gear", []):
                    mapped_gear_all.add(item)
                    
        if mapped_gear_all:
            fallback_categories["Activity Specific"] = list(mapped_gear_all)
            
        checklist = {
            "context": {
                "destination": trip.destination,
                "duration_days": duration,
                "season": season_fallback,
                "climate": climate_fallback,
                "weather_source": "Fallback logic"
            },
            "categories": [{"name": k, "items": [{"name": v, "rationale": "Recommended"} for v in items]} for k, items in fallback_categories.items()],
            "missing_essentials": [],
            "warnings": ["AI provider failed. This is a rule-based fallback checklist."],
            "daily_gear": daily_activities,
            "packing_score": 75.0,
            "generation_source": "rule_based_fallback"
        }

    # Persist or update packing list in DB
    packing_list = db.query(PackingList).filter(PackingList.trip_id == trip.id).first()
    if not packing_list:
        packing_list = PackingList(trip_id=trip.id, user_id=trip.user_id)
        db.add(packing_list)
        
    packing_list.destination = checklist.get("context", {}).get("destination", trip.destination)
    packing_list.start_date = checklist.get("context", {}).get("start_date", start_str)
    packing_list.end_date = checklist.get("context", {}).get("end_date", end_str)
    packing_list.duration_days = checklist.get("context", {}).get("duration_days", duration)
    packing_list.season = checklist.get("context", {}).get("season", season_fallback)
    packing_list.climate = checklist.get("context", {}).get("climate", climate_fallback)
    packing_list.weather_source = checklist.get("context", {}).get("weather_source", "Fallback")
    
    packing_list.categories = checklist.get("categories", [])
    packing_list.warnings = checklist.get("warnings", [])
    packing_list.missing_essentials = checklist.get("missing_essentials", [])
    packing_list.packing_score = checklist.get("packing_score", 0.0)
    packing_list.daily_gear = checklist.get("daily_gear", [])
    packing_list.generation_source = checklist.get("generation_source", "ai")
    
    db.commit()
    db.refresh(packing_list)
    
    return {"packing_list_id": packing_list.id, "checklist": checklist}

@router.get("/trip/{trip_id}")
def get_trip_packing_list(trip_id: int, db: Session = Depends(get_db)):
    packing_list = db.query(PackingList).filter(PackingList.trip_id == trip_id).first()
    if not packing_list:
        return {"status": "not_found"}
        
    return {
        "status": "found",
        "checklist": {
            "context": {
                "destination": packing_list.destination,
                "start_date": packing_list.start_date,
                "end_date": packing_list.end_date,
                "duration_days": packing_list.duration_days,
                "season": packing_list.season,
                "climate": packing_list.climate,
                "weather_source": packing_list.weather_source
            },
            "categories": packing_list.categories,
            "warnings": packing_list.warnings,
            "missing_essentials": packing_list.missing_essentials,
            "packing_score": packing_list.packing_score,
            "daily_gear": packing_list.daily_gear,
            "generation_source": packing_list.generation_source
        }
    }
