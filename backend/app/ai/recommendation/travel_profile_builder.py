from typing import List, Dict, Any
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.models.recommendations import UserTravelProfile, TripPreferenceHistory
from app.models.user import User
from app.models.trip import Trip

class TravelProfileBuilder:

    @staticmethod
    def build_or_update_profile(user_id: int, db: Session) -> UserTravelProfile:
        """
        Builds or updates user travel profile based on user preferences and completed trips.
        """
        user = db.query(User).filter(User.id == user_id).first()
        pref_str = user.travel_preference.lower() if user and user.travel_preference else "nature & adventure"

        # Baseline interest scores derived from user sign-up preferences
        nature = 90 if any(w in pref_str for w in ["nature", "beach", "waterfall"]) else 65
        adventure = 85 if any(w in pref_str for w in ["adventure", "trek", "hike"]) else 60
        culture = 85 if any(w in pref_str for w in ["culture", "temple", "heritage", "history"]) else 60
        food = 80 if any(w in pref_str for w in ["food", "cuisine", "eat"]) else 70
        beach = 85 if "beach" in pref_str else 45
        history = 80 if "history" in pref_str else 50

        # Sync completed trip preference history
        completed_trips = db.query(Trip).filter(Trip.user_id == user_id, Trip.status == "Completed").all()
        visited_names = []
        tot_budget = 0.0

        for trip in completed_trips:
            visited_names.append(trip.destination)
            if trip.budget:
                tot_budget += trip.budget

            # Check if TripPreferenceHistory exists
            hist = db.query(TripPreferenceHistory).filter(
                TripPreferenceHistory.user_id == user_id,
                TripPreferenceHistory.trip_id == trip.id
            ).first()

            if not hist:
                hist = TripPreferenceHistory(
                    user_id=user_id,
                    trip_id=trip.id,
                    destination=trip.destination,
                    liked_categories=["nature", "photography", "waterfalls"] if "meghalaya" in trip.destination.lower() or "kerala" in trip.destination.lower() else ["culture", "food"],
                    activities_completed=["Waterfalls", "Trekking", "Photography"],
                    rating=5.0,
                    expense=trip.budget or 500.0,
                    duration=trip.duration_days if hasattr(trip, "duration_days") else 5,
                    month="October"
                )
                db.add(hist)

        avg_b = (tot_budget / len(completed_trips)) if completed_trips else 800.0

        profile = db.query(UserTravelProfile).filter(UserTravelProfile.user_id == user_id).first()
        if not profile:
            profile = UserTravelProfile(
                user_id=user_id,
                nature_score=nature,
                adventure_score=adventure,
                culture_score=culture,
                food_score=food,
                beach_score=beach,
                history_score=history,
                visited_destinations=visited_names,
                average_trip_budget=avg_b,
                preferred_months=["October", "November"]
            )
            db.add(profile)
        else:
            profile.nature_score = nature
            profile.adventure_score = adventure
            profile.culture_score = culture
            profile.food_score = food
            profile.beach_score = beach
            profile.history_score = history
            profile.visited_destinations = visited_names
            profile.average_trip_budget = avg_b
            profile.updated_at = datetime.now(timezone.utc)

        db.commit()
        db.refresh(profile)
        return profile
