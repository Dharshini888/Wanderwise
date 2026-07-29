import json
import re
from typing import Tuple, Optional, Any

class JSONValidator:
    """Layer 1: Raw text JSON parsing & markdown cleanup."""

    @staticmethod
    def parse(raw_str: str) -> Tuple[bool, Optional[Any], Optional[str]]:
        if not raw_str or not raw_str.strip():
            return False, None, "Empty response received"

        clean = raw_str.strip()
        # Remove ```json backticks
        if "```" in clean:
            clean = re.sub(r"^```(?:json)?\s*", "", clean, flags=re.IGNORECASE)
            clean = re.sub(r"\s*```$", "", clean)
            clean = clean.strip()

        # Find first '{' and last '}'
        start_idx = clean.find("{")
        end_idx = clean.rfind("}")
        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
            clean = clean[start_idx:end_idx+1]

        try:
            data = json.loads(clean)
            return True, data, None
        except Exception as e:
            return False, None, f"JSON parse error: {e}"
