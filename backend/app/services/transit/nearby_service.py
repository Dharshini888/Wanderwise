# Nearby essentials and alerts service

def get_nearby_essentials(destination: str):
    return [
        { "type": "Hospital", "icon": "🏥" },
        { "type": "ATM", "icon": "🏧" },
        { "type": "Petrol Station", "icon": "⛽" },
        { "type": "Hotel", "icon": "🏨" },
        { "type": "Restaurant", "icon": "🍽️" },
        { "type": "Police", "icon": "👮" },
        { "type": "Pharmacy", "icon": "💊" }
    ]

def get_dynamic_alerts(destination: str):
    return [
        { "type": "Traffic", "message": "Festival Traffic expected downtown." },
        { "type": "Weather", "message": "Heavy Rain Warning." }
    ]
