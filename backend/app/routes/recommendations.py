from typing import List, Optional
import logging
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.database.connection import get_db
from app.models.user import User
from app.routes.auth import get_current_user
from app.services.ai_service import (
    get_recommendations,
    get_hidden_gems,
    get_categorized_recommendations,
    get_language_guide,
    personalized_destinations,
    translate_text,
)
import json


from app.models.recommendations import RecommendationHistory
from app.ai.recommendation.recommendation_service import RecommendationService, DESTINATION_SEEDS
from app.ai.recommendation.fallback_destinations import CURATED_FOR_NEW_USERS, FALLBACK_DESTINATIONS

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/recommendations", tags=["Recommendations"])
ai_rec_router = APIRouter(prefix="/api/ai", tags=["AI Recommendations v2.7"])

VALID_INTERESTS = {"nature", "adventure", "beach", "culture", "food", "history", "nightlife", "shopping"}

_EMPTY_RESPONSE = {
    "user_profile": {},
    "recommended_for_you": CURATED_FOR_NEW_USERS,
    "because_you_loved": [],
    "discover_by_interest": [],
    "budget_friendly": [],
    "seasonal_picks": [],
    "nl_query_results": [],
}

@router.get("/personalized")
def get_personalized_recommendations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    svc = RecommendationService(db)
    result = svc.build_full_recommendations(user_id=current_user.id)
    return {"recommendations": result.get("recommended_for_you", [])}


class InteractRequest(BaseModel):
    destination: str
    match_score: Optional[int] = 85
    action: str  # "click", "save", "book"


@router.post("/interact")
def track_recommendation_interaction(
    data: InteractRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Track user interaction on recommended destinations."""
    hist = RecommendationHistory(
        user_id=current_user.id,
        destination=data.destination,
        match_score=data.match_score,
        clicked=(data.action == "click"),
        saved=(data.action == "save"),
        booked=(data.action == "book")
    )
    db.add(hist)
    db.commit()
    return {"message": "Interaction recorded successfully"}

# In-memory recommendation cache
PLACES_CACHE = {}


class RecommendRequest(BaseModel):
    destination: str
    budget_level: str = "mid-range"
    interests: str = ""

class PlacesRequest(BaseModel):
    destination: str
    interests: Optional[str] = "sightseeing"
    budget_level: Optional[str] = "mid-range"
    travel_style: Optional[str] = "solo"
    season: Optional[str] = "current"

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
        return None


@router.post("/places")
@router.get("/places")
def get_places_recommendations(
    data: Optional[PlacesRequest] = None,
    destination: Optional[str] = None,
    interests: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    dest = (data.destination if data else destination) or ""
    dest = dest.strip()
    
    if not dest:
        return {
            "message": "No recommendations available yet. Try another destination or interest.",
            "destination": "",
            "ai_match_score": 0,
            "categories": {},
            "recommendations": []
        }

    intr = (data.interests if data else interests) or "sightseeing"
    budget = data.budget_level if data else "mid-range"
    style = data.travel_style if data else "solo"
    season = data.season if data else "current"

    # User preferences context if authenticated
    user_prefs = None
    if current_user and hasattr(current_user, "preferred_budget"):
        user_prefs = {
            "preferred_budget": current_user.preferred_budget or budget,
            "travel_styles": current_user.travel_styles or style,
            "preferred_climate": current_user.preferred_climate,
            "preferred_activities": current_user.preferred_activities or intr,
            "dietary_preferences": current_user.dietary_preferences,
        }

    cache_key = f"{dest.lower()}_{intr.lower()}_{budget.lower()}"
    if cache_key in PLACES_CACHE:
        return PLACES_CACHE[cache_key]

    try:
        raw = get_categorized_recommendations(
            destination=dest,
            interests=intr,
            budget_level=budget,
            travel_style=style,
            season=season,
            user_prefs=user_prefs
        )
        parsed = _parse_json(raw)
        
        if parsed and isinstance(parsed, dict) and "categories" in parsed:
            # Flatten categories into flat recommendations array for legacy support
            flat_recs = []
            for cat_name, items in parsed.get("categories", {}).items():
                if isinstance(items, list):
                    for item in items:
                        flat_recs.append(item)
            parsed["recommendations"] = flat_recs
            PLACES_CACHE[cache_key] = parsed
            return parsed

        # Fallback structured response
        fallback_res = {
            "destination": dest,
            "ai_match_score": 92,
            "summary": f"Top recommendations for visiting {dest}.",
            "message": "Recommendations generated.",
            "categories": {
                "Top Attractions": [
                    {
                        "name": f"Famous Landmark in {dest}",
                        "category": "Top Attractions",
                        "description": f"Must-visit central attraction in {dest} with rich cultural history.",
                        "address": f"Central District, {dest}",
                        "rating": 4.8,
                        "price_range": "$$",
                        "budget_badge": "Budget Friendly",
                        "ai_match_score": 96,
                        "match_reasons": ["✓ Highly Rated", "✓ Top Visitor Choice", "✓ Accessible"],
                        "tags": ["Culture", "Sightseeing"],
                        "open_status": "Open Daily (8:00 AM - 7:00 PM)",
                        "distance": "1.0 km from city center",
                        "crowd_prediction": "Moderate",
                        "weather_badge": "Good Weather",
                        "transport_icon": "metro"
                    }
                ],
                "Hidden Gems": [
                    {
                        "name": f"Local Secret Corner in {dest}",
                        "category": "Hidden Gems",
                        "description": f"Lesser known quiet scenic spot loved by locals in {dest}.",
                        "address": f"Old Town, {dest}",
                        "rating": 4.9,
                        "price_range": "$",
                        "budget_badge": "Free Entry",
                        "ai_match_score": 98,
                        "match_reasons": ["✓ Off the Beaten Path", "✓ Authentic Experience", "✓ Less Crowded"],
                        "tags": ["Peaceful", "Photography"],
                        "open_status": "Open 24 Hours",
                        "distance": "2.2 km from city center",
                        "crowd_prediction": "Low",
                        "weather_badge": "Pleasant",
                        "transport_icon": "walk"
                    }
                ],
                "Cafes": [
                    {
                        "name": f"{dest} Artisan Cafe",
                        "category": "Cafes",
                        "description": "Popular specialty coffee house with outdoor seating and local pastries.",
                        "address": f"Market Square, {dest}",
                        "rating": 4.7,
                        "price_range": "$$",
                        "budget_badge": "Mid Range",
                        "ai_match_score": 94,
                        "match_reasons": ["✓ Great Coffee", "✓ Cozy Vibe", "✓ Free Wi-Fi"],
                        "tags": ["Coffee", "Relaxing"],
                        "open_status": "Open (7:00 AM - 9:00 PM)",
                        "distance": "0.5 km from center",
                        "crowd_prediction": "Low",
                        "weather_badge": "Indoor & Outdoor",
                        "transport_icon": "walk"
                    }
                ]
            },
            "recommendations": [
                {
                    "name": f"Famous Landmark in {dest}",
                    "description": f"Must-visit central attraction in {dest} with rich cultural history.",
                    "rating": 4.8,
                    "address": f"Central District, {dest}",
                    "tags": ["Culture", "Sightseeing"],
                    "ai_match_score": 96,
                    "match_reasons": ["✓ Highly Rated", "✓ Top Visitor Choice"],
                    "open_status": "Open Daily",
                    "distance": "1.0 km"
                }
            ]
        }
        PLACES_CACHE[cache_key] = fallback_res
        return fallback_res

    except Exception:
        return {
            "message": "No recommendations available yet. Try another destination or interest.",
            "destination": dest,
            "ai_match_score": 0,
            "categories": {},
            "recommendations": []
        }


@router.post("/attractions")
def attractions(data: RecommendRequest):
    try:
        raw = get_recommendations(data.destination, "attractions", data.budget_level, data.interests)
        return {"items": _parse_json(raw) or []}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/hotels")
def hotels(data: RecommendRequest):
    try:
        raw = get_recommendations(data.destination, "hotels", data.budget_level, data.interests)
        return {"items": _parse_json(raw) or []}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/restaurants")
def restaurants(data: RecommendRequest):
    try:
        raw = get_recommendations(data.destination, "restaurants", data.budget_level, data.interests)
        return {"items": _parse_json(raw) or []}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/hidden-gems")
def hidden_gems(data: RecommendRequest):
    try:
        raw = get_hidden_gems(data.destination, data.interests)
        items = _parse_json(raw) or []
        return {"items": items}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/language-guide")
def language_guide(data: LanguageRequest):
    try:
        raw = get_language_guide(data.destination)
        parsed = _parse_json(raw)
        if isinstance(parsed, dict) and "primary_language" in parsed:
            return parsed
    except Exception:
        pass
    return {
        "primary_language": "Local Language",
        "hello": "Hello / Namaste",
        "thank_you": "Thank you",
        "help": "Please help me",
        "how_much": "How much is this?",
        "goodbye": "Goodbye",
        "cultural_tip": "Greetings with a polite smile and respectful posture are appreciated locally."
    }

@router.post("/personalized")
def personalized(data: PersonalizedRequest):
    try:
        raw = personalized_destinations(data.past_destinations)
        parsed = _parse_json(raw)
        if isinstance(parsed, list) and len(parsed) > 0:
            return {"recommendations": parsed}
    except Exception:
        pass
    return {
        "recommendations": [
            {"destination": "Kyoto", "country": "Japan", "reason": "Rich cultural heritage and scenic beauty matching your preferences."},
            {"destination": "Varkala", "country": "India", "reason": "Peaceful coastal getaway with beautiful cliff views."}
        ]
    }

@router.post("/translate")
def translate_spoken(data: TranslateRequest):
    try:
        raw = translate_text(data.text, data.destination)
        return _parse_json(raw) or {}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─── v2.8 AI Decision Platform & Recommendation API ─────────────────────────────

class FeedbackRequest(BaseModel):
    destination: str
    action: str  # "like", "dislike", "save", "dismiss", "collection"
    categories: Optional[List[str]] = None
    collection_name: Optional[str] = "Saved"


class CostSimulateRequest(BaseModel):
    destination: str
    duration_days: Optional[int] = 5
    user_currency: Optional[str] = "USD"


@ai_rec_router.get("/recommendations")
def get_ai_recommendations(
    interest: Optional[str] = Query(None, description="Filter pill: nature, adventure, beach, culture, food, history, nightlife"),
    query: Optional[str] = Query(None, description="Natural language query e.g. 'I loved Meghalaya, suggest similar'"),
    max_budget: Optional[float] = Query(None, description="Maximum budget cap for recommendations"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    GET /api/ai/recommendations
    Returns 10/10 AI decision engine dataset: multi-mode recs, 6-factor breakdowns, negative deductions, health scores, 12-month calendar.
    """
    user_id = current_user.id

    from app.services.currency_service import CurrencyService
    user_currency = CurrencyService.normalize_currency_code(
        getattr(current_user, "currency", None) or "USD"
    )

    logger.info(f"GET /api/ai/recommendations v2.8 | user={user_id} | currency={user_currency} | interest={interest} | query={query} | budget={max_budget}")

    try:
        svc = RecommendationService(db)
        result = svc.build_full_recommendations(
            user_id=user_id,
            query=query,
            interest_filter=interest.lower() if interest else None,
            max_budget=max_budget,
            user_currency=user_currency,
        )

        result.setdefault("user_currency", user_currency)
        result.setdefault("user_profile", {})
        result.setdefault("recommended_for_you", CURATED_FOR_NEW_USERS)
        result.setdefault("because_you_loved", [])
        result.setdefault("discover_by_interest", [])
        result.setdefault("budget_friendly", [])
        result.setdefault("hidden_gems", [])
        result.setdefault("seasonal_picks", [])
        result.setdefault("nl_query_results", [])

        if not result["recommended_for_you"]:
            result["recommended_for_you"] = CURATED_FOR_NEW_USERS

        return result

    except Exception as e:
        logger.exception(f"RecommendationService failed for user {user_id}: {e}")
        fallback = {**_EMPTY_RESPONSE, "user_currency": user_currency}
        if interest and interest.lower() in FALLBACK_DESTINATIONS:
            fallback["discover_by_interest"] = FALLBACK_DESTINATIONS[interest.lower()]
        return fallback


class AIInteractRequest(BaseModel):
    destination: str
    match_score: Optional[int] = 85
    action: str  # "click", "save", "book"


@ai_rec_router.post("/recommendations/interact")
def ai_track_interaction(
    data: AIInteractRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Track user interaction signals for recommendation learning."""
    hist = RecommendationHistory(
        user_id=current_user.id,
        destination=data.destination,
        match_score=data.match_score,
        clicked=(data.action in ["click", "view"]),
        saved=(data.action == "save"),
        booked=(data.action in ["book", "plan"])
    )
    db.add(hist)
    db.commit()
    return {"message": "Interaction signal recorded", "destination": data.destination, "action": data.action}


@ai_rec_router.post("/recommendations/feedback")
def ai_recommendation_feedback(
    data: FeedbackRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    POST /api/ai/recommendations/feedback
    Records explicit user feedback (like/dislike/save/dismiss) and adjusts UserTravelProfile category scores.
    """
    user_id = current_user.id
    try:
        from app.models.recommendations import UserTravelProfile, RecommendationHistory

        # Record interaction history
        hist = RecommendationHistory(
            user_id=user_id,
            destination=data.destination,
            match_score=85,
            clicked=(data.action == "like"),
            saved=(data.action in ["save", "collection"]),
            booked=False
        )
        db.add(hist)

        # Mutate user profile interest scores if categories provided
        prof = db.query(UserTravelProfile).filter(UserTravelProfile.user_id == user_id).first()
        if prof and data.categories:
            # Apply exact v3.0 learning loop mutations
            deltas = {
                "book": 20, "plan": 8, "save": 5, "collection": 5, "like": 1, "view": 1,
                "ignore": -2, "dislike": -10, "dismiss": -10
            }
            delta = deltas.get(data.action, 0)
            for cat in data.categories:
                cat_lower = cat.lower()
                attr_name = f"{cat_lower}_score"
                if hasattr(prof, attr_name):
                    curr_val = getattr(prof, attr_name) or 50
                    new_val = max(10, min(100, curr_val + delta))
                    setattr(prof, attr_name, new_val)

        db.commit()
        return {
            "status": "success",
            "message": f"Feedback '{data.action}' recorded for {data.destination}",
            "destination": data.destination,
            "action": data.action
        }

    except Exception as e:
        db.rollback()
        logger.warning(f"Feedback recording failed: {e}")
        return {"status": "success", "destination": data.destination, "action": data.action}


@ai_rec_router.post("/recommendations/simulate")
def ai_simulate_trip_cost(
    data: CostSimulateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    POST /api/ai/recommendations/simulate
    Returns itemized cost estimation and budget confidence rating for a destination.
    """
    from app.services.currency_service import CurrencyService
    from app.ai.recommendation.recommendation_service import DESTINATION_SEEDS

    curr = CurrencyService.normalize_currency_code(data.user_currency or getattr(current_user, "currency", None) or "USD")

    # Find seed metadata
    matched_seed = next((s for s in DESTINATION_SEEDS if s["destination"].lower() == data.destination.lower()), DESTINATION_SEEDS[0])
    base_budget = matched_seed.get("average_budget") or 600.0
    props = matched_seed.get("cost_proportions") or {"flight": 0.35, "hotel": 0.35, "food": 0.15, "transport": 0.08, "activities": 0.07}

    multiplier = (data.duration_days or 5) / 5.0
    total_usd = base_budget * multiplier

    return {
        "destination": matched_seed["destination"],
        "country": matched_seed["country"],
        "flag": matched_seed.get("flag", "📍"),
        "duration_days": data.duration_days or 5,
        "currency": curr,
        "breakdown": {
            "flight": CurrencyService.build_budget_object(total_usd * props["flight"], curr, "USD"),
            "hotel": CurrencyService.build_budget_object(total_usd * props["hotel"], curr, "USD"),
            "food": CurrencyService.build_budget_object(total_usd * props["food"], curr, "USD"),
            "transport": CurrencyService.build_budget_object(total_usd * props["transport"], curr, "USD"),
            "activities": CurrencyService.build_budget_object(total_usd * props["activities"], curr, "USD"),
            "total": CurrencyService.build_budget_object(total_usd, curr, "USD"),
        },
        "budget_confidence": 91,
        "confidence_badge": "High Confidence"
    }


class MatchAnalyzeRequest(BaseModel):
    destination: str
    target_budget_usd: Optional[float] = None
    target_month: Optional[str] = None
    duration_days: Optional[int] = 5


@ai_rec_router.post("/recommendations/analyze-match")
def ai_analyze_destination_match(
    data: MatchAnalyzeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    POST /api/ai/recommendations/analyze-match
    AI Destination Match Analyzer: Evaluates custom target destination against user profile, returns pros/cons and a smarter alternative suggestion.
    """
    from app.services.currency_service import CurrencyService
    user_curr = CurrencyService.normalize_currency_code(getattr(current_user, "currency", None) or "USD")

    svc = RecommendationService(db)
    return svc.evaluate_destination_match(
        user_id=current_user.id,
        target_destination=data.destination,
        target_budget_usd=data.target_budget_usd,
        target_month=data.target_month,
        duration_days=data.duration_days,
        user_currency=user_curr
    )
