from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from app.core.currencies import get_all_currencies, get_currency_info, load_currency_registry
from app.services.currency_service import CurrencyService
from app.core.budget_tiers import get_budget_tiers_for_currency, interpret_budget
from app.services.budget_allocation_service import BudgetAllocationService

router = APIRouter(prefix="/api/currency", tags=["Currency"])

@router.get("/registry")
def get_currency_registry():
    """Return dataset of 100+ world currencies for frontend dropdowns."""
    return get_all_currencies()


@router.get("/budget-tiers")
def get_budget_tiers(currency: str = Query("USD", description="Target currency code")):
    """
    Return currency-aware daily budget range tiers for registration, settings, and itinerary forms.
    Thresholds are converted from base USD using real exchange rates.
    """
    tiers = get_budget_tiers_for_currency(currency)
    return {
        "currency": currency.upper(),
        "tiers": tiers
    }


@router.get("/budget-allocation")
def get_budget_allocation(
    budget: float = Query(150000.0, description="Total user trip budget"),
    currency: str = Query("INR", description="Currency code"),
    tier: str = Query("Budget", description="Budget tier: Budget, Mid-range, Luxury, Ultra Luxury"),
    destination: str = Query("Bolivia", description="Destination"),
    origin_city: str = Query("Coimbatore", description="Origin city"),
    days: int = Query(5, ge=1, description="Number of days"),
    adults: int = Query(1, ge=1, description="Adult count"),
    children: int = Query(0, ge=0, description="Child count"),
    travel_style: Optional[str] = Query(None, description="Travel style: family, solo, couple, friends, etc."),
    transport_mode: str = Query("Mixed Transport", description="Transport mode"),
    accommodation_preference: str = Query("hotel", description="Accommodation preference")
):
    """
    Centralized API providing explainable, testable door-to-door financial breakdown
    for any comfort tier and destination.
    """
    resolved_travel_style = travel_style or ("family" if children > 0 else "solo")
    return BudgetAllocationService.calculate_plan(
        total_budget=budget,
        currency=currency,
        tier=tier,
        destination=destination,
        origin_city=origin_city,
        days=days,
        adults=adults,
        children=children,
        travel_style=resolved_travel_style,
        transport_mode=transport_mode,
        accommodation_preference=accommodation_preference
    )


@router.get("/interpret-budget")
def interpret_budget_endpoint(
    tier: str = Query("mid_range", description="Budget tier key or legacy string"),
    currency: str = Query("USD", description="Currency code"),
    days: int = Query(1, ge=1, description="Number of days"),
    total_budget: Optional[float] = Query(None, description="Optional total budget"),
    destination: str = Query("", description="Optional destination"),
    origin_city: str = Query("Coimbatore", description="Origin city")
):
    """
    Return detailed monetary interpretation of a budget tier in the selected currency.
    """
    return interpret_budget(
        tier,
        currency=currency,
        days=days,
        total_budget=total_budget,
        destination=destination,
        origin_city=origin_city
    )


@router.get("/convert")
def convert_currency(from_currency: str, to_currency: str, amount: float):
    """
    Convert amount from one currency to another using CurrencyService with 24h caching.
    """
    from_c = (from_currency or "USD").strip().upper()
    to_c = (to_currency or "USD").strip().upper()

    rate = CurrencyService.get_rate(from_c, to_c)
    converted_amount = CurrencyService.convert(amount, from_c, to_c)

    return {
        "from_currency": from_c,
        "to_currency": to_c,
        "amount": amount,
        "rate": rate,
        "converted_amount": converted_amount,
        "formatted": CurrencyService.format(converted_amount, to_c),
        "source": "WanderWise Central Currency Engine"
    }
