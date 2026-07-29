from typing import List, Dict, Any
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.ai_suggestions import AISuggestion
from app.models.user import User
from app.models.trip import Trip
from app.models.expense import Expense

from app.ai.suggestions.weather_suggestions import generate_weather_suggestions
from app.ai.suggestions.budget_suggestions import generate_budget_suggestions
from app.ai.suggestions.itinerary_optimizer import generate_itinerary_optimizations
from app.ai.suggestions.destination_suggestions import generate_destination_suggestions
from app.ai.suggestions.packing_suggestions import generate_packing_suggestions
from app.ai.suggestions.experience_suggestions import generate_experience_suggestions

class AISuggestionService:

    @staticmethod
    def generate_user_suggestions(user_id: int, db: Session) -> List[Dict[str, Any]]:
        """Proactively evaluate user context and persist new non-duplicate suggestions."""
        user = db.query(User).filter(User.id == user_id).first()
        user_pref = user.travel_preference if user else "Adventure"

        # Fetch active or most recent trip
        trip = db.query(Trip).filter(Trip.user_id == user_id).order_by(Trip.start_date.desc()).first()

        today_info = {}
        total_spent = 0.0
        total_budget = trip.budget if trip and trip.budget else 0.0

        if trip:
            from app.services.trip_service import get_today_itinerary, enrich_trip_response
            try:
                today_info = get_today_itinerary(trip.id, db, user_id)
            except Exception:
                pass
            
            enriched = enrich_trip_response(trip, db)
            total_spent = enriched.get("budget_spent", 0.0)

        past_trips = [t.destination for t in db.query(Trip).filter(Trip.user_id == user_id).all()]

        # Collect raw suggestions from all engines
        raw_items = []
        raw_items.extend(generate_weather_suggestions(trip, today_info))
        raw_items.extend(generate_budget_suggestions(trip, total_spent, total_budget))
        raw_items.extend(generate_itinerary_optimizations(trip, today_info.get("activities", [])))
        raw_items.extend(generate_destination_suggestions(user_pref, past_trips))
        raw_items.extend(generate_packing_suggestions(trip))
        raw_items.extend(generate_experience_suggestions(trip))

        # Cleanup expired suggestions
        now = datetime.now(timezone.utc)
        db.query(AISuggestion).filter(
            AISuggestion.user_id == user_id,
            AISuggestion.expires_at < now
        ).delete()
        db.commit()

        # Deduplicate & Persist
        saved_count = 0
        for item in raw_items:
            # Check duplicate active suggestion
            existing = db.query(AISuggestion).filter(
                AISuggestion.user_id == user_id,
                AISuggestion.status == "active",
                AISuggestion.title == item["title"]
            ).first()

            if not existing:
                score = item.get("priority_score", 50)
                prio = "high" if score >= 80 else "medium" if score >= 40 else "low"

                sug = AISuggestion(
                    user_id=user_id,
                    trip_id=item.get("trip_id"),
                    type=item["type"],
                    title=item["title"],
                    description=item["description"],
                    priority=prio,
                    priority_score=score,
                    metadata_json=item.get("metadata_json"),
                    status="active",
                    expires_at=item.get("expires_at")
                )
                db.add(sug)
                saved_count += 1

        db.commit()
        return AISuggestionService.get_user_suggestions(user_id, db)

    @staticmethod
    def get_user_suggestions(user_id: int, db: Session) -> Dict[str, List[Dict[str, Any]]]:
        """Retrieve active user suggestions grouped by priority with strict user isolation."""
        items = db.query(AISuggestion).filter(
            AISuggestion.user_id == user_id,
            AISuggestion.status == "active"
        ).order_by(AISuggestion.priority_score.desc(), AISuggestion.id.desc()).all()

        high, medium, low = [], [], []

        for s in items:
            s_dict = {
                "id": s.id,
                "user_id": s.user_id,
                "trip_id": s.trip_id,
                "type": s.type,
                "title": s.title,
                "description": s.description,
                "priority": s.priority,
                "priority_score": s.priority_score,
                "metadata": s.metadata_json or {},
                "status": s.status,
                "created_at": s.created_at.isoformat() if s.created_at else None
            }

            if s.priority == "high":
                high.append(s_dict)
            elif s.priority == "medium":
                medium.append(s_dict)
            else:
                low.append(s_dict)

        return {
            "high": high,
            "medium": medium,
            "low": low,
            "all_count": len(items)
        }

    @staticmethod
    def mark_suggestion_complete(suggestion_id: int, user_id: int, db: Session) -> bool:
        sug = db.query(AISuggestion).filter(
            AISuggestion.id == suggestion_id,
            AISuggestion.user_id == user_id
        ).first()

        if not sug:
            raise ValueError("Suggestion not found or unauthorized")

        sug.status = "completed"
        db.commit()
        return True

    @staticmethod
    def dismiss_suggestion(suggestion_id: int, user_id: int, db: Session) -> bool:
        sug = db.query(AISuggestion).filter(
            AISuggestion.id == suggestion_id,
            AISuggestion.user_id == user_id
        ).first()

        if not sug:
            raise ValueError("Suggestion not found or unauthorized")

        sug.status = "dismissed"
        db.commit()
        return True
