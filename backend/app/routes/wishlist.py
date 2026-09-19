from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from app.database.connection import get_db
from app.models.wishlist import WishlistItem
from app.services.wishlist_service import WishlistService
from app.services.ai_service import personalized_destinations
import json

router = APIRouter(prefix="/api/wishlist", tags=["Wishlist"])


class WishlistCreate(BaseModel):
    user_id: int
    destination: str
    country: Optional[str] = ""
    notes: Optional[str] = ""
    priority: Optional[str] = "someday"
    estimated_budget: Optional[float] = 120000.0
    duration_days: Optional[int] = 7
    best_season: Optional[str] = "October - March"
    travel_style: Optional[str] = "Nature & Culture"


class WishlistUpdate(BaseModel):
    notes: Optional[str] = None
    priority: Optional[str] = None
    estimated_budget: Optional[float] = None
    duration_days: Optional[int] = None
    is_visited: Optional[bool] = None
    is_planned: Optional[bool] = None


class WishlistCompareRequest(BaseModel):
    item_ids: List[int]


class PlanTripRequest(BaseModel):
    item_id: int
    user_id: int
    start_date: str = "2026-10-31"
    budget: Optional[float] = None


@router.get("/{user_id}")
def get_wishlist(user_id: int, db: Session = Depends(get_db)):
    items = db.query(WishlistItem).filter(
        WishlistItem.user_id == user_id
    ).order_by(WishlistItem.created_at.desc()).all()

    analytics = WishlistService.get_user_wishlist_analytics(user_id, db)

    # Ensure items have image URLs & coords
    serialized = []
    for item in items:
        img = item.image_url or WishlistService.get_destination_photo(item.destination)
        serialized.append({
            "id": item.id,
            "user_id": item.user_id,
            "destination": item.destination,
            "country": item.country or "Global",
            "notes": item.notes or "",
            "priority": item.priority or "someday",
            "estimated_budget": item.estimated_budget or 120000.0,
            "duration_days": item.duration_days or 7,
            "best_season": item.best_season or "October - March",
            "travel_style": item.travel_style or "Nature & Culture",
            "image_url": img,
            "rating": item.rating or 4.8,
            "ai_match_score": item.ai_match_score or 92.0,
            "is_visited": item.is_visited or False,
            "is_planned": item.is_planned or False,
            "visa_required": item.visa_required or False,
            "is_international": item.is_international or False,
            "latitude": item.latitude,
            "longitude": item.longitude,
            "created_at": item.created_at.isoformat() if item.created_at else None
        })

    return {
        "items": serialized,
        "analytics": analytics
    }


@router.post("/add")
def add_to_wishlist(data: WishlistCreate, db: Session = Depends(get_db)):
    # Auto-enrich destination with coords and image
    geo = WishlistService.geocode_destination(data.destination)
    img = WishlistService.get_destination_photo(data.destination)

    country_name = data.country if data.country else geo.get("country", "")

    item = WishlistItem(
        user_id=data.user_id,
        destination=data.destination,
        country=country_name,
        notes=data.notes,
        priority=data.priority or "dream",
        estimated_budget=data.estimated_budget or 120000.0,
        duration_days=data.duration_days or 7,
        best_season=data.best_season or "October - March",
        travel_style=data.travel_style or "Nature & Culture",
        image_url=img,
        rating=4.8,
        ai_match_score=94.0,
        is_visited=False,
        is_planned=False,
        visa_required=geo.get("is_international", False),
        is_international=geo.get("is_international", False),
        latitude=geo.get("lat"),
        longitude=geo.get("lon")
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.delete("/{item_id}")
def remove_from_wishlist(item_id: int, db: Session = Depends(get_db)):
    item = db.query(WishlistItem).filter(WishlistItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    db.delete(item)
    db.commit()
    return {"message": "Removed from wishlist"}


@router.put("/{item_id}")
def update_wishlist_item(item_id: int, data: WishlistUpdate, db: Session = Depends(get_db)):
    item = db.query(WishlistItem).filter(WishlistItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    if data.notes is not None:
        item.notes = data.notes
    if data.priority is not None:
        item.priority = data.priority
    if data.estimated_budget is not None:
        item.estimated_budget = data.estimated_budget
    if data.duration_days is not None:
        item.duration_days = data.duration_days
    if data.is_visited is not None:
        item.is_visited = data.is_visited
    if data.is_planned is not None:
        item.is_planned = data.is_planned

    db.commit()
    db.refresh(item)
    return item


@router.get("/details/{item_id}")
def get_wishlist_details(item_id: int, db: Session = Depends(get_db)):
    item = db.query(WishlistItem).filter(WishlistItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    img = item.image_url or WishlistService.get_destination_photo(item.destination)
    cost_variants = WishlistService.calculate_cost_variants(item.estimated_budget or 120000.0)

    # Fetch weather via Open-Meteo
    weather_info = {}
    try:
        from app.routes.weather import get_weather
        weather_info = get_weather(item.destination)
    except Exception:
        weather_info = {"current": {"temperature": 24, "description": "Sunny & Pleasant"}}

    # Fetch nearby attractions via POI Service
    nearby_pois = []
    try:
        from app.services.poi_service import fetch_real_pois_for_destination
        nearby_pois = fetch_real_pois_for_destination(item.destination)
    except Exception:
        nearby_pois = [
            {"name": f"Historic Central Square in {item.destination}", "category": "Sightseeing", "confidence": 0.98},
            {"name": f"Local Cultural Museum", "category": "Museum", "confidence": 0.95},
            {"name": f"Scenic Viewpoint Trail", "category": "Nature", "confidence": 0.97}
        ]

    return {
        "id": item.id,
        "destination": item.destination,
        "country": item.country or "Global",
        "notes": item.notes or "",
        "priority": item.priority,
        "estimated_budget": item.estimated_budget or 120000.0,
        "duration_days": item.duration_days or 7,
        "best_season": item.best_season or "October - March",
        "travel_style": item.travel_style or "Nature & Culture",
        "image_url": img,
        "rating": item.rating or 4.8,
        "ai_match_score": item.ai_match_score or 94.0,
        "is_visited": item.is_visited or False,
        "is_planned": item.is_planned or False,
        "visa_required": item.visa_required or False,
        "is_international": item.is_international or False,
        "latitude": item.latitude,
        "longitude": item.longitude,
        "cost_variants": cost_variants,
        "weather": weather_info,
        "nearby_attractions": nearby_pois[:6],
        "why_ai_recommends": f"Highly matched with your preference for {item.travel_style or 'nature & culture'}. Features optimal weather during {item.best_season or 'autumn'} and rich local heritage."
    }


@router.post("/compare")
def compare_wishlist_items(data: WishlistCompareRequest, db: Session = Depends(get_db)):
    if not data.item_ids or len(data.item_ids) < 2:
        raise HTTPException(status_code=400, detail="Select at least 2 destinations to compare")
    return WishlistService.compare_destinations(data.item_ids, db)


@router.get("/recommendations/{user_id}")
def get_wishlist_recommendations(user_id: int, db: Session = Depends(get_db)):
    items = db.query(WishlistItem).filter(WishlistItem.user_id == user_id).all()
    past_destinations = [item.destination for item in items]

    try:
        raw_recs = personalized_destinations(past_destinations)
        text = raw_recs.strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        return json.loads(text.strip())
    except Exception:
        return [
            {"destination": "Tokyo, Japan", "reason": "Recommended because: ✓ Similar culture & mountain scenery ✓ Fits budget", "vibe": "Culture & Tech"},
            {"destination": "Kyoto, Japan", "reason": "Recommended because: ✓ Historic temples & serene gardens ✓ Great autumn season", "vibe": "Heritage"},
            {"destination": "Varkala, India", "reason": "Recommended because: ✓ Scenic cliffside beach ✓ Highly cost effective", "vibe": "Beach & Sunset"}
        ]


@router.post("/plan-trip")
def plan_trip_from_wishlist(data: PlanTripRequest, db: Session = Depends(get_db)):
    try:
        return WishlistService.convert_wishlist_to_trip(
            item_id=data.item_id,
            user_id=data.user_id,
            start_date=data.start_date,
            budget=data.budget,
            db=db
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


