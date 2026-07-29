from typing import List, Dict, Any, Optional
from datetime import datetime, timezone, timedelta

def generate_weather_suggestions(trip: Any, today_info: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Evaluates weather conditions and today's outdoor activities to generate weather alert suggestions.
    """
    if not trip or not today_info:
        return []

    suggestions = []
    weather_cond = today_info.get("weather", {}).get("condition", "").lower()
    activities = today_info.get("activities", [])

    is_rainy = any(w in weather_cond for w in ["rain", "shower", "thunderstorm", "downpour", "drizzle"])
    outdoor_acts = [a for a in activities if a.get("weather_suitability") == "outdoor" or "beach" in a.get("title", "").lower()]

    if is_rainy and outdoor_acts:
        act = outdoor_acts[0]
        suggestions.append({
            "trip_id": trip.id,
            "type": "weather",
            "title": f"🌧 Weather Alert: Heavy Rain Expected in {trip.destination}",
            "description": f"Rain is expected today during your planned '{act.get('title')}' activity. We suggest moving outdoor activities to evening or an indoor venue.",
            "priority": "high",
            "priority_score": 95,
            "metadata_json": {
                "action_type": "update_itinerary",
                "suggested_change": {
                    "activity": act.get("title"),
                    "from_time": act.get("time", "10:00 AM"),
                    "to_time": "05:00 PM",
                    "reason": "Rain expected in the morning slot"
                },
                "why_reasons": [
                    f"You scheduled an outdoor activity ('{act.get('title')}')",
                    f"Rain probability increased for {trip.destination} ({weather_cond})",
                    "Indoor cultural alternatives available today"
                ]
            },
            "expires_at": datetime.now(timezone.utc) + timedelta(days=2)
        })

    return suggestions
