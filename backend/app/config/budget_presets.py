from typing import Dict, Any

BUDGET_PRESETS: Dict[str, Dict[str, float]] = {
    "Luxury": {
        "Accommodation": 55.0,
        "Food": 20.0,
        "Transport": 10.0,
        "Activities": 10.0,
        "Emergency": 5.0
    },
    "Backpacking": {
        "Accommodation": 25.0,
        "Food": 25.0,
        "Transport": 25.0,
        "Activities": 20.0,
        "Emergency": 5.0
    },
    "Family": {
        "Accommodation": 40.0,
        "Food": 25.0,
        "Transport": 15.0,
        "Activities": 15.0,
        "Emergency": 5.0
    },
    "Business": {
        "Accommodation": 45.0,
        "Transport": 25.0,
        "Food": 15.0,
        "Activities": 10.0,
        "Emergency": 5.0
    },
    "Standard": {
        "Accommodation": 40.0,
        "Food": 20.0,
        "Transport": 20.0,
        "Activities": 15.0,
        "Emergency": 5.0
    }
}

def get_budget_preset(travel_style: str) -> Dict[str, float]:
    """Return budget breakdown percentages for a travel style."""
    if not travel_style:
        return BUDGET_PRESETS["Standard"]
    
    style_lower = travel_style.lower().strip()
    if "luxury" in style_lower:
        return BUDGET_PRESETS["Luxury"]
    elif "backpack" in style_lower or "budget" in style_lower:
        return BUDGET_PRESETS["Backpacking"]
    elif "family" in style_lower:
        return BUDGET_PRESETS["Family"]
    elif "business" in style_lower:
        return BUDGET_PRESETS["Business"]
    else:
        return BUDGET_PRESETS["Standard"]
