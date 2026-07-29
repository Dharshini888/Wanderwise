"""
recommendation_service.py  (v2.7.2 — global currency support)

6-Factor Scoring:
  Interest Match    → 35%
  Past Similarity   → 25%
  Budget Match      → 15%
  Season Match      → 10%
  Travel Style      → 10%
  Popularity        → 5%
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from sqlalchemy.orm import Session

from app.ai.recommendation.interest_analyzer import InterestAnalyzer
from app.ai.recommendation.destination_matcher import DestinationMatcher
from app.ai.recommendation.similarity_engine import SimilarityEngine
from app.services.currency_service import CurrencyService

logger = logging.getLogger(__name__)

VALID_INTERESTS = {"nature", "adventure", "beach", "culture", "food", "history", "nightlife", "shopping"}

# ─── In-Memory Destination Knowledge Base ────────────────────────────────────
DESTINATION_SEEDS = [
    {
        "destination": "Meghalaya", "country": "India",
        "categories": ["nature", "waterfall", "photography", "adventure", "trekking"],
        "activities": ["Living Root Bridges", "Dawki River Photography", "Trekking", "Caving"],
        "best_months": ["October", "November", "December", "January"],
        "average_budget": 600.0, "weather_pattern": "Cool & Misty",
        "travel_style": "Nature & Adventure", "popularity_score": 88
    },
    {
        "destination": "Kyoto", "country": "Japan",
        "categories": ["culture", "history", "photography", "nature", "temples"],
        "activities": ["Temple Tours", "Tea Ceremony", "Bamboo Grove Walk", "Geisha District"],
        "best_months": ["March", "April", "October", "November"],
        "average_budget": 1200.0, "weather_pattern": "Temperate",
        "travel_style": "Cultural & Scenic", "popularity_score": 95
    },
    {
        "destination": "Bali", "country": "Indonesia",
        "categories": ["beach", "culture", "food", "adventure", "nature"],
        "activities": ["Temple Visits", "Rice Terrace Walk", "Surfing", "Street Food"],
        "best_months": ["April", "May", "June", "July", "August", "September"],
        "average_budget": 700.0, "weather_pattern": "Tropical",
        "travel_style": "Beach & Culture", "popularity_score": 96
    },
    {
        "destination": "Sikkim", "country": "India",
        "categories": ["nature", "mountain", "adventure", "culture", "photography"],
        "activities": ["Tsomgo Lake", "Gangtok Ropeway", "Trekking", "Monastery Visits"],
        "best_months": ["October", "November", "March", "April", "May"],
        "average_budget": 500.0, "weather_pattern": "Cool Himalayan",
        "travel_style": "Mountain & Adventure", "popularity_score": 83
    },
    {
        "destination": "Bhutan", "country": "Bhutan",
        "categories": ["culture", "history", "nature", "adventure", "photography"],
        "activities": ["Tiger's Nest Monastery", "Punakha Dzong", "Archery Festival", "Trekking"],
        "best_months": ["March", "April", "October", "November"],
        "average_budget": 900.0, "weather_pattern": "Cool & Pristine",
        "travel_style": "Cultural & Spiritual", "popularity_score": 80
    },
    {
        "destination": "Coorg", "country": "India",
        "categories": ["nature", "coffee", "waterfall", "adventure", "wildlife"],
        "activities": ["Coffee Plantation Tour", "Abbey Falls", "Dubare Elephant Camp", "Trekking"],
        "best_months": ["October", "November", "December", "January", "February"],
        "average_budget": 350.0, "weather_pattern": "Lush Green",
        "travel_style": "Nature & Relaxation", "popularity_score": 79
    },
    {
        "destination": "Manali", "country": "India",
        "categories": ["adventure", "mountain", "snow", "trekking", "nature"],
        "activities": ["Rohtang Pass", "River Rafting", "Solang Valley", "Hadimba Temple"],
        "best_months": ["March", "April", "May", "June", "October"],
        "average_budget": 400.0, "weather_pattern": "Cold Himalayan",
        "travel_style": "Adventure & Mountains", "popularity_score": 87
    },
    {
        "destination": "Goa", "country": "India",
        "categories": ["beach", "nightlife", "food", "water sports", "culture"],
        "activities": ["Beach Parties", "Water Sports", "Old Goa Churches", "Flea Markets"],
        "best_months": ["November", "December", "January", "February"],
        "average_budget": 400.0, "weather_pattern": "Tropical",
        "travel_style": "Beach & Nightlife", "popularity_score": 93
    },
    {
        "destination": "Udaipur", "country": "India",
        "categories": ["history", "culture", "photography", "romantic", "lake"],
        "activities": ["City Palace Tour", "Lake Pichola Boating", "Vintage Car Museum", "Local Bazaars"],
        "best_months": ["October", "November", "December", "January", "February", "March"],
        "average_budget": 450.0, "weather_pattern": "Dry & Warm",
        "travel_style": "Cultural & Heritage", "popularity_score": 86
    },
    {
        "destination": "Phuket", "country": "Thailand",
        "categories": ["beach", "nightlife", "food", "water sports", "island"],
        "activities": ["Phi Phi Islands", "Patong Beach", "Muay Thai", "Thai Cuisine"],
        "best_months": ["November", "December", "January", "February", "March"],
        "average_budget": 600.0, "weather_pattern": "Tropical",
        "travel_style": "Beach & Entertainment", "popularity_score": 92
    },
    {
        "destination": "Munnar", "country": "India",
        "categories": ["nature", "tea", "mountain", "wildlife", "photography"],
        "activities": ["Tea Garden Walks", "Eravikulam National Park", "Top Station Trek", "Mattupetty Dam"],
        "best_months": ["September", "October", "November", "December", "January", "February"],
        "average_budget": 300.0, "weather_pattern": "Misty & Cool",
        "travel_style": "Nature & Relaxation", "popularity_score": 82
    },
    {
        "destination": "Rajasthan", "country": "India",
        "categories": ["history", "culture", "photography", "desert", "food"],
        "activities": ["Jaisalmer Fort", "Camel Safari", "Pushkar Festival", "Jaipur Palaces"],
        "best_months": ["October", "November", "December", "January", "February", "March"],
        "average_budget": 500.0, "weather_pattern": "Dry Desert",
        "travel_style": "Cultural & Heritage", "popularity_score": 90
    }
]

# ─── Fallback defaults per interest ─────────────────────────────────────────
FALLBACK_BY_INTEREST = {
    "nature": ["Meghalaya", "Sikkim", "Coorg", "Munnar"],
    "adventure": ["Manali", "Sikkim", "Meghalaya", "Bhutan"],
    "beach": ["Goa", "Bali", "Phuket", "Meghalaya"],
    "culture": ["Kyoto", "Bhutan", "Udaipur", "Rajasthan"],
    "food": ["Bali", "Kyoto", "Goa", "Rajasthan"],
    "history": ["Kyoto", "Udaipur", "Rajasthan", "Bhutan"],
    "nightlife": ["Goa", "Phuket", "Bali", "Manali"],
    "shopping": ["Goa", "Rajasthan", "Bali", "Phuket"],
}

# ─── Helpers ──────────────────────────────────────────────────────────────────

def _seed_destination_knowledge(db: Session):
    """Idempotent seed — silently skips on any DB error."""
    try:
        from app.models.recommendations import DestinationKnowledge
        for data in DESTINATION_SEEDS:
            existing = db.query(DestinationKnowledge).filter(
                DestinationKnowledge.destination == data["destination"]
            ).first()
            if not existing:
                dest = DestinationKnowledge(**data)
                db.add(dest)
        db.commit()
    except Exception as e:
        db.rollback()
        logger.warning(f"destination_knowledge seeding skipped (will use in-memory): {e}")


def _get_profile_dict(user_id: int, db: Session) -> Dict[str, Any]:
    """
    Load user travel profile from DB.
    Returns safe dict with defaults if profile not found or DB error.
    """
    defaults = {
        "nature": 65, "adventure": 65, "culture": 65, "food": 70,
        "beach": 50, "history": 55, "nightlife": 40, "shopping": 45,
        "average_budget": 800.0, "visited_destinations": []
    }
    try:
        from app.models.recommendations import UserTravelProfile
        profile = db.query(UserTravelProfile).filter(
            UserTravelProfile.user_id == user_id
        ).first()

        if not profile:
            logger.info(f"No travel profile for user {user_id} — using defaults")
            return defaults

        return {
            "nature": getattr(profile, "nature_score", 65) or 65,
            "adventure": getattr(profile, "adventure_score", 65) or 65,
            "culture": getattr(profile, "culture_score", 65) or 65,
            "food": getattr(profile, "food_score", 70) or 70,
            "beach": getattr(profile, "beach_score", 50) or 50,
            "history": getattr(profile, "history_score", 55) or 55,
            "nightlife": getattr(profile, "nightlife_score", 40) or 40,
            "shopping": getattr(profile, "shopping_score", 45) or 45,
            "average_budget": float(getattr(profile, "average_trip_budget", None) or getattr(profile, "average_budget", None) or 800.0),
            "visited_destinations": list(getattr(profile, "visited_destinations", None) or []),
        }
    except Exception as e:
        logger.warning(f"Failed to load user profile for {user_id}: {e}")
        return defaults


def _get_trip_history(user_id: int, db: Session) -> List[Dict[str, Any]]:
    """Load trip preference history safely."""
    try:
        from app.models.recommendations import TripPreferenceHistory
        histories = db.query(TripPreferenceHistory).filter(
            TripPreferenceHistory.user_id == user_id
        ).order_by(TripPreferenceHistory.created_at.desc()).limit(5).all()

        return [
            {
                "destination": h.destination,
                "liked_categories": list(h.liked_categories or []),
                "rating": float(h.rating or 5.0),
            }
            for h in histories
        ]
    except Exception as e:
        logger.warning(f"Failed to load trip history for {user_id}: {e}")
        return []


def _score_dest(seed: Dict, profile: Dict, interest_scores: Dict[str, int]) -> Tuple[int, List[str]]:
    """
    6-factor scoring using pure dicts — no ORM objects, no DB required.
    """
    cats = [c.lower() for c in (seed.get("categories") or [])]
    reasons = []

    # 1. Interest Match (35%)
    matched = [c for c in cats if c in interest_scores and interest_scores.get(c, 0) > 50]
    interest_accum = sum(interest_scores.get(c, 0) for c in matched)
    interest_weight = (interest_accum / max(1, len(cats) * 100)) * 35.0
    interest_score = min(35.0, max(10.0, interest_weight))
    if matched:
        reasons.append(f"Matches your interest in {', '.join(matched[:2])}")

    # 2. Past Trip Similarity (25%)
    visited = profile.get("visited_destinations") or []
    past_score = 22.0 if visited else 15.0
    if visited:
        reasons.append(f"Similar style to your previous trip to {visited[0]}")

    # 3. Budget Match (15%)
    user_b = float(profile.get("average_budget") or 800.0)
    dest_b = float(seed.get("average_budget") or 500.0)
    diff = abs(user_b - dest_b)
    budget_score = 15.0 if diff <= 400 else (10.0 if diff <= 700 else 6.0)
    reasons.append(f"Avg budget ${dest_b:.0f} fits your travel range")

    # 4. Season Match (10%)
    curr_month = datetime.now().strftime("%B")
    best_months = seed.get("best_months") or []
    season_score = 10.0 if curr_month in best_months else 6.0
    if curr_month in best_months:
        reasons.append(f"{curr_month} is peak season here")

    # 5. Travel Style (10%)
    style_score = 9.0
    reasons.append(f"'{seed.get('travel_style', 'Adventure')}' matches your style")

    # 6. Popularity (5%)
    pop_score = (int(seed.get("popularity_score") or 80) / 100.0) * 5.0

    final = int(round(interest_score + past_score + budget_score + season_score + style_score + pop_score))
    final = max(55, min(96, final))
    return final, reasons[:3]


def _serialize_seed(
    seed: Dict,
    score: int,
    reasons: List[str],
    based_on: str = None,
    user_currency: str = "USD",
    has_trip_history: bool = False,
) -> Dict:
    """Build a destination response dict with budget object in user's currency."""
    base_budget = seed.get("average_budget") or 500.0
    budget_obj = CurrencyService.build_budget_object(base_budget, user_currency, "USD")

    # Fix reason wording: don't claim past trips if user has none
    fixed_reasons = []
    for r in reasons:
        if not has_trip_history and "previous trip" in r.lower():
            fixed_reasons.append("Based on your selected interests")
        else:
            fixed_reasons.append(r)

    result = {
        "destination": seed["destination"],
        "country": seed["country"],
        "categories": seed.get("categories") or [],
        "activities": (seed.get("activities") or [])[:4],
        "best_months": seed.get("best_months") or [],
        "average_budget": base_budget,       # kept for backward compat
        "budget": budget_obj,                # new structured budget object
        "weather_pattern": seed.get("weather_pattern") or "",
        "travel_style": seed.get("travel_style") or "",
        "popularity_score": seed.get("popularity_score") or 80,
        "match_score": score,
        "reasons": fixed_reasons[:3],
    }
    if based_on:
        result["based_on"] = based_on
    return result


# ─── Main Service ─────────────────────────────────────────────────────────────

class RecommendationService:

    def __init__(self, db: Session):
        self.db = db
        # Seed DB in background — if it fails, we still work from DESTINATION_SEEDS
        _seed_destination_knowledge(db)

    def build_full_recommendations(
        self,
        user_id: int,
        query: Optional[str] = None,
        interest_filter: Optional[str] = None,
        max_budget: Optional[float] = None,
        user_currency: str = "USD",
    ) -> Dict[str, Any]:
        """
        Master recommendation builder — never raises. Returns safe defaults on any error.
        user_currency: ISO 4217 code e.g. 'INR', 'AED', 'EUR'
        """
        user_currency = (user_currency or "USD").upper()
        logger.info(
            f"Recommendation Request | user={user_id} | interest={interest_filter} | query={query} | budget={max_budget} | currency={user_currency}"
        )

        # Always-safe empty response
        safe_response: Dict[str, Any] = {
            "user_profile": {},
            "recommended_for_you": [],
            "because_you_loved": [],
            "discover_by_interest": [],
            "budget_friendly": [],
            "seasonal_picks": [],
            "nl_query_results": [],
        }

        try:
            profile = _get_profile_dict(user_id, self.db)
            trip_history = _get_trip_history(user_id, self.db)
            visited = profile.get("visited_destinations") or []

            logger.info(f"Profile loaded | profile_found={bool(profile)} | past_trips={len(trip_history)} | visited={visited}")

            # Base interest scores from profile
            base_scores: Dict[str, int] = {
                "nature": profile["nature"],
                "adventure": profile["adventure"],
                "culture": profile["culture"],
                "food": profile["food"],
                "beach": profile["beach"],
                "history": profile["history"],
                "nightlife": profile["nightlife"],
                "shopping": profile.get("shopping", 45),
            }

            # ── User Profile summary ──────────────────────────────────────────
            safe_response["user_profile"] = {**profile, **base_scores}
            safe_response["user_currency"] = user_currency

            # ── Mode 1: Recommended For You ───────────────────────────────────
            safe_response["recommended_for_you"] = self._recommended_for_you(
                profile, base_scores, visited, limit=6, user_currency=user_currency,
                has_trip_history=bool(trip_history)
            )

            # ── Mode 2: Because You Loved ─────────────────────────────────────
            safe_response["because_you_loved"] = self._because_you_loved(
                trip_history, visited, profile, user_currency=user_currency
            )

            # ── Mode 3: Budget Friendly ───────────────────────────────────────
            safe_response["budget_friendly"] = self._budget_friendly(
                profile, max_budget, visited, user_currency=user_currency
            )

            # ── Mode 4: Seasonal ──────────────────────────────────────────────
            safe_response["seasonal_picks"] = self._seasonal(visited, user_currency=user_currency)

            # ── Mode 5a: Discover By Interest ─────────────────────────────────
            if interest_filter:
                interest_lower = interest_filter.lower()
                if interest_lower not in VALID_INTERESTS:
                    safe_response["discover_by_interest"] = []
                else:
                    boosted = {**base_scores, interest_lower: 100}
                    safe_response["discover_by_interest"] = self._recommended_for_you(
                        profile, boosted, visited, limit=6
                    )

            # ── Mode 5b: Natural Language Query ───────────────────────────────
            if query and query.strip():
                nl_scores = InterestAnalyzer.extract_interest_scores(query, None)
                # Merge: nl scores + base profile
                merged = {k: max(base_scores.get(k, 50), nl_scores.get(k, 50)) for k in base_scores}
                safe_response["nl_query_results"] = self._recommended_for_you(
                    profile, merged, visited, limit=6, query_label=query
                )

        except Exception as e:
            logger.exception(f"Recommendation engine error for user {user_id}: {e}")
            # Return fallback curated list so the page is never empty
            safe_response["recommended_for_you"] = self._fallback_curated(user_currency=user_currency)
            safe_response["seasonal_picks"] = self._seasonal([], user_currency=user_currency)
            safe_response["budget_friendly"] = [
                _serialize_seed(s, s["popularity_score"], ["Great value destination", "Popular among budget travelers"],
                                user_currency=user_currency)
                for s in sorted(DESTINATION_SEEDS, key=lambda x: x["average_budget"])[:4]
            ]

        return safe_response

    # ── Private helpers ────────────────────────────────────────────────────────

    def _recommended_for_you(
        self,
        profile: Dict,
        interest_scores: Dict[str, int],
        visited: List[str],
        limit: int = 6,
        query_label: str = None,
        user_currency: str = "USD",
        has_trip_history: bool = False,
    ) -> List[Dict]:
        try:
            scored = []
            seen = set()
            for seed in DESTINATION_SEEDS:
                dest_name = seed["destination"]
                if dest_name in visited or dest_name in seen:
                    continue
                seen.add(dest_name)
                score, reasons = _score_dest(seed, profile, interest_scores)
                if query_label:
                    reasons.insert(0, f'Matches your query: "{query_label}"')
                scored.append((score, seed, reasons))

            scored.sort(key=lambda x: x[0], reverse=True)
            return [
                _serialize_seed(s, sc, r, user_currency=user_currency, has_trip_history=has_trip_history)
                for sc, s, r in scored[:limit]
            ]
        except Exception as e:
            logger.warning(f"_recommended_for_you error: {e}")
            return self._fallback_curated(user_currency=user_currency)

    def _because_you_loved(
        self,
        trip_history: List[Dict],
        visited: List[str],
        profile: Dict,
        user_currency: str = "USD",
    ) -> List[Dict]:
        try:
            if not trip_history:
                return []

            groups = []
            for hist in trip_history[:2]:
                src = hist["destination"]
                src_tags = hist.get("liked_categories") or ["nature", "adventure"]

                similarities = []
                seen = set()
                for seed in DESTINATION_SEEDS:
                    dest_name = seed["destination"]
                    if dest_name in visited or dest_name == src or dest_name in seen:
                        continue
                    seen.add(dest_name)
                    sim_score, sim_reasons = SimilarityEngine.calculate_destination_similarity(
                        src, src_tags, {"destination": dest_name, "categories": seed.get("categories") or []}
                    )
                    similarities.append((sim_score, seed, sim_reasons))

                similarities.sort(key=lambda x: x[0], reverse=True)
                top = [
                    _serialize_seed(s, sc, r, based_on=src, user_currency=user_currency, has_trip_history=True)
                    for sc, s, r in similarities[:4]
                ]
                if top:
                    groups.append({"based_on": src, "destinations": top})

            return groups
        except Exception as e:
            logger.warning(f"_because_you_loved error: {e}")
            return []

    def _budget_friendly(
        self,
        profile: Dict,
        max_budget: Optional[float],
        visited: List[str],
        user_currency: str = "USD",
    ) -> List[Dict]:
        try:
            cap_usd = max_budget or (float(profile.get("average_budget") or 800.0) * 0.85)
            cap_label = CurrencyService.format(
                CurrencyService.convert(cap_usd, "USD", user_currency), user_currency
            )
            budget_seeds = [
                s for s in DESTINATION_SEEDS
                if s["average_budget"] <= cap_usd and s["destination"] not in visited
            ]
            budget_seeds.sort(key=lambda x: x["popularity_score"], reverse=True)
            seen = set()
            result = []
            for s in budget_seeds:
                if s["destination"] in seen:
                    continue
                seen.add(s["destination"])
                result.append(_serialize_seed(s, s["popularity_score"], [
                    f"Well within your budget cap of {cap_label}",
                    "High value-to-cost ratio",
                    "Popular among budget-conscious travelers"
                ], user_currency=user_currency))
                if len(result) >= 6:
                    break
            return result
        except Exception as e:
            logger.warning(f"_budget_friendly error: {e}")
            return []

    def _seasonal(self, visited: List[str], user_currency: str = "USD") -> List[Dict]:
        try:
            curr_month = datetime.now().strftime("%B")
            seasonal = [
                s for s in DESTINATION_SEEDS
                if curr_month in (s.get("best_months") or []) and s["destination"] not in visited
            ]
            seasonal.sort(key=lambda x: x["popularity_score"], reverse=True)
            seen = set()
            result = []
            for s in seasonal:
                if s["destination"] in seen:
                    continue
                seen.add(s["destination"])
                result.append(_serialize_seed(s, s["popularity_score"], [
                    f"{curr_month} is peak season for {s['destination']}",
                    "Ideal weather conditions this month",
                    "Most activities available now"
                ], user_currency=user_currency))
                if len(result) >= 6:
                    break
            return result
        except Exception as e:
            logger.warning(f"_seasonal error: {e}")
            return []

    def _fallback_curated(self, user_currency: str = "USD") -> List[Dict]:
        """Top 6 curated picks when profile data unavailable — for new users."""
        top = sorted(DESTINATION_SEEDS, key=lambda x: x["popularity_score"], reverse=True)[:6]
        return [
            _serialize_seed(s, s["popularity_score"], [
                "Highly rated destination",
                "Great for first-time travelers",
                "Based on popular traveler choices"
            ], user_currency=user_currency)
            for s in top
        ]
