"""
tz_utils.py -- Robust timezone resolution for WanderWise Transit.

Provides ZoneInfo lookup when tzdata is available, with graceful fallback
to fixed-offset timezones (e.g. UTC+05:30 for Asia/Kolkata) on Windows systems
where tzdata may not be installed.
"""

from datetime import datetime, timezone, timedelta
from typing import Optional


def get_timezone(tz_name: Optional[str] = "Asia/Kolkata") -> timezone:
    """
    Return a timezone object for the given tz_name.
    - If tz_name is None, empty, 'UTC', 'Etc/UTC', or 'Z', immediately returns timezone.utc.
    - Tries zoneinfo.ZoneInfo first (full IANA database support including DST transitions).
    - Falls back gracefully to standard offsets if zoneinfo lookup fails on systems without tzdata.
    """
    if not tz_name:
        return timezone.utc

    name_clean = str(tz_name).strip()
    name_lower = name_clean.lower()

    if name_lower in ("utc", "etc/utc", "z", "gmt", "universal"):
        return timezone.utc

    try:
        from zoneinfo import ZoneInfo
        return ZoneInfo(name_clean)
    except Exception:
        pass

    # Robust region fallbacks
    if "kolkata" in name_lower or "calcutta" in name_lower or "ist" in name_lower or "india" in name_lower:
        return timezone(timedelta(hours=5, minutes=30), name="Asia/Kolkata")
    elif "tokyo" in name_lower or "japan" in name_lower or "jst" in name_lower:
        return timezone(timedelta(hours=9), name="Asia/Tokyo")
    elif "singapore" in name_lower or "sgt" in name_lower:
        return timezone(timedelta(hours=8), name="Asia/Singapore")
    elif "london" in name_lower or "bst" in name_lower or "british" in name_lower:
        return timezone(timedelta(0), name="Europe/London")
    elif "paris" in name_lower or "berlin" in name_lower or "cet" in name_lower or "cest" in name_lower or "rome" in name_lower:
        return timezone(timedelta(hours=1), name="Europe/Paris")
    elif "new_york" in name_lower or "est" in name_lower or "edt" in name_lower or "eastern" in name_lower:
        return timezone(timedelta(hours=-5), name="America/New_York")
    elif "los_angeles" in name_lower or "pst" in name_lower or "pdt" in name_lower or "pacific" in name_lower:
        return timezone(timedelta(hours=-8), name="America/Los_Angeles")
    elif "dubai" in name_lower or "gulf" in name_lower:
        return timezone(timedelta(hours=4), name="Asia/Dubai")
    elif "bangkok" in name_lower or "ict" in name_lower or "indochina" in name_lower:
        return timezone(timedelta(hours=7), name="Asia/Bangkok")
    else:
        return timezone.utc


# Standardized Indian Railway / Transit timezone instance
KOLKATA_TZ = get_timezone("Asia/Kolkata")
