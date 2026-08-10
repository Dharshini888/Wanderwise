import requests
from typing import Dict, Any
from ..cache.transit_cache import TransitCache

def get_exchange_rate(from_currency: str = "USD", to_currency: str = "INR") -> float:
    """
    Fetches real-time exchange rates from Frankfurter API (100% free, no key).
    """
    from_c = (from_currency or "USD").upper()
    to_c = (to_currency or "INR").upper()

    if from_c == to_c:
        return 1.0

    cache_key = f"rate_{from_c}_{to_c}"
    cached = TransitCache.get(cache_key)
    if cached:
        return cached

    try:
        url = f"https://api.frankfurter.app/latest?from={from_c}&to={to_c}"
        resp = requests.get(url, timeout=2.5)
        if resp.status_code == 200:
            data = resp.json()
            rate = float(data.get("rates", {}).get(to_c, 1.0))
            TransitCache.set(cache_key, rate)
            return rate
    except Exception:
        pass

    # Static fallback rate
    fallback_rate = 83.5 if (from_c == "USD" and to_c == "INR") else 1.0
    TransitCache.set(cache_key, fallback_rate)
    return fallback_rate
