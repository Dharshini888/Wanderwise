import os
import json
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

class CurrencyInfo(BaseModel):
    code: str
    symbol: str
    name: str
    country: str
    decimal_places: int = 2
    locale: str = "en-US"
    minor_unit: Optional[str] = "Cent"
    exchange_rate_supported: bool = True

_CURRENCY_REGISTRY: Dict[str, CurrencyInfo] = {}

def load_currency_registry() -> Dict[str, CurrencyInfo]:
    """Load currency dataset from currencies.json into memory."""
    global _CURRENCY_REGISTRY
    if _CURRENCY_REGISTRY:
        return _CURRENCY_REGISTRY
    
    data_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "currencies.json")
    if os.path.exists(data_path):
        with open(data_path, "r", encoding="utf-8") as f:
            raw_list = json.load(f)
            for item in raw_list:
                info = CurrencyInfo(**item)
                _CURRENCY_REGISTRY[info.code.upper()] = info

    # Fallback minimal USD / INR if file loading fails
    if "USD" not in _CURRENCY_REGISTRY:
        _CURRENCY_REGISTRY["USD"] = CurrencyInfo(code="USD", symbol="$", name="US Dollar", country="United States", decimal_places=2, locale="en-US")
    if "INR" not in _CURRENCY_REGISTRY:
        _CURRENCY_REGISTRY["INR"] = CurrencyInfo(code="INR", symbol="₹", name="Indian Rupee", country="India", decimal_places=2, locale="en-IN")

    return _CURRENCY_REGISTRY

def get_currency_info(code: str) -> CurrencyInfo:
    """Retrieve CurrencyInfo for code. Defaults to USD if code not found."""
    registry = load_currency_registry()
    clean_code = (code or "USD").strip().upper()
    return registry.get(clean_code, registry.get("USD"))

def get_currency_symbol(code: str) -> str:
    """Get currency symbol for code."""
    return get_currency_info(code).symbol

def get_all_currencies() -> List[Dict[str, Any]]:
    """Get list of all currency dicts for registry endpoint."""
    registry = load_currency_registry()
    return [c.model_dump() for c in registry.values()]
