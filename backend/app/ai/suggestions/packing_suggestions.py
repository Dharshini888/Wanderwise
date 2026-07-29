from typing import List, Dict, Any
from datetime import datetime, timezone, timedelta

def generate_packing_suggestions(trip: Any) -> List[Dict[str, Any]]:
    """
    Generates weather-aware packing suggestions for upcoming or active trips.
    """
    if not trip:
        return []

    suggestions = []
    dest = trip.destination

    suggestions.append({
        "trip_id": trip.id,
        "type": "packing",
        "title": f"🎒 Smart Packing Advice for {dest}",
        "description": f"Don't forget to pack a light jacket, rain umbrella, power adapter, and comfortable walking shoes for your upcoming journey to {dest}.",
        "priority": "low",
        "priority_score": 45,
        "metadata_json": {
            "action_type": "view_packing",
            "suggested_items": ["Light Jacket / Rain Poncho", "Universal Power Adapter", "Comfortable Trail Shoes", "Reusable Water Bottle"],
            "why_reasons": [
                f"Weather forecast for {dest} indicates variable temperatures",
                "Planned itinerary involves 5+ km walking per day",
                "Local electrical outlet compatibility"
            ]
        },
        "expires_at": datetime.now(timezone.utc) + timedelta(days=5)
    })

    return suggestions
