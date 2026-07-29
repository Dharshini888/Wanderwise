from typing import Tuple, Optional, Dict, Any

class SchemaValidator:
    """Layer 2: Structural schema validation for AI JSON payload."""

    @staticmethod
    def validate(data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        if not isinstance(data, dict):
            return False, "Payload root must be a JSON object"

        # Check root or wrapped trip object
        trip_obj = data.get("trip") if "trip" in data else data
        if not isinstance(trip_obj, dict):
            return False, "Trip object missing in JSON output"

        days = trip_obj.get("days") or trip_obj.get("itinerary_days")
        if not days or not isinstance(days, list):
            return False, "Days array missing or empty in trip object"

        for idx, d in enumerate(days):
            if not isinstance(d, dict):
                return False, f"Day at index {idx} must be an object"
            acts = d.get("activities", [])
            if not isinstance(acts, list):
                return False, f"Activities in Day {idx+1} must be an array"

        return True, None
