from typing import Tuple, Optional, Dict, Any

class WeatherValidator:
    """Stage 7: Conditional Weather & Rain Mode Filter Layer."""

    @staticmethod
    def validate(data: Dict[str, Any], weather_info: Optional[Dict[str, Any]] = None) -> Tuple[bool, Optional[str]]:
        # If no weather forecast data passed, skip gracefully
        if not weather_info:
            return True, None

        is_rainy = False
        condition = str(weather_info.get("condition") or weather_info.get("weather") or "").lower()
        if "rain" in condition or "storm" in condition or "shower" in condition:
            is_rainy = True

        if not is_rainy:
            return True, None

        trip_obj = data.get("trip") if "trip" in data else data
        days = trip_obj.get("days") or trip_obj.get("itinerary_days", [])

        for d_idx, day in enumerate(days):
            acts = day.get("activities", [])
            for a_idx, act in enumerate(acts):
                suitability = str(act.get("weather_suitability") or "").lower()
                category = str(act.get("category") or "").lower()
                title = str(act.get("title") or "").lower()

                # If rain forecast and activity is strictly outdoor hiking/park walk
                if suitability == "outdoor" and ("park" in title or "hiking" in title or "walking tour" in title):
                    return False, f"WEATHER_VIOLATION: Outdoor activity '{act.get('title')}' scheduled during rain forecast on Day {d_idx+1}. Substitute with indoor museum/aquarium."

        return True, None
