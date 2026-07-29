from typing import Dict, Any, List

class InterestAnalyzer:

    @staticmethod
    def extract_interest_scores(query_text: str, default_profile: Any = None) -> Dict[str, int]:
        """
        Analyzes natural language text or category pills to extract quantitative interest scores (0-100).
        """
        text = query_text.lower() if query_text else ""

        # Default scores from user profile or baseline
        scores = {
            "nature": getattr(default_profile, "nature_score", 70),
            "adventure": getattr(default_profile, "adventure_score", 65),
            "culture": getattr(default_profile, "culture_score", 60),
            "food": getattr(default_profile, "food_score", 75),
            "beach": getattr(default_profile, "beach_score", 50),
            "history": getattr(default_profile, "history_score", 55),
            "nightlife": getattr(default_profile, "nightlife_score", 40),
            "shopping": getattr(default_profile, "shopping_score", 45)
        }

        # Query text keyword boosting
        if any(w in text for w in ["nature", "waterfall", "mountain", "green", "lake", "forest"]):
            scores["nature"] = min(100, scores["nature"] + 25)
        if any(w in text for w in ["adventure", "trek", "hike", "water sports", "rafting"]):
            scores["adventure"] = min(100, scores["adventure"] + 25)
        if any(w in text for w in ["culture", "temple", "shrine", "tradition", "heritage"]):
            scores["culture"] = min(100, scores["culture"] + 25)
        if any(w in text for w in ["food", "cuisine", "eat", "street food", "market", "sushi"]):
            scores["food"] = min(100, scores["food"] + 25)
        if any(w in text for w in ["beach", "coastal", "island", "sea", "ocean", "sunset"]):
            scores["beach"] = min(100, scores["beach"] + 25)
        if any(w in text for w in ["history", "historical", "ancient", "museum", "ruins"]):
            scores["history"] = min(100, scores["history"] + 25)

        return scores
