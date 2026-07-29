from typing import List, Dict, Any

class SmartReplanner:
    @staticmethod
    def evaluate_weather_recommendation(weather_summary: str, activities: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Rule engine to generate weather-aware smart replanning recommendations.
        """
        if not weather_summary:
            return {
                "has_recommendation": False,
                "type": "none",
                "title": "Clear Conditions",
                "suggestions": []
            }

        weather_lower = weather_summary.lower()
        is_rainy = any(w in weather_lower for w in ["rain", "shower", "thunderstorm", "drizzle", "downpour"])
        is_extreme_heat = any(w in weather_lower for w in ["hot", "sunny", "heatwave", "35°", "36°", "37°", "38°", "39°", "40°"])

        suggestions = []

        if is_rainy:
            outdoor_activities = [a for a in activities if a.get("weather_suitability") == "outdoor"]
            if outdoor_activities:
                for act in outdoor_activities[:2]:
                    suggestions.append(f"Move '{act.get('title')}' to indoor venue or evening slot")
            suggestions.append("Visit local museum or indoor heritage site during heavy rain")

            return {
                "has_recommendation": True,
                "type": "weather_rain",
                "title": "Rain & Weather Alert",
                "condition": weather_summary,
                "suggestions": suggestions if suggestions else ["Shift outdoor tours to indoor galleries today"]
            }

        elif is_extreme_heat:
            return {
                "has_recommendation": True,
                "type": "weather_heat",
                "title": "☀️ Extreme Heat Advisory",
                "condition": weather_summary,
                "suggestions": [
                    "Plan outdoor walking tours before 10:30 AM or after 4:30 PM",
                    "Stay hydrated and utilize air-conditioned transit options"
                ]
            }

        return {
            "has_recommendation": False,
            "type": "normal",
            "title": "Favorable Weather",
            "suggestions": []
        }
