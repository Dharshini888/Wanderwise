import re

class ActivityGearMapper:
    """
    Rule-based engine to map actual database itinerary activities to required gear.
    """
    
    RULES = [
        {
            "keywords": ["beach", "swimming", "swim", "ocean", "pool"],
            "gear": ["Swimwear", "Towel", "Waterproof pouch", "Sunscreen", "Sunglasses"]
        },
        {
            "keywords": ["snorkel", "snorkeling", "scuba", "dive"],
            "gear": ["Swimwear", "Reef-safe sunscreen", "Waterproof pouch", "Snorkeling equipment (if not provided)"]
        },
        {
            "keywords": ["hike", "hiking", "trek", "trekking", "trail", "mountain", "peak"],
            "gear": ["Comfortable hiking shoes", "Breathable clothing", "Water bottle", "Sunscreen", "Hat", "Small backpack", "First aid kit"]
        },
        {
            "keywords": ["museum", "gallery", "exhibit", "art"],
            "gear": ["Comfortable walking shoes", "Daypack"]
        },
        {
            "keywords": ["palace", "temple", "shrine", "mosque", "church", "cathedral"],
            "gear": ["Comfortable walking shoes", "Modest/culturally appropriate clothing"]
        },
        {
            "keywords": ["formal", "dinner", "upscale", "gala", "restaurant", "fine dining"],
            "gear": ["Dressier outfit", "Appropriate footwear"]
        },
        {
            "keywords": ["rain", "monsoon", "storm"],
            "gear": ["Compact umbrella", "Rain jacket", "Waterproof bag"]
        },
        {
            "keywords": ["camp", "camping", "tent"],
            "gear": ["Tent-related equipment", "Sleeping equipment", "Flashlight/Headlamp", "First aid kit", "Bug repellent"]
        },
        {
            "keywords": ["cycle", "cycling", "bike", "biking", "bicycle"],
            "gear": ["Comfortable sports clothing", "Helmet (if not provided)", "Water bottle", "Small daypack"]
        },
        {
            "keywords": ["walk", "walking", "explore", "exploring", "sightseeing", "city", "tour"],
            "gear": ["Comfortable walking shoes", "Water bottle", "Daypack", "Power bank"]
        },
        {
            "keywords": ["photo", "photography", "shoot", "camera"],
            "gear": ["Camera", "Extra battery", "Memory card"]
        },
        {
            "keywords": ["cold", "snow", "ski", "winter"],
            "gear": ["Heavy jacket", "Sweater/Warm layers", "Gloves", "Beanie/Hat", "Scarf"]
        }
    ]

    @classmethod
    def get_gear_for_activity(cls, title: str, description: str = "") -> list:
        """
        Extracts required gear based on activity title and description.
        Returns a deduplicated list of recommended gear strings.
        """
        combined_text = f"{title or ''} {description or ''}".lower()
        
        recommended_gear = set()
        
        for rule in cls.RULES:
            for keyword in rule["keywords"]:
                if re.search(r'\b' + re.escape(keyword) + r'\b', combined_text):
                    for item in rule["gear"]:
                        recommended_gear.add(item)
                    break 
                    
        return sorted(list(recommended_gear))
