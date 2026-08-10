# Carbon footprint service

def get_carbon_footprint(origin: str, destination: str):
    return {
        "modes": [
            { "mode": "Flight", "co2_kg": 420, "rating": "★★★★☆" },
            { "mode": "Train", "co2_kg": 61, "rating": "★★★★★" },
            { "mode": "Taxi", "co2_kg": 150, "rating": "★★★☆☆" },
            { "mode": "Bus", "co2_kg": 84, "rating": "★★★★★" }
        ],
        "suggestion": "Choose train to reduce emissions by 86%."
    }
