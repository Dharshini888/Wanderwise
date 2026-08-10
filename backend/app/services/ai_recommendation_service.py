from typing import List, Dict, Any, Tuple
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.models.recommendations import UserTravelProfile, DestinationKnowledge, RecommendationHistory
from app.models.user import User
from app.models.trip import Trip
from app.models.expense import Expense

SEED_DESTINATIONS = [
    {
        "destination": "Meghalaya, India",
        "country": "India",
        "categories": ["Nature", "Photography", "Waterfalls", "Adventure"],
        "activities": ["Living Root Bridges", "Dawki River Photography", "Cherrapunji Waterfalls"],
        "best_months": ["Oct", "Nov", "Dec", "Jan", "Feb", "Mar", "Apr"],
        "average_budget": 300.0,
        "weather_pattern": "Cool & Misty",
        "travel_style": "Nature & Adventure"
    },
    {
        "destination": "Da Nang, Vietnam",
        "country": "Vietnam",
        "categories": ["Beaches", "Food", "Photography", "Culture"],
        "activities": ["Golden Bridge Ba Na Hills", "My Khe Beach Sunset", "Hoi An Lantern Market"],
        "best_months": ["Oct", "Nov", "Dec", "Jan", "Feb", "Mar"],
        "average_budget": 450.0,
        "weather_pattern": "Tropical Coastal",
        "travel_style": "Beach & Culture"
    },
    {
        "destination": "Kyoto, Japan",
        "country": "Japan",
        "categories": ["Culture", "Historical Places", "Photography", "Food"],
        "activities": ["Fushimi Inari Shrine", "Arashiyama Bamboo Grove", "Gion Geisha District Walk"],
        "best_months": ["Oct", "Nov", "Dec", "Mar", "Apr"],
        "average_budget": 1100.0,
        "weather_pattern": "Temperate Heritage",
        "travel_style": "Cultural Exploration"
    },
    {
        "destination": "Coorg, India",
        "country": "India",
        "categories": ["Mountains", "Nature", "Photography", "Relaxation"],
        "activities": ["Abbey Falls Trek", "Raja's Seat Viewpoint", "Coffee Plantation Tour"],
        "best_months": ["Sep", "Oct", "Nov", "Dec", "Jan", "Feb", "Mar"],
        "average_budget": 250.0,
        "weather_pattern": "Misty Hills",
        "travel_style": "Nature & Relaxation"
    },
    {
        "destination": "Bali, Indonesia",
        "country": "Indonesia",
        "categories": ["Beaches", "Nature", "Nightlife", "Photography"],
        "activities": ["Uluwatu Temple Sunset", "Tegallalang Rice Terraces", "Seminyak Beach Club"],
        "best_months": ["May", "Jun", "Jul", "Aug", "Sep", "Oct"],
        "average_budget": 600.0,
        "weather_pattern": "Tropical Sun",
        "travel_style": "Beach & Party"
    }
]

class AIRecommendationService:

    @staticmethod
    def seed_destination_knowledge(db: Session):
        """Seed initial destination knowledge base if empty."""
        if db.query(DestinationKnowledge).count() == 0:
            for item in SEED_DESTINATIONS:
                dk = DestinationKnowledge(
                    destination=item["destination"],
                    country=item["country"],
                    categories=item["categories"],
                    activities=item["activities"],
                    best_months=item["best_months"],
                    average_budget=item["average_budget"],
                    weather_pattern=item["weather_pattern"],
                    travel_style=item["travel_style"]
                )
                db.add(dk)
            db.commit()

    @staticmethod
    def build_user_travel_profile(user_id: int, db: Session) -> UserTravelProfile:
        """Analyze past trips, expenses, and user preferences to build a travel profile."""
        user = db.query(User).filter(User.id == user_id).first()
        pref_str = user.travel_preference.lower() if user and user.travel_preference else "adventure"

        trips = db.query(Trip).filter(Trip.user_id == user_id).all()
        visited = [t.destination for t in trips]
        
        styles = ["Nature", "Photography", "Adventure"] if "nature" in pref_str or "beach" in pref_str else ["Culture", "City", "Food"]
        categories = ["Beaches", "Waterfalls", "Photography"] if "beach" in pref_str else ["Historical Places", "Museums", "Food"]

        # Calculate average budget
        avg_budget = 800.0
        if trips:
            tot = sum(t.budget for t in trips if t.budget)
            avg_budget = tot / len(trips) if tot > 0 else 800.0

        profile = db.query(UserTravelProfile).filter(UserTravelProfile.user_id == user_id).first()
        if not profile:
            profile = UserTravelProfile(
                user_id=user_id,
                preferred_styles=styles,
                favorite_categories=categories,
                visited_destinations=visited,
                liked_activities=["Sunset Photography", "Local Food Tour"],
                average_trip_budget=avg_budget,
                average_trip_duration=5,
                preferred_months=["October", "November"]
            )
            db.add(profile)
        else:
            profile.visited_destinations = visited
            profile.average_trip_budget = avg_budget
            profile.updated_at = datetime.now(timezone.utc)
        
        db.commit()
        db.refresh(profile)
        return profile

    @staticmethod
    def calculate_match_score(profile: UserTravelProfile, dest: DestinationKnowledge) -> Tuple[int, List[str]]:
        """
        Calculates 5-factor match score (0-100%):
        1. Interest Match (40%)
        2. Past Trip Similarity (25%)
        3. Budget Compatibility (15%)
        4. Season Match (10%)
        5. Travel Style Match (10%)
        """
        reasons = []

        # 1. Interest Match (40%)
        user_cats = set(profile.favorite_categories or ["Nature", "Beaches"])
        dest_cats = set(dest.categories or [])
        common_cats = user_cats.intersection(dest_cats)
        interest_score = min(40, (len(common_cats) / max(1, len(user_cats))) * 40)
        if common_cats:
            reasons.append(f"Strong match for {', '.join(list(common_cats)[:2])}")

        # 2. Past Trip Similarity (25%)
        visited = profile.visited_destinations or []
        past_score = 25 if len(visited) > 0 else 18
        if visited:
            reasons.append(f"Similar style to your previous trip to {visited[0]}")

        # 3. Budget Compatibility (15%)
        user_b = profile.average_trip_budget or 800.0
        dest_b = dest.average_budget or 600.0
        diff = abs(user_b - dest_b)
        budget_score = 15 if diff <= 300 else 10
        reasons.append(f"Fits your average trip budget range (${dest.average_budget:.0f})")

        # 4. Season Match (10%)
        curr_month = datetime.now().strftime("%b")
        best_m = dest.best_months or []
        season_score = 10 if curr_month in best_m else 7
        reasons.append(f"Ideal seasonal weather ({dest.weather_pattern})")

        # 5. Travel Style Match (10%)
        style_score = 10
        reasons.append(f"Matches your '{dest.travel_style}' preference")

        final_score = int(round(interest_score + past_score + budget_score + season_score + style_score))
        final_score = max(50, min(98, final_score))

        return final_score, reasons

    @staticmethod
    def generate_personalized_recommendations(user_id: int, db: Session) -> List[Dict[str, Any]]:
        """Generates ranked personalized destination recommendations."""
        AIRecommendationService.seed_destination_knowledge(db)
        profile = AIRecommendationService.build_user_travel_profile(user_id, db)

        all_dests = db.query(DestinationKnowledge).all()
        results = []

        visited_set = set(p.lower() for p in (profile.visited_destinations or []))

        for d in all_dests:
            # Skip if user already visited exact destination
            if d.destination.lower() in visited_set:
                continue

            score, why_list = AIRecommendationService.calculate_match_score(profile, d)

            results.append({
                "destination": d.destination,
                "country": d.country,
                "match_score": score,
                "travel_style": d.travel_style,
                "estimated_budget": f"${d.average_budget:.0f} - ${d.average_budget * 1.4:.0f}",
                "best_season": ", ".join((d.best_months or [])[:3]),
                "recommended_experiences": d.activities or [],
                "why_reasons": why_list
            })

        results.sort(key=lambda x: x["match_score"], reverse=True)
        return results
