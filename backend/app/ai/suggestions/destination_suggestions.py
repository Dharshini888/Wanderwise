from typing import List, Dict, Any
from datetime import datetime, timezone, timedelta

def generate_destination_suggestions(user_preference: str, past_trips: List[str]) -> List[Dict[str, Any]]:
    """
    Generates personalized destination recommendation suggestions based on user travel history and style.
    """
    suggestions = []
    
    past_names = [t.lower() for t in past_trips]
    
    if any(p in past_names for p in ["bali", "goa", "phuket", "thailand"]):
        rec_dest = "Da Nang, Vietnam 🇻🇳"
        reason_past = "Bali & coastal beach trips"
    else:
        rec_dest = "Kyoto, Japan 🇯🇵"
        reason_past = "Cultural heritage & city exploration"

    suggestions.append({
        "trip_id": None,
        "type": "destination",
        "title": f"🌍 Tailored Next Destination Idea: {rec_dest}",
        "description": f"Based on your travel preferences for {user_preference or 'adventure'}, {rec_dest} offers incredible experiences, great value, and ideal seasonal weather.",
        "priority": "medium",
        "priority_score": 55,
        "metadata_json": {
            "action_type": "explore_destination",
            "destination_name": rec_dest,
            "estimated_budget": "$650 - $1,200",
            "best_season": "Oct - Mar",
            "why_reasons": [
                f"You previously enjoyed trips to {', '.join(past_trips[:2]) if past_trips else 'scenic spots'}",
                f"Matches your saved travel style ('{user_preference or 'Adventure'}')",
                "Current season offers optimal weather & favorable flight rates"
            ]
        },
        "expires_at": datetime.now(timezone.utc) + timedelta(days=14)
    })

    return suggestions
