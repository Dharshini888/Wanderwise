import re
from typing import Tuple, Dict, Any

class LanguageValidator:
    """Validates that the generated itinerary uses the requested language and rejects unwanted scripts."""

    @staticmethod
    def validate(data: Dict[str, Any], requested_language: str = "English") -> Tuple[bool, str]:
        if not data or not isinstance(data, dict):
            return True, ""

        if requested_language.lower() != "english":
            return True, ""

        # Pattern to detect substantial Devanagari script (Hindi, Marathi, etc.)
        devanagari_pattern = re.compile(r'[\u0900-\u097F]')

        trip_data = data.get("trip", {})
        days = trip_data.get("days", [])
        
        for day in days:
            for activity in day.get("activities", []):
                # We check titles and descriptions
                title = activity.get("title", "")
                description = activity.get("description", "")
                
                # Check for Devanagari characters
                if devanagari_pattern.search(title):
                    print(f"[LANGUAGE VALIDATION] requested_language={requested_language} detected_script=Devanagari status=FAILED field=activity.title value={title}")
                    return False, f"Activity title contains forbidden characters for requested language {requested_language}: {title}"
                
                if devanagari_pattern.search(description):
                    print(f"[LANGUAGE VALIDATION] requested_language={requested_language} detected_script=Devanagari status=FAILED field=activity.description value={description[:30]}...")
                    return False, f"Activity description contains forbidden characters for requested language {requested_language}"

        return True, ""
