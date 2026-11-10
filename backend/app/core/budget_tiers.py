"""
budget_tiers.py — Canonical Budget Tiers & Currency-Aware Interpretation
Provides centralized budget models, stable tier keys, exchange-rate conversion,
and AI prompt constraints.
"""

from typing import Dict, Any, List, Optional
from app.services.currency_service import CurrencyService
from app.core.currencies import get_currency_info, get_currency_symbol
from app.utils.currency_formatter import format_currency

# Canonical daily thresholds in USD (Base currency)
CANONICAL_TIERS = {
    "budget": {
        "key": "budget",
        "name": "Budget",
        "min_usd": 0.0,
        "max_usd": 50.0,
        "typical_usd": 40.0,
    },
    "mid_range": {
        "key": "mid_range",
        "name": "Mid-range",
        "min_usd": 50.0,
        "max_usd": 180.0,
        "typical_usd": 110.0,
    },
    "luxury": {
        "key": "luxury",
        "name": "Luxury",
        "min_usd": 180.0,
        "max_usd": 450.0,
        "typical_usd": 280.0,
    },
    "ultra_luxury": {
        "key": "ultra_luxury",
        "name": "Ultra Luxury",
        "min_usd": 450.0,
        "max_usd": None,
        "typical_usd": 650.0,
    },
}

# Legacy string mapping to stable keys
LEGACY_MAPPING = {
    "budget (<$50/day)": "budget",
    "budget": "budget",
    "mid-range ($50–150/day)": "mid_range",
    "mid-range ($50-150/day)": "mid_range",
    "mid-range": "mid_range",
    "mid_range": "mid_range",
    "comfort ($150–350/day)": "mid_range",
    "comfort ($150-350/day)": "mid_range",
    "comfort": "mid_range",
    "luxury ($350+/day)": "luxury",
    "luxury": "luxury",
    "ultra luxury": "ultra_luxury",
    "ultra-luxury": "ultra_luxury",
    "ultra_luxury": "ultra_luxury",
}


def normalize_budget_tier(raw_val: Optional[str]) -> str:
    """Normalize any budget string to a stable key: 'budget', 'mid_range', 'luxury', 'ultra_luxury'."""
    if not raw_val:
        return "mid_range"
    clean = str(raw_val).strip().lower()
    if clean in LEGACY_MAPPING:
        return LEGACY_MAPPING[clean]
    for pattern, key in LEGACY_MAPPING.items():
        if pattern in clean:
            return key
    return "mid_range"


def _round_clean(amount: float, currency: str) -> float:
    """Round monetary amount cleanly for display."""
    curr = currency.upper()
    if curr in ["INR", "JPY", "KRW", "IDR", "VND", "HUF", "CLP"]:
        if amount > 5000:
            return round(amount / 500) * 500
        elif amount > 500:
            return round(amount / 100) * 100
        else:
            return round(amount / 10) * 10
    else:
        if amount > 500:
            return round(amount / 50) * 50
        elif amount > 50:
            return round(amount / 5) * 5
        else:
            return round(amount)


def get_budget_tiers_for_currency(currency: str = "USD") -> List[Dict[str, Any]]:
    """
    Generate currency-aware budget tiers converted using applicable exchange rates.
    Returns clean labels, e.g. for INR: 'Budget (<₹4,200/day)', 'Mid-range (₹4,200–15,000/day)', etc.
    """
    curr = (currency or "USD").upper()
    rate = CurrencyService.get_rate("USD", curr)
    sym = get_currency_symbol(curr)

    tiers = []
    # 1. Budget (<$50)
    b_max = _round_clean(50.0 * rate, curr)
    b_fmt = format_currency(b_max, curr)
    tiers.append({
        "key": "budget",
        "name": "Budget",
        "label": f"Budget (<{b_fmt}/day)",
        "min_daily": 0.0,
        "max_daily": b_max,
        "currency": curr,
        "symbol": sym,
    })

    # 2. Mid-range ($50-180)
    m_min = b_max
    m_max = _round_clean(180.0 * rate, curr)
    m_fmt_min = format_currency(m_min, curr)
    m_fmt_max = format_currency(m_max, curr)
    tiers.append({
        "key": "mid_range",
        "name": "Mid-range",
        "label": f"Mid-range ({m_fmt_min}–{m_fmt_max}/day)",
        "min_daily": m_min,
        "max_daily": m_max,
        "currency": curr,
        "symbol": sym,
    })

    # 3. Luxury ($180-450)
    l_min = m_max
    l_max = _round_clean(450.0 * rate, curr)
    l_fmt_min = format_currency(l_min, curr)
    l_fmt_max = format_currency(l_max, curr)
    tiers.append({
        "key": "luxury",
        "name": "Luxury",
        "label": f"Luxury ({l_fmt_min}–{l_fmt_max}/day)",
        "min_daily": l_min,
        "max_daily": l_max,
        "currency": curr,
        "symbol": sym,
    })

    # 4. Ultra Luxury ($450+)
    ul_min = l_max
    ul_fmt_min = format_currency(ul_min, curr)
    tiers.append({
        "key": "ultra_luxury",
        "name": "Ultra Luxury",
        "label": f"Ultra Luxury ({ul_fmt_min}+/day)",
        "min_daily": ul_min,
        "max_daily": None,
        "currency": curr,
        "symbol": sym,
    })

    return tiers


def interpret_budget(
    tier_raw: Optional[str],
    currency: str = "USD",
    days: int = 1,
    total_budget: Optional[float] = None,
    destination: str = "",
    origin_city: str = "Coimbatore"
) -> Dict[str, Any]:
    """
    Interpret budget tier into monetary constraints for both the UI and AI planner.
    """
    from app.services.budget_allocation_service import BudgetAllocationService

    tier_key = normalize_budget_tier(tier_raw)
    curr = (currency or "USD").upper()
    rate = CurrencyService.get_rate("USD", curr)
    days_count = max(1, days)

    base = CANONICAL_TIERS.get(tier_key, CANONICAL_TIERS["mid_range"])
    min_daily = round(base["min_usd"] * rate, 2)
    max_daily = round(base["max_usd"] * rate, 2) if base["max_usd"] else None
    typical_daily = round(base["typical_usd"] * rate, 2)

    total_est = round(typical_daily * days_count, 2)
    effective_budget = total_budget if (total_budget and total_budget > 0) else total_est

    # Door-to-door full breakdown
    door_to_door = BudgetAllocationService.calculate_plan(
        total_budget=effective_budget,
        currency=curr,
        tier=tier_key,
        destination=destination,
        origin_city=origin_city,
        days=days_count
    )

    return {
        "tier_key": tier_key,
        "tier_name": base["name"],
        "currency": curr,
        "symbol": get_currency_symbol(curr),
        "rate_vs_usd": rate,
        "min_daily": min_daily,
        "max_daily": max_daily,
        "typical_daily": typical_daily,
        "total_estimated": total_est,
        "days": days_count,
        "formatted_daily": f"{format_currency(min_daily, curr)} - {format_currency(max_daily, curr)}/day" if max_daily else f"{format_currency(min_daily, curr)}+/day",
        "formatted_total": format_currency(total_est, curr),
        "door_to_door": door_to_door,
    }
