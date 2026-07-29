from typing import Optional, Any
from app.core.currencies import get_currency_info


def format_currency(amount: Optional[float], currency_code: str = "USD") -> str:
    """
    Format numeric cost according to currency registry metadata.
    Returns clean formatted string e.g. '₹350', '€40', '¥1,200'.
    """
    if amount is None:
        amount = 0.0
    
    info = get_currency_info(currency_code)
    decimals = info.decimal_places
    symbol = info.symbol
    
    if decimals == 0:
        formatted_num = f"{int(round(amount)):,}"
    else:
        formatted_num = f"{amount:,.{decimals}f}"
        
        # Clean trailing .00 if whole number
        if formatted_num.endswith(".00"):
            formatted_num = formatted_num[:-3]
            
    return f"{symbol}{formatted_num}"

def parse_currency(val: Any) -> float:
    """Extract numeric value from currency string or number."""
    if val is None:
        return 0.0
    if isinstance(val, (int, float)):
        return float(val)
    
    val_str = str(val).strip()
    import re
    cleaned = re.sub(r"[^\d.]", "", val_str)
    try:
        return float(cleaned)
    except Exception:
        return 0.0
