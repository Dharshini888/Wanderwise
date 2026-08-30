"""
ai_learning_engine.py — WanderWise Phase 2 AI Learning Engine

Persistent Preference Learning Layer:
Tracks explicit & implicit user feedback (activity completions, skips, transit choices, budget selections).
Learns preference weights over time and exposes user reset control.
"""

import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


class AILearningEngine:
    """Persistent preference learning engine."""

    _user_preference_store: Dict[int, Dict[str, Any]] = {}

    @classmethod
    def get_learned_preferences(cls, user_id: int) -> Dict[str, Any]:
        """Returns the current learned preferences for a user."""
        if user_id not in cls._user_preference_store:
            cls._user_preference_store[user_id] = {
                "culture_weight": 1.0,
                "nature_weight": 1.0,
                "food_weight": 1.0,
                "adventure_weight": 1.0,
                "crowd_tolerance": "moderate",
                "preferred_transit": "public_transit",
                "budget_sensitivity": "moderate",
                "disliked_categories": [],
                "liked_categories": [],
                "learned_signals_count": 0,
            }
        return cls._user_preference_store[user_id]

    @classmethod
    def record_user_feedback(cls, user_id: int, action: str, category: str, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Updates learned weights based on user feedback signals (liked, skipped, visited, disliked)."""
        prefs = cls.get_learned_preferences(user_id)
        cat_lower = str(category).lower()
        metadata = metadata or {}

        if action in ["like", "visited", "save"]:
            if cat_lower not in prefs["liked_categories"]:
                prefs["liked_categories"].append(cat_lower)
            if cat_lower in prefs["disliked_categories"]:
                prefs["disliked_categories"].remove(cat_lower)

            if "museum" in cat_lower or "culture" in cat_lower or "art" in cat_lower:
                prefs["culture_weight"] = round(min(2.0, prefs["culture_weight"] + 0.15), 2)
            elif "nature" in cat_lower or "park" in cat_lower or "outdoor" in cat_lower:
                prefs["nature_weight"] = round(min(2.0, prefs["nature_weight"] + 0.15), 2)
            elif "food" in cat_lower or "dining" in cat_lower or "culinary" in cat_lower:
                prefs["food_weight"] = round(min(2.0, prefs["food_weight"] + 0.15), 2)

        elif action in ["skip", "dislike"]:
            if cat_lower not in prefs["disliked_categories"]:
                prefs["disliked_categories"].append(cat_lower)

            if "museum" in cat_lower or "culture" in cat_lower:
                prefs["culture_weight"] = round(max(0.2, prefs["culture_weight"] - 0.15), 2)
            elif "nature" in cat_lower or "outdoor" in cat_lower:
                prefs["nature_weight"] = round(max(0.2, prefs["nature_weight"] - 0.15), 2)

        if metadata.get("crowd_rating") == "crowded_disliked":
            prefs["crowd_tolerance"] = "low"
        if metadata.get("transit_choice"):
            prefs["preferred_transit"] = metadata["transit_choice"]

        prefs["learned_signals_count"] += 1
        cls._user_preference_store[user_id] = prefs
        logger.info(f"[AI Learning Engine] Updated user {user_id} learned preferences: {prefs}")
        return prefs

    @classmethod
    def reset_learned_preferences(cls, user_id: int) -> Dict[str, Any]:
        """Resets learned preferences back to default clean slate for transparency & control."""
        cls._user_preference_store[user_id] = {
            "culture_weight": 1.0,
            "nature_weight": 1.0,
            "food_weight": 1.0,
            "adventure_weight": 1.0,
            "crowd_tolerance": "moderate",
            "preferred_transit": "public_transit",
            "budget_sensitivity": "moderate",
            "disliked_categories": [],
            "liked_categories": [],
            "learned_signals_count": 0,
        }
        logger.info(f"[AI Learning Engine] User {user_id} reset learned preferences.")
        return cls._user_preference_store[user_id]
