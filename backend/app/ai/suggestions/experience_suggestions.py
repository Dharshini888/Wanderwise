from typing import List, Dict, Any
from datetime import datetime, timezone, timedelta

def generate_experience_suggestions(trip: Any) -> List[Dict[str, Any]]:
    """
    Generates hidden local experience suggestions.
    """
    if not trip:
        return []

    suggestions = []
    dest = trip.destination

    suggestions.append({
        "trip_id": trip.id,
        "type": "experience",
        "title": f"✨ Hidden Gem Experience in {dest}",
        "description": f"Explore secret sunrise viewpoints and authentic local night markets during your stay in {dest}.",
        "priority": "low",
        "priority_score": 35,
        "metadata_json": {
            "action_type": "explore_experience",
            "experience_name": f"{dest} Hidden Heritage & Food Trail",
            "why_reasons": [
                f"Highly rated hidden gem by fellow WanderWise travelers in {dest}",
                "Away from heavy tourist crowd peak hours"
            ]
        },
        "expires_at": datetime.now(timezone.utc) + timedelta(days=7)
    })

    return suggestions
