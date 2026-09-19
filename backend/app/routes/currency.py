from fastapi import APIRouter, HTTPException
import urllib.request
import json
from app.core.currencies import get_all_currencies, get_currency_info, load_currency_registry

router = APIRouter(prefix="/api/currency", tags=["Currency"])

@router.get("/registry")
def get_currency_registry():
    """Return dataset of 100+ world currencies for frontend dropdowns."""
    return get_all_currencies()

STATIC_USD_RATES = {
    "USD": 1.0, "EUR": 0.92, "GBP": 0.79, "INR": 83.5, "JPY": 155.0,
    "AUD": 1.52, "CAD": 1.36, "SGD": 1.35, "AED": 3.67, "CHF": 0.90
}

@router.get("/convert")
def convert_currency(from_currency: str, to_currency: str, amount: float):
    from_c = from_currency.upper()
    to_c = to_currency.upper()

    try:
        url = f"https://api.exchangerate-api.com/v4/latest/{from_c}"
        with urllib.request.urlopen(url, timeout=4) as response:
            data = json.loads(response.read())
        
        rates = data.get("rates", {})
        if to_c in rates:
            rate = rates[to_c]
            return {
                "from_currency": from_c,
                "to_currency": to_c,
                "amount": amount,
                "rate": rate,
                "converted_amount": round(amount * rate, 2),
                "source": "Live Exchange Rate API"
            }
    except Exception:
        pass

    # Static Fallback Matrix via USD cross rates
    from_rate_usd = STATIC_USD_RATES.get(from_c, 1.0)
    to_rate_usd = STATIC_USD_RATES.get(to_c, 1.0)
    calc_rate = to_rate_usd / from_rate_usd

    return {
        "from_currency": from_c,
        "to_currency": to_c,
        "amount": amount,
        "rate": round(calc_rate, 4),
        "converted_amount": round(amount * calc_rate, 2),
        "source": "Estimated Fallback Rate Matrix"
    }
