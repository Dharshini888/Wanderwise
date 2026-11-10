import re
from typing import Tuple, Optional, Dict, Any

PLACEHOLDER_REGEX = re.compile(
    r"(?i)\b(landmark|bistro|museum|viewpoint|attraction|restaurant|activity|cafe|coffee|park|place|spot|location|site)\s*\d+\b"
    r"|\b(shortcut|shortcut to|footpath to|corridor to|path to|turn right|turn left|walk along|head north|head south|head east|head west|abandoned|abandond|old car|thai bamboo tattoo|blue corridor|sarawak flagpole|flightless birds|world of parrot|oriental bird aviaries|hornbill park|love aviary|bulbul land|brahminy kite|mini stone henge|godzilla x kong mural|upside down house)\b|\bzone\s*[1-4]\b"
)

EXACT_ONLY_PLACEHOLDERS = {
    "historic landmark",
    "traditional bistro",
    "city museum",
    "central cafe",
    "sunset viewpoint",
    "sample place",
    "dummy place",
    "example location",
    "placeholder",
    "shortcut",
    "shortcut to khao san",
    "abandond building",
    "abandoned building",
    "old car",
    "thai bamboo tattoo",
    "blue corridor",
    "sarawak flagpole",
    "flightless birds",
    "world of parrot",
    "oriental bird aviaries",
    "zone 1",
    "zone 2",
    "zone 3",
    "zone 4",
    "hornbill park",
    "love aviary",
    "bulbul land",
    "brahminy kite",
    "mini stone henge",
    "godzilla x kong mural",
    "upside down house",
    "bamboo wood",
    "old city wall",
    "seylanovs house",
    "historic city center",
    "city center",
    "central district",
    "historic center",
    "old town & heritage quarter",
    "riverfront promenade & public gardens",
    "artisan souvenir bazaar & walk",
    "local dining"
}

SUBSTRING_PLACEHOLDERS = [
    "scenic walk & artisan trail",
    "scenic overlook & panoramic vistas",
    "regional culinary lunch",
    "artisan trail near",
    "panoramic vistas:",
    "culinary lunch near",
    "landmark 1",
    "bistro 1",
    "museum 1",
    "shortcut",
    "shortcut to",
    "shortcut to khao san",
    "abandond building",
    "abandoned building",
    "old car",
    "thai bamboo tattoo",
    "turn right",
    "turn left",
    "walk along",
    "head north",
    "head south",
    "blue corridor",
    "sarawak flagpole",
    "flightless birds",
    "world of parrot",
    "oriental bird aviaries",
    "zone 1",
    "zone 2",
    "zone 3",
    "zone 4",
    "hornbill park",
    "love aviary",
    "bulbul land",
    "brahminy kite",
    "mini stone henge",
    "godzilla x kong mural",
    "upside down house",
    "bamboo wood",
    "old city wall",
    "seylanovs house",
    "cultural landmark & heritage enclave",
    "scenic park & nature boardwalk",
    "lunch recommendation near",
    "dinner recommendation near",
    "recommendation near",
    "historic city center",
    "local dining near",
    "independent dining exploration",
    "independent dining",
    "old town & heritage quarter",
    "riverfront promenade & public gardens",
    "artisan souvenir bazaar & walk"
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

                # 2. Check exact generic placeholders (where the place or title is just the placeholder)
                p_lower = p_name.lower().strip()
                t_lower = title.lower().strip()
                for gen_str in EXACT_ONLY_PLACEHOLDERS:
                    if p_lower == gen_str or t_lower == gen_str:
                        return False, f"PLACEHOLDER_CONTENT_DETECTED: Generic placeholder '{gen_str}' found in Day {d_idx+1} Activity '{title}'"

                # 3. Check substring placeholders (fabricated filler templates)
                lower_text = text_to_check.lower()
                for sub_str in SUBSTRING_PLACEHOLDERS:
                    if sub_str in lower_text:
                        return False, f"PLACEHOLDER_CONTENT_DETECTED: Generic placeholder string '{sub_str}' found in Day {d_idx+1} Activity '{title}'"

        return True, None
