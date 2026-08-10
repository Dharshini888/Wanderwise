# Emergency service

def get_offline_emergency_data(destination: str):
    return {
        "medical": "112 (National Emergency), 108 (Ambulance)",
        "police": "100 / 112 (Police)",
        "hospital": f"{destination} General Hospital",
        "embassy": "Embassy details available offline.",
        "hotel_address": f"Hotel Stay, {destination}",
        "nearest_pharmacy": "24x7 City Pharmacy (0.8km)"
    }
