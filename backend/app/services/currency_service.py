"""
currency_service.py — Central Currency Service (v2.7.2)

Responsibilities:
  - Exchange rate fetching with 24-hour in-memory cache
  - Multi-currency conversion (USD base)
  - Budget object construction for API responses
  - Formatted display strings for all 80+ supported currencies

Fallback rates are used if the live API is unavailable.
"""

import logging
import time
from typing import Dict, Optional, Tuple

from app.core.currencies import get_currency_info, get_currency_symbol
from app.utils.currency_formatter import format_currency

logger = logging.getLogger(__name__)

# ─── Comprehensive Fallback Rates (USD base) ─────────────────────────────────
# Updated periodically — used when live API is unavailable
FALLBACK_RATES_USD: Dict[str, float] = {
    "USD": 1.0,
    "INR": 83.5,
    "EUR": 0.92,
    "GBP": 0.79,
    "JPY": 150.0,
    "AUD": 1.52,
    "CAD": 1.37,
    "CHF": 0.89,
    "CNY": 7.25,
    "HKD": 7.82,
    "SGD": 1.34,
    "NZD": 1.63,
    "SEK": 10.5,
    "NOK": 10.6,
    "DKK": 6.88,
    "PLN": 3.98,
    "THB": 35.0,
    "MYR": 4.72,
    "IDR": 15600.0,
    "PHP": 57.0,
    "VND": 24400.0,
    "KRW": 1320.0,
    "ZAR": 18.5,
    "BRL": 5.0,
    "MXN": 17.2,
    "SAR": 3.75,
    "QAR": 3.64,
    "AED": 3.67,
    "KWD": 0.308,
    "OMR": 0.385,
    "BHD": 0.376,
    "EGP": 30.9,
    "TRY": 30.2,
    "RUB": 91.0,
    "ARS": 870.0,
    "CLP": 900.0,
    "COP": 3950.0,
    "PEN": 3.75,
    "CZK": 22.8,
    "HUF": 360.0,
    "RON": 4.58,
    "BGN": 1.80,
    "ILS": 3.73,
    "PKR": 278.0,
    "BDT": 110.0,
    "LKR": 310.0,
    "NPR": 133.0,
    "NGN": 1530.0,
    "KES": 132.0,
    "GHS": 12.8,
    "UGX": 3760.0,
    "ETB": 56.5,
    "MAD": 9.97,
    "DZD": 135.0,
    "TWD": 31.8,
    "ISK": 138.0,
    "UAH": 38.0,
    "RSD": 107.0,
    "GEL": 2.68,
}

# ─── In-Memory Cache ──────────────────────────────────────────────────────────
_rate_cache: Dict[str, float] = {}      # code → rate vs USD
_cache_timestamp: float = 0.0
_CACHE_TTL_SECONDS = 86400              # 24 hours


class CurrencyService:
    """
    Central currency service for WanderWise.
    Converts and formats monetary values for any supported currency.
    """

    # ── Exchange Rate Layer ────────────────────────────────────────────────────

    @staticmethod
    def _get_rates() -> Dict[str, float]:
        """
        Returns USD-base exchange rates.
        Uses live API if reachable within 3s, else falls back to FALLBACK_RATES_USD.
        Caches result for 24 hours.
        """
        global _rate_cache, _cache_timestamp

        now = time.time()
        if _rate_cache and (now - _cache_timestamp) < _CACHE_TTL_SECONDS:
            return _rate_cache

        try:
            import urllib.request
            import json
            url = "https://api.exchangerate-api.com/v4/latest/USD"
            with urllib.request.urlopen(url, timeout=3) as resp:
                data = json.loads(resp.read())
                _rate_cache = data.get("rates", {})
                _cache_timestamp = now
                logger.info(f"Exchange rates refreshed from live API ({len(_rate_cache)} currencies)")
                return _rate_cache
        except Exception as e:
            logger.warning(f"Live exchange rate API unavailable: {e} — using fallback rates")
            _rate_cache = dict(FALLBACK_RATES_USD)
            _cache_timestamp = now
            return _rate_cache

    @staticmethod
    def get_rate(from_currency: str, to_currency: str) -> float:
        """
        Returns conversion rate from `from_currency` → `to_currency`.
        All conversions go via USD as the base.
        """
        f = (from_currency or "USD").upper()
        t = (to_currency or "USD").upper()

        if f == t:
            return 1.0

        rates = CurrencyService._get_rates()

        # Both relative to USD
        rate_f = rates.get(f, FALLBACK_RATES_USD.get(f, 1.0))
        rate_t = rates.get(t, FALLBACK_RATES_USD.get(t, 1.0))

        if rate_f == 0:
            return 1.0

        return rate_t / rate_f

    # ── Conversion ────────────────────────────────────────────────────────────

    @staticmethod
    def convert(amount: float, from_currency: str = "USD", to_currency: str = "USD") -> float:
        """Convert amount from one currency to another."""
        if not amount or amount == 0:
            return 0.0
        rate = CurrencyService.get_rate(from_currency, to_currency)
        return round(amount * rate, 2)

    # ── Formatting ────────────────────────────────────────────────────────────

    @staticmethod
    def format(amount: float, currency: str = "USD") -> str:
        """Format amount as a currency string using the registry."""
        return format_currency(amount, currency)

    # ── Budget Object Builder ─────────────────────────────────────────────────

    @staticmethod
    def build_budget_object(
        base_amount_usd: float,
        user_currency: str = "USD",
        base_currency: str = "USD",
    ) -> Dict:
        """
        Build the standardized budget object for API responses.

        Returns:
        {
            "amount": 700,
            "base_currency": "USD",
            "user_currency": "INR",
            "converted_amount": 58450,
            "formatted": "₹58,450"
        }
        """
        user_currency = (user_currency or "USD").upper()
        base_currency = (base_currency or "USD").upper()

        converted = CurrencyService.convert(base_amount_usd, base_currency, user_currency)
        formatted = CurrencyService.format(converted, user_currency)

        return {
            "amount": base_amount_usd,
            "base_currency": base_currency,
            "user_currency": user_currency,
            "converted_amount": converted,
            "formatted": formatted,
        }

    # ── Validation ────────────────────────────────────────────────────────────

    @staticmethod
    def is_valid_currency(code: str) -> bool:
        """Returns True if the currency code is in the registry."""
        if not code:
            return False
        info = get_currency_info(code.upper())
        return info.code.upper() == code.upper()

    @staticmethod
    def normalize_currency_code(raw: str) -> str:
        """
        Normalize a currency string like 'USD ($)' or 'inr' → 'USD' / 'INR'.
        Strips symbols, parenthetical text, and uppercases.
        """
        if not raw:
            return "USD"
        code = raw.strip().split(" ")[0].strip().upper()
        if len(code) == 3:
            return code
        return "USD"


# Module-level convenience functions
def convert_budget(amount_usd: float, user_currency: str) -> Dict:
    """Shorthand to build a budget object from a USD amount."""
    return CurrencyService.build_budget_object(amount_usd, user_currency, "USD")


def format_for_user(amount_usd: float, user_currency: str) -> str:
    """Shorthand to get formatted string in user's currency."""
    converted = CurrencyService.convert(amount_usd, "USD", user_currency)
    return CurrencyService.format(converted, user_currency)
