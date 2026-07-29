from typing import List, Dict, Any
from datetime import datetime, timezone, timedelta

def generate_budget_suggestions(trip: Any, total_spent: float, total_budget: float) -> List[Dict[str, Any]]:
    """
    Evaluates spending velocity vs total budget to generate proactive budget recommendations.
    """
    if not trip or total_budget <= 0:
        return []

    suggestions = []
    spent_pct = (total_spent / total_budget) * 100.0
    curr = trip.currency or "USD"

    if spent_pct >= 75.0:
        suggestions.append({
            "trip_id": trip.id,
            "type": "budget",
            "title": f"💰 High Budget Usage Warning: {spent_pct:.0f}% Spent",
            "description": f"You have spent {curr} {total_spent:.0f} out of your total {curr} {total_budget:.0f} budget. Consider local dining alternatives to preserve funds.",
            "priority": "high",
            "priority_score": 85,
            "metadata_json": {
                "action_type": "view_budget",
                "total_budget": total_budget,
                "spent": total_spent,
                "remaining": max(0, total_budget - total_spent),
                "why_reasons": [
                    f"Spent amount ({curr} {total_spent:.0f}) reached {spent_pct:.0f}% of total budget",
                    "Daily food/dining expenses above recommended average",
                    "Remaining journey days require budget pacing"
                ]
            },
            "expires_at": datetime.now(timezone.utc) + timedelta(days=7)
        })
    elif spent_pct >= 50.0:
        suggestions.append({
            "trip_id": trip.id,
            "type": "budget",
            "title": f"💡 Budget Health Check: Halfway Mark Reached",
            "description": f"You have used 50% of your budget for {trip.destination}. Track remaining expenses to stay on target.",
            "priority": "medium",
            "priority_score": 60,
            "metadata_json": {
                "action_type": "view_budget",
                "total_budget": total_budget,
                "spent": total_spent,
                "remaining": max(0, total_budget - total_spent),
                "why_reasons": [
                    "Budget milestone reached: 50% utilized",
                    "Current spending pace is stable"
                ]
            },
            "expires_at": datetime.now(timezone.utc) + timedelta(days=7)
        })

    return suggestions
