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
    elif "thimphu" in name_lower or "bhutan" in name_lower or "btt" in name_lower:
        return timezone(timedelta(hours=6), name="Asia/Thimphu")
    elif "tokyo" in name_lower or "japan" in name_lower or "jst" in name_lower:
        return timezone(timedelta(hours=9), name="Asia/Tokyo")
    elif "singapore" in name_lower or "sgt" in name_lower:
        return timezone(timedelta(hours=8), name="Asia/Singapore")
    elif "sydney" in name_lower or "aest" in name_lower or "australia/sydney" in name_lower:
        return timezone(timedelta(hours=10), name="Australia/Sydney")
    elif "auckland" in name_lower or "nzst" in name_lower or "new_zealand" in name_lower:
        return timezone(timedelta(hours=12), name="Pacific/Auckland")
    elif "zurich" in name_lower or "switzerland" in name_lower:
        return timezone(timedelta(hours=1), name="Europe/Zurich")
    elif "cairo" in name_lower or "egypt" in name_lower:
        return timezone(timedelta(hours=2), name="Africa/Cairo")
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


def format_datetime_with_tz(dt: Optional[datetime], tz_name: Optional[str] = None) -> Optional[str]:
    """
    Formats a datetime object with 12-hour AM/PM and its authentic local timezone abbreviation.
    Example outputs: '3:50 PM IST', '4:20 PM +06', '7:00 PM JST'.
    """
    if not dt:
        return None
    time_str = dt.strftime("%I:%M %p").lstrip("0")
    tz_abbr = dt.tzname()
    if not tz_abbr and tz_name:
        tz_abbr = tz_name.split("/")[-1].replace("_", " ")
    if tz_abbr:
        return f"{time_str} {tz_abbr}".strip()
    return time_str
