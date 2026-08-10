# AI Replanning Engine

def replan_itinerary(reason: str, delay_hours: int, current_itinerary: list):
    # Simulates shifting activities due to a delay
    # In a real app, this would recalculate timings for remaining activities
    return {
        "original": "Sunset Cruise 6 PM",
        "updated": "Sunset Cruise → Tomorrow 5 PM",
        "reason": f"{reason.replace('_', ' ').capitalize()} + availability optimization",
        "impact_cost": 0
    }
