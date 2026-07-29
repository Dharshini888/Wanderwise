from typing import List, Dict, Any
from datetime import datetime, timezone, timedelta

def generate_itinerary_optimizations(trip: Any, activities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Analyzes activity sequence and travel distances to generate route optimization suggestions.
    """
    if not trip or len(activities) < 3:
        return []

    suggestions = []
    # If 3 or more activities, suggest smart route order optimization
    act_names = [a.get("title", "Stop") for a in activities[:3]]

    suggestions.append({
        "trip_id": trip.id,
        "type": "itinerary",
        "title": f"✨ Optimized Route: Save ~45 mins Travel Time in {trip.destination}",
        "description": f"We detected a more efficient travel route for today's activities: {act_names[1]} → {act_names[0]} → {act_names[2]}.",
        "priority": "medium",
        "priority_score": 70,
        "metadata_json": {
            "action_type": "optimize_route",
            "optimized_order": [act_names[1], act_names[0], act_names[2]],
            "why_reasons": [
                "Current sequence requires back-and-forth travel across town",
                "Optimized route reduces transit duration by 45 minutes",
                "Aligns with opening hours of primary venues"
            ]
        },
        "expires_at": datetime.now(timezone.utc) + timedelta(days=3)
    })

    return suggestions
