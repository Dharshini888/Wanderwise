"""
canonical_pricing_registry.py — Canonical Trip-Wide Attraction & Dining Pricing Registry

Enforces a single consistent pricing record per attraction across the entire trip:
1. Normalizes place names and business identities into stable entity keys.
2. Maintains consistent adult, child, and family/group ticket prices.
3. Distinguishes admission tickets from food, transport, and rentals.
4. Restaurant and dining visits are strictly 0 admission ticket price (a la carte dining).
5. Paid attractions are never labeled "Free Entry"; unknown prices display "Price unavailable".
6. Prevents arbitrary price inflation or differing prices for the same venue on different days.
"""

import re
from typing import Dict, Any, Optional, Tuple
from app.services.currency_service import CurrencyService

STOP_ENTITY_WORDS = {
    "temple", "shrine", "observatory", "observation", "deck", "tower", "park",
    "garden", "gardens", "national", "museum", "historic", "historical", "site",
    "palace", "citadel", "castle", "cathedral", "church", "mosque", "basilica",
    "aquarium", "zoo", "market", "bazaar", "crossing", "street", "district",
    "quarter", "alley", "lake", "falls", "waterfall", "beach", "cliff", "ridge",
    "walkway", "lookout", "viewpoint", "view", "monument", "memorial",
    "visit", "explore", "exploring", "experience", "dining", "dinner", "lunch",
    "breakfast", "cafe", "restaurant", "ramen", "bar", "grill", "bistro", "eatery",
    "at", "the", "in", "of", "and", "&"
}


def normalize_place_entity_key(name: str) -> str:
    """
    Extract a normalized, noise-free entity key from an attraction or restaurant name.
    Examples:
      - "Senso-ji Temple" -> "sensoji"
      - "Tokyo Skytree Observatory" -> "tokyoskytree"
      - "Meiji Jingu Shrine" -> "meijijingu"
      - "Shibuya Sky Observation Deck" -> "shibuyasky"
      - "Ichiran Ramen Asakusa" -> "ichiran"
    """
    if not name:
        return ""
    clean = name.lower()
    clean = re.sub(r'[\(\)\[\]\{\}\-\–\—\:\,\.\/\'\"]', ' ', clean)
    tokens = clean.split()
    meaningful = [t for t in tokens if t not in STOP_ENTITY_WORDS and len(t) > 1]
    if meaningful:
        key = "".join(meaningful)
    else:
        key = re.sub(r'[^a-z0-9]', '', clean)
    return key if len(key) >= 3 else re.sub(r'[^a-z0-9]', '', clean)


class PricingRecord(dict):
    """
    Dict subclass providing both dictionary access and property attribute access.
    """
    def __init__(self, data: Dict[str, Any]):
        super().__init__(data)
        self.__dict__.update(data)

    @property
    def adult_price(self) -> Optional[float]:
        return self.get("ticket_price_adult")

    @property
    def child_price(self) -> Optional[float]:
        return self.get("ticket_price_child")

    @property
    def family_price(self) -> Optional[float]:
        return self.get("ticket_price_family")

    @property
    def price_status(self) -> str:
        return self.get("price_status", "Price unavailable")

    @property
    def is_free(self) -> bool:
        return bool(self.get("is_free_entry"))

    @property
    def is_dining(self) -> bool:
        return bool(self.get("is_dining"))

    def to_dict(self) -> Dict[str, Any]:
        return dict(self)


class CanonicalPricingRegistry:
    """
    Trip-level pricing registry maintaining single-source-of-truth pricing records.
    """

    def __init__(self, target_currency: str = "USD"):
        self.target_currency = (target_currency or "USD").upper()
        self._registry: Dict[str, PricingRecord] = {}

    def register(
        self,
        name: Optional[str] = None,
        category: str = "Sightseeing",
        ticket_price_adult: Optional[float] = None,
        ticket_price_child: Optional[float] = None,
        is_dining: bool = False,
        source_currency: Optional[str] = None,
        is_known_free: bool = False,
        meal_cost_est: Optional[float] = None,
        place_name: Optional[str] = None,
        raw_price: Optional[float] = None,
        currency: Optional[str] = None
    ) -> PricingRecord:
        """
        Register or look up a canonical pricing record for a venue.
        If already registered, preserves the first validated baseline.
        """
        venue_name = name or place_name or ""
        key = normalize_place_entity_key(venue_name)
        if not key:
            key = re.sub(r'[^a-z0-9]', '', venue_name.lower())

        if key in self._registry:
            return self._registry[key]

        source_curr = (source_currency or currency or self.target_currency).upper()
        clean_cat = (category or "Sightseeing").strip().lower()
        
        is_dining_venue = (
            is_dining
            or any(d in clean_cat for d in ["dining", "restaurant", "cafe", "food", "bar", "bistro", "eatery"])
            or any(d in venue_name.lower() for d in ["ramen", "restaurant", "cafe", "dining", "bar & grill", "bakery"])
        )

        effective_adult_price = ticket_price_adult if ticket_price_adult is not None else raw_price

        if is_dining_venue:
            # Dining venues: admission ticket is strictly 0.0; meal cost is separate
            adult_price = 0.0
            child_price = 0.0
            family_price = 0.0
            price_status = "A la carte dining (No entry ticket)"
            is_free = False
            effective_meal_cost = meal_cost_est if meal_cost_est is not None else 25.0
            if source_curr != self.target_currency:
                effective_meal_cost = round(CurrencyService.convert(effective_meal_cost, source_curr, self.target_currency), 2)
        elif is_known_free or (effective_adult_price is not None and float(effective_adult_price) == 0.0 and ("park" in clean_cat or "shrine" in clean_cat or "temple" in clean_cat or "beach" in clean_cat or "walk" in clean_cat or "square" in clean_cat or "quarter" in clean_cat)):
            adult_price = 0.0
            child_price = 0.0
            family_price = 0.0
            price_status = "Free Entry"
            is_free = True
            effective_meal_cost = None
        elif effective_adult_price is not None and float(effective_adult_price) > 0.0:
            raw_adult = float(effective_adult_price)
            if source_curr != self.target_currency:
                adult_price = round(CurrencyService.convert(raw_adult, source_curr, self.target_currency), 2)
            else:
                adult_price = round(raw_adult, 2)

            if ticket_price_child is not None and float(ticket_price_child) >= 0:
                raw_child = float(ticket_price_child)
                if source_curr != self.target_currency:
                    child_price = round(CurrencyService.convert(raw_child, source_curr, self.target_currency), 2)
                else:
                    child_price = round(raw_child, 2)
            else:
                child_price = round(adult_price * 0.50, 2)

            family_price = round(adult_price * 2 + child_price * 2 * 0.85, 2)
            price_status = "Paid admission"
            is_free = False
            effective_meal_cost = None
        elif effective_adult_price is not None and float(effective_adult_price) == 0.0:
            adult_price = 0.0
            child_price = 0.0
            family_price = 0.0
            price_status = "Free Entry"
            is_free = True
            effective_meal_cost = None
        else:
            # Price unknown/unverified: never claim Free Entry; use Price unavailable
            adult_price = None
            child_price = None
            family_price = None
            price_status = "Price unavailable"
            is_free = False
            effective_meal_cost = None

        record_data = {
            "entity_key": key,
            "name": venue_name,
            "category": "Dining" if is_dining_venue else category,
            "is_dining": is_dining_venue,
            "ticket_price_adult": adult_price,
            "ticket_price_child": child_price,
            "ticket_price_family": family_price,
            "ticket_price": adult_price if adult_price is not None else 0.0,
            "source_currency": source_curr,
            "display_currency": self.target_currency,
            "price_status": price_status,
            "is_free_entry": is_free,
            "meal_cost": effective_meal_cost,
        }
        record = PricingRecord(record_data)
        self._registry[key] = record
        return record

    def get(self, name: str) -> Optional[Dict[str, Any]]:
        key = normalize_place_entity_key(name)
        return self._registry.get(key)

    def reconcile_activity(self, act: Dict[str, Any]) -> Dict[str, Any]:
        """
        Reconcile an activity dictionary with the canonical pricing record.
        Ensures consistent pricing across multi-day references.
        """
        place = act.get("place") if isinstance(act.get("place"), dict) else {}
        p_name = place.get("name") or act.get("place_name") or act.get("title") or ""
        p_cat = place.get("category") or act.get("category") or "Sightseeing"
        is_din = act.get("is_dining") or act.get("activity_type") == "meal" or "restaurant" in p_cat.lower() or "cafe" in p_cat.lower()

        raw_price = act.get("ticket_price")
        if raw_price is None and place.get("ticket_price") is not None:
            raw_price = place.get("ticket_price")

        source_curr = act.get("currency") or place.get("currency") or self.target_currency
        meal_cost = act.get("meal_cost") or place.get("meal_cost")

        rec = self.register(
            name=p_name,
            category=p_cat,
            ticket_price_adult=raw_price if raw_price is not None else None,
            ticket_price_child=act.get("ticket_price_child"),
            is_dining=is_din,
            source_currency=source_curr,
            meal_cost_est=meal_cost
        )

        act["ticket_price"] = rec["ticket_price"]
        act["ticket_price_adult"] = rec["ticket_price_adult"]
        act["ticket_price_child"] = rec["ticket_price_child"]
        act["price_status"] = rec["price_status"]
        act["is_free_entry"] = rec["is_free_entry"]
        act["currency"] = self.target_currency
        if rec["is_dining"]:
            act["activity_type"] = "meal"
            act["is_dining"] = True
            act["ticket_price"] = 0.0
            if rec.get("meal_cost"):
                act["meal_cost"] = rec["meal_cost"]
        return act
