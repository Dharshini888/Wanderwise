"""
user_embedding.py — WanderWise Phase 2 ML Module

Builds user feature vector embeddings representing user interest weights, budget scale,
pace preference, and past destination interactions.
"""

from typing import Dict, Any, List


class UserEmbeddingModel:
    """User Interest Vector & Embedding Engine."""

    @staticmethod
    def build_user_embedding(user_profile: Dict[str, Any], travel_history: List[Dict[str, Any]]) -> Dict[str, float]:
        """Constructs a normalized feature vector for a user."""
        embedding: Dict[str, float] = {
            "culture": 0.5,
            "nature": 0.5,
            "food": 0.5,
            "adventure": 0.5,
            "relaxation": 0.5,
            "budget": 0.5,
            "luxury": 0.5,
        }

        # Boost from explicit preferences
        interests = user_profile.get("travel_preferences", {}).get("interests", []) or user_profile.get("interests", [])
        if isinstance(interests, list):
            for interest in interests:
                key = str(interest).lower()
                if key in embedding:
                    embedding[key] = min(1.0, embedding[key] + 0.3)
                elif "hist" in key or "museum" in key or "art" in key:
                    embedding["culture"] = min(1.0, embedding["culture"] + 0.3)
                elif "beach" in key or "park" in key or "mountain" in key:
                    embedding["nature"] = min(1.0, embedding["nature"] + 0.3)
                elif "rest" in key or "dine" in key or "culinary" in key:
                    embedding["food"] = min(1.0, embedding["food"] + 0.3)

        budget_tier = user_profile.get("travel_preferences", {}).get("budget_tier", "moderate")
        if budget_tier == "budget":
            embedding["budget"] = 0.9
            embedding["luxury"] = 0.1
        elif budget_tier == "luxury":
            embedding["luxury"] = 0.9
            embedding["budget"] = 0.2

        # Adjust weights from past trip history
        for trip in travel_history:
            tags = trip.get("tags", [])
            for t in tags:
                t_lower = str(t).lower()
                if t_lower in embedding:
                    embedding[t_lower] = min(1.0, embedding[t_lower] + 0.1)

        # Normalize embedding vector length
        total_sum = sum(embedding.values()) or 1.0
        return {k: round(v / total_sum, 3) for k, v in embedding.items()}
