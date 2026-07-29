from typing import Dict, Any, List, Tuple
from datetime import datetime

class DestinationMatcher:

    @staticmethod
    def calculate_6factor_score(
        profile: Any,
        dest: Any,
        interest_scores: Dict[str, int]
    ) -> Tuple[int, List[str]]:
        """
        Implements 6-factor recommendation scoring formula:
        - Interest Match: 35%
        - Past Trip Similarity: 25%
        - Budget Match: 15%
        - Season Match: 10%
        - Travel Style Match: 10%
        - Popularity: 5%
        """
        reasons = []
        categories = [c.lower() for c in (dest.categories or [])]

        # 1. Interest Match (35%)
        # Calculate interest alignment score
        matched_interests = []
        interest_accum = 0.0
        for cat in categories:
            if cat in interest_scores and interest_scores[cat] > 50:
                matched_interests.append(cat)
                interest_accum += interest_scores[cat]

        interest_weight = (interest_accum / max(1, len(categories) * 100)) * 35.0
        interest_score = min(35.0, max(15.0, interest_weight))
        if matched_interests:
            reasons.append(f"Matches your high interest in {', '.join(matched_interests[:2])}")

        # 2. Past Trip Similarity (25%)
        visited = getattr(profile, "visited_destinations", []) or []
        past_score = 25.0 if len(visited) > 0 else 18.0
        if visited:
            reasons.append(f"Similar style to your previous trip to {visited[0]}")

        # 3. Budget Match (15%)
        user_b = getattr(profile, "average_trip_budget", 800.0) or 800.0
        dest_b = dest.average_budget or 500.0
        diff = abs(user_b - dest_b)
        budget_score = 15.0 if diff <= 300 else 10.0
        reasons.append(f"Fits your average budget range (${dest.average_budget:.0f})")

        # 4. Season Match (10%)
        curr_month = datetime.now().strftime("%B")
        best_months = dest.best_months or []
        season_score = 10.0 if curr_month in best_months or "October" in best_months else 7.0
        reasons.append(f"October/Autumn is ideal visiting season")

        # 5. Travel Style Match (10%)
        style_score = 10.0
        reasons.append(f"Matches your '{dest.travel_style}' style")

        # 6. Popularity (5%)
        pop_score = (dest.popularity_score / 100.0) * 5.0

        final_score = int(round(interest_score + past_score + budget_score + season_score + style_score + pop_score))
        final_score = max(55, min(96, final_score))

        return final_score, reasons
