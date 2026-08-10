from fastapi import APIRouter, HTTPException
import urllib.request
import json
from app.core.currencies import get_all_currencies, get_currency_info, load_currency_registry

router = APIRouter(prefix="/api/currency", tags=["Currency"])

@router.get("/registry")
def get_currency_registry():
    """Return dataset of 100+ world currencies for frontend dropdowns."""
    return get_all_currencies()

@router.get("/convert")
def convert_currency(from_currency: str, to_currency: str, amount: float):
    try:
        url = f"https://api.exchangerate-api.com/v4/latest/{from_currency.upper()}"
        with urllib.request.urlopen(url, timeout=5) as response:
            data = json.loads(response.read())
        
        rates = data.get("rates", {})
        if to_currency.upper() not in rates:
            raise HTTPException(status_code=400, detail="Target currency not supported")
            
        rate = rates[to_currency.upper()]
        converted_amount = amount * rate
        
        return {
            "from_currency": from_currency.upper(),
            "to_currency": to_currency.upper(),
            "amount": amount,
            "rate": rate,
            "converted_amount": round(converted_amount, 2)
        }
    except Exception:
        raise HTTPException(status_code=503, detail="Currency conversion service unavailable")
