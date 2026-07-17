from fastapi import APIRouter, HTTPException
import urllib.request
import json

router = APIRouter(prefix="/api/currency", tags=["Currency"])

@router.get("/convert")
def convert_currency(from_curr: str, to_curr: str, amount: float):
    try:
        url = f"https://api.exchangerate-api.com/v4/latest/{from_curr.upper()}"
        with urllib.request.urlopen(url, timeout=5) as response:
            data = json.loads(response.read())
        
        rates = data.get("rates", {})
        if to_curr.upper() not in rates:
            raise HTTPException(status_code=400, detail="Target currency not supported")
            
        rate = rates[to_curr.upper()]
        converted_amount = amount * rate
        
        return {
            "from_curr": from_curr.upper(),
            "to_curr": to_curr.upper(),
            "amount": amount,
            "rate": rate,
            "converted_amount": converted_amount
        }
    except Exception as e:
        # Fallback offline mock rates
        fallback_rates = {"USD": 1.0, "EUR": 0.92, "GBP": 0.79, "INR": 83.0, "JPY": 150.0, "AUD": 1.5, "CAD": 1.3}
        f = from_curr.upper()
        t = to_curr.upper()
        if f in fallback_rates and t in fallback_rates:
            rate = fallback_rates[t] / fallback_rates[f]
            return {
                "from_curr": f,
                "to_curr": t,
                "amount": amount,
                "rate": rate,
                "converted_amount": amount * rate
            }
        raise HTTPException(status_code=500, detail="Currency conversion failed and fallback not available")
