import time
from typing import Any, Optional

class TransitCache:
    """30-Minute In-Memory TTL Cache for transit telemetry and API calls."""
    _cache = {}
    _ttl_seconds = 1800  # 30 minutes

    @classmethod
    def get(cls, key: str) -> Optional[Any]:
        if key in cls._cache:
            entry = cls._cache[key]
            if time.time() - entry["timestamp"] < cls._ttl_seconds:
                return entry["value"]
            else:
                del cls._cache[key]
        return None

    @classmethod
    def set(cls, key: str, value: Any):
        cls._cache[key] = {
            "timestamp": time.time(),
            "value": value
        }

    @classmethod
    def clear(cls):
        cls._cache.clear()
