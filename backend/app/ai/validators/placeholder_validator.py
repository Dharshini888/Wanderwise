import re
from typing import Tuple, Optional, Dict, Any

PLACEHOLDER_REGEX = re.compile(
    r"(?i)\b(landmark|bistro|museum|viewpoint|attraction|restaurant|activity|cafe|coffee|park|place|spot|location|site)\s*\d+\b"
)

GENERIC_PLACEHOLDER_STRINGS = [
    "historic landmark",
    "traditional bistro",
    "city museum",
    "central cafe",
    "sunset viewpoint",
    "sample place",
    "placeholder",
    "dummy place",
    "example location",
    "landmark 1",
    "bistro 1",
    "museum 1"
]

class PlaceholderValidator:
    """Stage 3: Anti-Placeholder Validation Layer. Strictly rejects template/placeholder text."""

    @staticmethod
    def validate(data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        trip_obj = data.get("trip") if "trip" in data else data
        days = trip_obj.get("days") or trip_obj.get("itinerary_days", [])

        for d_idx, day in enumerate(days):
            acts = day.get("activities", [])
            for a_idx, act in enumerate(acts):
                title = str(act.get("title") or "").strip()
                desc = str(act.get("description") or "").strip()
                place_obj = act.get("place") if isinstance(act.get("place"), dict) else {}
                p_name = str(place_obj.get("name") or act.get("place_name") or "").strip()

                text_to_check = f"{title} {p_name} {desc}"

                # 1. Regex check for numbered placeholders (e.g. Landmark 1, Bistro 2)
                match = PLACEHOLDER_REGEX.search(text_to_check)
                if match:
                    return False, f"PLACEHOLDER_CONTENT_DETECTED: Numbered placeholder '{match.group(0)}' found in Day {d_idx+1} Activity '{title}'"

                # 2. String check for generic placeholders
                lower_text = text_to_check.lower()
                for gen_str in GENERIC_PLACEHOLDER_STRINGS:
                    if gen_str in lower_text:
                        return False, f"PLACEHOLDER_CONTENT_DETECTED: Generic placeholder string '{gen_str}' found in Day {d_idx+1} Activity '{title}'"

        return True, None
