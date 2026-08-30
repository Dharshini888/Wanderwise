"""
recommendation_engine.py — WanderWise Phase 2 Hybrid ML Recommendation Engine

Combines:
1. TF-IDF + Cosine Similarity (`DestinationSimilarityModel`)
2. User Embedding Representation (`UserEmbeddingModel`)
3. Collaborative Filtering Interactions (`CollaborativeFilter`)
4. Budget & Pace Matcher

Generates ranked destination and activity recommendations with EXPLAINABLE REASONS.
"""

from typing import List, Dict, Any
from .destination_similarity import DestinationSimilarityModel
from .user_embedding import UserEmbeddingModel
from .collaborative_filter import CollaborativeFilter


class HybridRecommendationEngine:
    """Hybrid ML Recommendation Engine powering WanderWise Smart Suggestions."""

    def __init__(self):
        self.similarity_model = DestinationSimilarityModel()
        self.user_embedding_model = UserEmbeddingModel()
        self.collaborative_filter = CollaborativeFilter()

    def rank_recommendations(
        self,
        user_id: int,
        user_profile: Dict[str, Any],
        candidates: List[Dict[str, Any]],
        current_trip: Dict[str, Any] = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """Ranks candidate recommendations using Hybrid ML scoring and returns explainable reasons."""
        if not candidates:
            return []

        # Train TF-IDF on candidate corpus
        self.similarity_model.fit(candidates)

        # Build user embedding
        user_vector = self.user_embedding_model.build_user_embedding(user_profile, user_profile.get("travel_history", []))

        user_interests = user_profile.get("travel_preferences", {}).get("interests", []) or user_profile.get("interests", [])
        user_interests_lower = [str(i).lower() for i in user_interests] if isinstance(user_interests, list) else []

        ranked_results = []

        for candidate in candidates:
            cand_name = candidate.get("name") or candidate.get("title") or "Item"
            cand_category = str(candidate.get("category", "")).lower()
            cand_tags = [str(t).lower() for t in candidate.get("tags", [])]

            # 1. Similarity Score
            sim_score = 0.5
            if current_trip:
                sim_score = self.similarity_model.similarity(current_trip, candidate)

            # 2. Interest Match Score
            interest_match_score = 0.4
            matched_interest_names = []
            for interest in user_interests_lower:
                if interest in cand_category or any(interest in tag for tag in cand_tags) or interest in cand_name.lower():
                    interest_match_score += 0.25
                    matched_interest_names.append(interest.capitalize())

            interest_match_score = min(1.0, interest_match_score)

            # 3. Collaborative Score
            collab_score = self.collaborative_filter.predict_user_item_affinity(user_id, cand_name)

            # 4. Budget Fit Score
            user_budget = user_profile.get("travel_preferences", {}).get("budget_tier", "moderate")
            item_budget = str(candidate.get("budget_tier", "moderate")).lower()
            budget_score = 0.9 if user_budget == item_budget or user_budget == "flexible" else 0.5

            # Hybrid Score Calculation (Weights: 35% Interest, 25% Similarity, 20% Collab, 20% Budget)
            final_score = round(
                (interest_match_score * 0.35) +
                (sim_score * 0.25) +
                (collab_score * 0.20) +
                (budget_score * 0.20),
                3
            )

            # Build EXPLAINABLE REASON
            reasons = []
            if matched_interest_names:
                reasons.append(f"Matches your preference for {', '.join(matched_interest_names[:2])}")
            elif interest_match_score > 0.6:
                reasons.append("Matches your travel profile & style")

            if sim_score > 0.6 and current_trip and current_trip.get("destination"):
                reasons.append(f"Complements your itinerary in {current_trip.get('destination')}")

            if collab_score > 0.6:
                reasons.append("Highly rated by travelers with similar interests")

            if budget_score >= 0.8:
                reasons.append(f"Fits your {user_budget} budget tier")

            if not reasons:
                reasons.append("Top curated attraction matching your trip duration")

            explanation = "Recommended because: " + " · ".join(reasons)

            cand_copy = dict(candidate)
            cand_copy["ml_score"] = final_score
            cand_copy["recommendation_reason"] = explanation
            cand_copy["explanation_details"] = {
                "interest_score": round(interest_match_score, 2),
                "similarity_score": round(sim_score, 2),
                "collaborative_score": round(collab_score, 2),
                "budget_score": round(budget_score, 2),
            }

            ranked_results.append(cand_copy)

        # Sort descending by hybrid score
        ranked_results.sort(key=lambda x: x["ml_score"], reverse=True)
        return ranked_results[:limit]
