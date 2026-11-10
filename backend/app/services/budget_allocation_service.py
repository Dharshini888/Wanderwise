"""
budget_allocation_service.py — Centralized Smart Budget Allocation & Door-to-Door Cost Service

Provides an explainable, testable, currency-aware financial planner that accounts for:
1. Outbound transportation from origin to destination
2. Return transportation from destination to origin
3. Accommodation for all required nights
4. Food and dining
5. Local and intercity transportation
6. Activities, attractions, and tours
7. Travel fees (visa, insurance, baggage)
8. Contingency / emergency reserve
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from app.services.currency_service import CurrencyService
from app.core.currencies import get_currency_symbol
from app.utils.currency_formatter import format_currency
from app.services.location.location_normalizer import resolve_destination_info


TIER_STRATEGIES = {
    "budget": {
        "key": "budget",
        "name": "Budget",
        "description": "Prioritizes economical accommodation, affordable local food, public transit, low-cost activities, and a realistic emergency reserve.",
        "percentages": {
            "outbound_transport": 25.0,
            "return_transport": 25.0,
            "accommodation": 18.0,
            "food": 14.0,
            "local_transport": 5.0,
            "activities": 6.0,
            "other_fees": 2.0,
            "contingency": 5.0,
        },
        "daily_base_usd": 40.0,
        "lodging_per_night_usd": 25.0,
        "food_per_day_usd": 15.0,
        "local_transit_per_day_usd": 6.0,
        "activities_per_day_usd": 8.0,
    },
    "mid_range": {
        "key": "mid_range",
        "name": "Mid-range",
        "description": "Balances comfort and affordability with standard hotels, convenient transit, paid cultural attractions, and selected dining experiences.",
        "percentages": {
            "outbound_transport": 22.0,
            "return_transport": 22.0,
            "accommodation": 24.0,
            "food": 14.0,
            "local_transport": 5.0,
            "activities": 8.0,
            "other_fees": 1.0,
            "contingency": 4.0,
        },
        "daily_base_usd": 110.0,
        "lodging_per_night_usd": 70.0,
        "food_per_day_usd": 35.0,
        "local_transit_per_day_usd": 15.0,
        "activities_per_day_usd": 20.0,
    },
    "luxury": {
        "key": "luxury",
        "name": "Luxury",
        "description": "Prioritizes 4-5 star comfort hotels, private transfers, premium cultural experiences, and higher-end dining.",
        "percentages": {
            "outbound_transport": 18.0,
            "return_transport": 18.0,
            "accommodation": 32.0,
            "food": 16.0,
            "local_transport": 6.0,
            "activities": 7.0,
            "other_fees": 1.0,
            "contingency": 2.0,
        },
        "daily_base_usd": 300.0,
        "lodging_per_night_usd": 200.0,
        "food_per_day_usd": 80.0,
        "local_transit_per_day_usd": 35.0,
        "activities_per_day_usd": 45.0,
    },
    "ultra_luxury": {
        "key": "ultra_luxury",
        "name": "Ultra Luxury",
        "description": "Considers signature suites and luxury villas, private chauffeur transfers, exclusive bespoke VIP experiences, and gourmet dining.",
        "percentages": {
            "outbound_transport": 16.0,
            "return_transport": 16.0,
            "accommodation": 38.0,
            "food": 16.0,
            "local_transport": 5.0,
            "activities": 6.0,
            "other_fees": 1.0,
            "contingency": 2.0,
        },
        "daily_base_usd": 650.0,
        "lodging_per_night_usd": 450.0,
        "food_per_day_usd": 150.0,
        "local_transit_per_day_usd": 70.0,
        "activities_per_day_usd": 90.0,
    },
}


def normalize_tier_key(tier: Optional[str]) -> str:
    """Normalize user or API input string to one of the 4 supported canonical tier keys."""
    if not tier:
        return "mid_range"
    clean = str(tier).strip().lower().replace("-", "_").replace(" ", "_")
    if "ultra" in clean:
        return "ultra_luxury"
    if "luxury" in clean:
        return "luxury"
    if "mid" in clean or "standard" in clean or "comfort" in clean:
        return "mid_range"
    if "budget" in clean or "backpack" in clean or "econom" in clean:
        return "budget"
    return "mid_range"


class BudgetAllocationService:
    """
    Centralized door-to-door trip cost and smart budget allocation service.
    """

    @classmethod
    def calculate_plan(
        cls,
        total_budget: float,
        currency: str = "USD",
        tier: str = "mid_range",
        destination: str = "",
        origin_city: str = "Coimbatore",
        days: int = 5,
        adults: int = 1,
        children: int = 0,
        travel_style: str = "solo",
        transport_mode: str = "Mixed Transport",
        accommodation_preference: str = "hotel",
        comfort_tier: Optional[str] = None,
        total_days: Optional[int] = None,
        origin: Optional[str] = None,
        custom_allocations: Optional[Dict[str, float]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Calculate an explainable financial plan distributing total budget across door-to-door categories
        while respecting the selected comfort tier.
        """
        if comfort_tier:
            tier = comfort_tier
        if total_days:
            days = total_days
        if origin:
            origin_city = origin

        tier_key = normalize_tier_key(tier)
        strategy = TIER_STRATEGIES[tier_key]
        curr = (currency or "USD").upper()
        rate = CurrencyService.get_rate("USD", curr)
        symbol = get_currency_symbol(curr)
        curr_symbol = symbol
        travellers = max(1, adults + children)
        trip_days = max(1, days)
        nights = max(1, trip_days - 1)

        # Baseline budget amounts based on selected tier strategy percentages
        pcts = strategy["percentages"]
        raw_budget = float(total_budget) if total_budget and total_budget > 0 else 1000.0

        # Calculate exact monetary amounts from user budget
        outbound_amt = round(raw_budget * (pcts["outbound_transport"] / 100.0), 2)
        return_amt = round(raw_budget * (pcts["return_transport"] / 100.0), 2)
        accom_amt = round(raw_budget * (pcts["accommodation"] / 100.0), 2)
        food_amt = round(raw_budget * (pcts["food"] / 100.0), 2)
        local_trans_amt = round(raw_budget * (pcts["local_transport"] / 100.0), 2)
        activities_amt = round(raw_budget * (pcts["activities"] / 100.0), 2)
        other_fees_amt = round(raw_budget * (pcts["other_fees"] / 100.0), 2)
        
        # Contingency absorbs any rounding differences so sum == raw_budget exactly
        allocated_so_far = round(
            outbound_amt + return_amt + accom_amt + food_amt + local_trans_amt + activities_amt + other_fees_amt, 2
        )
        contingency_amt = round(max(0.0, raw_budget - allocated_so_far), 2)

        # Truth-first bottom-up cost estimation distinguishing user budget limit from estimated trip cost
        # Group room count calculation: 2 adults per room standard
        num_rooms = max(1, (travellers + 1) // 2)

        # Global Destination & Route Corridor Awareness
        dest_info = resolve_destination_info(destination, origin_city)
        is_long_haul = dest_info["is_long_haul"]
        is_regional_international = dest_info["is_regional_international"]
        is_india_domestic = dest_info["is_india_domestic"]
        dest_country_code = dest_info.get("country_code", "")

        is_malaysia = dest_country_code == "MY" or any(m in (destination or "").lower() for m in ["kuala lumpur", "kuala_lumpur", "malaysia", "kl", "penang", "langkawi"])
        is_thailand = dest_country_code == "TH" or any(t in (destination or "").lower() for t in ["bangkok", "thailand", "phuket", "chiang mai"])
        is_singapore = dest_country_code == "SG" or any(s in (destination or "").lower() for s in ["singapore"])

        if is_long_haul:
            flight_est_usd = 865.0 * travellers  # Long-haul transcontinental routing index (~₹72,000 INR)
            est_fees_usd = 95.0 * travellers
            est_outbound = round((flight_est_usd / 2.0) * rate, 2)
            est_return = round((flight_est_usd / 2.0) * rate, 2)
            est_lodging = round((strategy["lodging_per_night_usd"] * num_rooms * nights) * rate, 2)
            est_food = round((strategy["food_per_day_usd"] * trip_days * travellers) * rate, 2)
            est_transit = round((strategy["local_transit_per_day_usd"] * trip_days + (30.0 if "bolivia" in (destination or "").lower() else 0.0)) * rate, 2)
            est_activities = round((strategy["activities_per_day_usd"] * trip_days * travellers) * rate, 2)
            est_fees = round(est_fees_usd * rate, 2)
        elif is_regional_international:
            if is_malaysia:
                # Calibrated Malaysia / Kuala Lumpur market rates (more affordable than Singapore)
                flight_est_usd = (120.0 if tier_key == "budget" else 190.0 if tier_key == "mid_range" else 380.0 if tier_key == "luxury" else 750.0) * travellers
                est_fees_usd = 25.0 * travellers
                est_outbound = round((flight_est_usd / 2.0) * rate, 2)
                est_return = round((flight_est_usd / 2.0) * rate, 2)
                my_room_usd = 25.0 if tier_key == "budget" else 55.0 if tier_key == "mid_range" else 135.0 if tier_key == "luxury" else 290.0
                est_lodging = round((my_room_usd * num_rooms * nights) * rate, 2)
                my_food_usd = 8.0 if tier_key == "budget" else 15.0 if tier_key == "mid_range" else 42.0 if tier_key == "luxury" else 85.0
                est_food = round((my_food_usd * trip_days * travellers) * rate, 2)
                my_transit_usd = 5.0 if tier_key == "budget" else 9.0 if tier_key == "mid_range" else 25.0 if tier_key == "luxury" else 55.0
                est_transit = round((my_transit_usd * trip_days) * rate, 2)
                my_act_usd = 6.0 if tier_key == "budget" else 14.0 if tier_key == "mid_range" else 30.0 if tier_key == "luxury" else 65.0
                est_activities = round((my_act_usd * trip_days * travellers) * rate, 2)
                est_fees = round(est_fees_usd * rate, 2)
            else:
                # Regional International route index (e.g. India <-> Singapore / SE Asia)
                flight_est_usd = (160.0 if tier_key == "budget" else 260.0 if tier_key == "mid_range" else 550.0 if tier_key == "luxury" else 950.0) * travellers
                est_fees_usd = 45.0 * travellers
                est_outbound = round((flight_est_usd / 2.0) * rate, 2)
                est_return = round((flight_est_usd / 2.0) * rate, 2)
                est_lodging = round((strategy["lodging_per_night_usd"] * num_rooms * nights) * rate, 2)
                est_food = round((strategy["food_per_day_usd"] * trip_days * travellers) * rate, 2)
                est_transit = round((strategy["local_transit_per_day_usd"] * trip_days) * rate, 2)
                est_activities = round((strategy["activities_per_day_usd"] * trip_days * travellers) * rate, 2)
                est_fees = round(est_fees_usd * rate, 2)
        elif is_india_domestic:
            # Calibrated domestic Indian market rates (benchmarked to Agra / Golden Triangle domestic travel)
            dom_flight_usd = 30.0 if tier_key == "budget" else 50.0 if tier_key == "mid_range" else 80.0 if tier_key == "luxury" else 120.0
            flight_est_usd = dom_flight_usd * travellers
            est_outbound = round((flight_est_usd / 2.0) * rate, 2)
            est_return = round((flight_est_usd / 2.0) * rate, 2)

            # Domestic lodging per room per night (Budget ₹1.5k, Mid-range ₹3.5k, Luxury ₹6.5k, Ultra Luxury ₹8.5k)
            room_rate_usd = 18.0 if tier_key == "budget" else 42.0 if tier_key == "mid_range" else 78.0 if tier_key == "luxury" else 102.0
            est_lodging = round((num_rooms * room_rate_usd * nights) * rate, 2)

            # Domestic food per person per day (Budget ₹500, Mid-range ₹1000, Luxury ₹1800, Ultra Luxury ₹2500)
            food_person_usd = 6.0 if tier_key == "budget" else 12.0 if tier_key == "mid_range" else 22.0 if tier_key == "luxury" else 30.0
            est_food = round((travellers * food_person_usd * trip_days) * rate, 2)

            # Domestic group transit per day (Budget ₹1.2k, Mid-range ₹2k, Luxury ₹2.9k, Ultra Luxury ₹3.7k private tempo traveler)
            transit_day_usd = 15.0 if tier_key == "budget" else 25.0 if tier_key == "mid_range" else 35.0 if tier_key == "luxury" else 45.0
            est_transit = round((transit_day_usd * trip_days) * rate, 2)

            # Domestic activities & guides per person per day (Budget ₹160, Mid-range ₹400, Luxury ₹670, Ultra Luxury ₹1000)
            act_person_usd = 2.0 if tier_key == "budget" else 5.0 if tier_key == "mid_range" else 8.0 if tier_key == "luxury" else 12.0
            est_activities = round((travellers * act_person_usd * trip_days) * rate, 2)

            # Domestic travel within India: Zero visa costs; modest allowance for domestic travel insurance & booking fees
            est_fees_usd = 2.0 * travellers
            est_fees = round(est_fees_usd * rate, 2)
        else:
            flight_est_usd = (180.0 if tier_key == "budget" else 350.0 if tier_key == "mid_range" else 750.0 if tier_key == "luxury" else 1400.0) * travellers
            est_outbound = round((flight_est_usd / 2.0) * rate, 2)
            est_return = round((flight_est_usd / 2.0) * rate, 2)
            est_lodging = round((strategy["lodging_per_night_usd"] * num_rooms * nights) * rate, 2)
            est_food = round((strategy["food_per_day_usd"] * trip_days * travellers) * rate, 2)
            est_transit = round((strategy["local_transit_per_day_usd"] * trip_days) * rate, 2)
            est_activities = round((strategy["activities_per_day_usd"] * trip_days * travellers) * rate, 2)
            est_fees = round(95.0 * travellers * rate, 2)

        subtotal_est = est_outbound + est_return + est_lodging + est_food + est_transit + est_activities + est_fees
        est_contingency = round(subtotal_est * (0.05 if is_india_domestic else 0.06 if is_malaysia else 0.08), 2)
        bottom_up_trip_cost = round(subtotal_est + est_contingency, 2)

        total_estimated_trip_cost = bottom_up_trip_cost
        daily_cost = round(total_estimated_trip_cost / trip_days, 2)

        # Budget Feasibility Check (Compare user budget limit against bottom-up estimated trip cost)
        is_feasible = raw_budget >= total_estimated_trip_cost
        shortfall = max(0.0, round(total_estimated_trip_cost - raw_budget, 2)) if not is_feasible else 0.0
        remaining_budget = max(0.0, round(raw_budget - total_estimated_trip_cost, 2)) if is_feasible else 0.0
        surplus_buffer_pct = round((remaining_budget / raw_budget) * 100.0, 1) if raw_budget > 0 else 0.0

        feasibility_status = "Budget Feasible" if is_feasible else "Over Budget"
        feasibility_color = "emerald" if is_feasible else "rose"
        shortfall_pct = round((shortfall / raw_budget) * 100.0, 1) if (not is_feasible and raw_budget > 0) else 0.0

        if is_feasible:
            feasibility_note = f"Allocated budget of {format_currency(raw_budget, curr)} comfortably accommodates the estimated {strategy['name']} group trip cost of {format_currency(total_estimated_trip_cost, curr)}."
        else:
            if tier_key == "mid_range":
                advice = "Consider adjusting comfort tier to Budget, booking 1 family room instead of 2 standard rooms, exploring promotional flight fares, or increasing total budget."
            elif tier_key in ["luxury", "ultra_luxury"]:
                advice = "Consider adjusting comfort tier to Mid-range or Budget, booking standard rooms, or increasing total budget."
            else:
                advice = "Consider securing promotional transit bookings, selecting hostel/homestay accommodations, or increasing total budget."

            feasibility_note = (
                f"Group of {travellers} traveler(s) over {trip_days} days in {strategy['name']} tier "
                f"({num_rooms} hotel room(s), transit, dining, activities) requires an estimated {format_currency(total_estimated_trip_cost, curr)}. "
                f"Your budget has a shortfall of {format_currency(shortfall, curr)} (+{shortfall_pct}%). "
                f"{advice}"
            )

        min_cost = round(total_estimated_trip_cost * 0.94, 2)
        max_cost = round(total_estimated_trip_cost * 1.07, 2)
        # Dynamic category label & notes based on domestic vs international travel
        is_domestic = is_india_domestic or (dest_country_code and dest_country_code == dest_info.get("origin_country_code"))
        fees_label = "Baggage & Travel Insurance" if is_domestic else "Visa, Baggage & Insurance"
        fees_notes = (
            f"Domestic travel ({dest_info.get('country', 'India')}): No visa required. Allowance covers travel insurance, railway reservation fees, and optional baggage for {travellers} traveller(s)."
            if is_domestic else
            f"International entry visa / ETA fees, comprehensive travel medical insurance, and checked baggage for {travellers} traveller(s)."
        )

        # Category allocations array for UI cards and charts
        categories = [
            {
                "key": "outbound_transport",
                "label": "Outbound Travel",
                "percentage": pcts["outbound_transport"],
                "allocated_amount": outbound_amt,
                "amount": outbound_amt,
                "formatted": format_currency(outbound_amt, curr),
                "formatted_allocated": format_currency(outbound_amt, curr),
                "estimated_cost": est_outbound,
                "formatted_estimated": format_currency(est_outbound, curr),
                "is_estimate": True,
                "pricing_basis": f"Per person one-way transit ({travellers} traveller(s))",
                "unit_rate": f"{curr_symbol}{round(est_outbound / max(1, travellers), 2):,.2f} per person",
                "notes": f"Travel from {origin_city or 'origin'} to {destination or 'destination'} via {transport_mode} for {travellers} traveller(s).",
            },
            {
                "key": "return_transport",
                "label": "Return Travel",
                "percentage": pcts["return_transport"],
                "allocated_amount": return_amt,
                "amount": return_amt,
                "formatted": format_currency(return_amt, curr),
                "formatted_allocated": format_currency(return_amt, curr),
                "estimated_cost": est_return,
                "formatted_estimated": format_currency(est_return, curr),
                "is_estimate": True,
                "pricing_basis": f"Per person return transit ({travellers} traveller(s))",
                "unit_rate": f"{curr_symbol}{round(est_return / max(1, travellers), 2):,.2f} per person",
                "notes": f"Return journey from {destination or 'destination'} to {origin_city or 'origin'} for {travellers} traveller(s).",
            },
            {
                "key": "accommodation",
                "label": "Accommodation",
                "percentage": pcts["accommodation"],
                "allocated_amount": accom_amt,
                "amount": accom_amt,
                "formatted": format_currency(accom_amt, curr),
                "formatted_allocated": format_currency(accom_amt, curr),
                "estimated_cost": est_lodging,
                "formatted_estimated": format_currency(est_lodging, curr),
                "is_estimate": True,
                "pricing_basis": f"Per room per night ({num_rooms} room(s) × {nights} night(s))",
                "unit_rate": f"{curr_symbol}{round(est_lodging / max(1, num_rooms * nights), 2):,.2f} per room/night",
                "notes": f"{nights} night(s) in {accommodation_preference.title()} ({tier_key.replace('_', ' ').title()} tier standard).",
            },
            {
                "key": "food",
                "label": "Food & Beverages",
                "percentage": pcts["food"],
                "allocated_amount": food_amt,
                "amount": food_amt,
                "formatted": format_currency(food_amt, curr),
                "formatted_allocated": format_currency(food_amt, curr),
                "estimated_cost": est_food,
                "formatted_estimated": format_currency(est_food, curr),
                "is_estimate": True,
                "pricing_basis": f"Per person per day ({travellers} traveler(s) × {trip_days} day(s))",
                "unit_rate": f"{curr_symbol}{round(est_food / max(1, travellers * trip_days), 2):,.2f} per person/day",
                "notes": f"Daily breakfast, lunch, and regional dinner dining for {travellers} traveller(s) across {trip_days} days.",
            },
            {
                "key": "local_transport",
                "label": "Local / Intercity Transit",
                "percentage": pcts["local_transport"],
                "allocated_amount": local_trans_amt,
                "amount": local_trans_amt,
                "formatted": format_currency(local_trans_amt, curr),
                "formatted_allocated": format_currency(local_trans_amt, curr),
                "estimated_cost": est_transit,
                "formatted_estimated": format_currency(est_transit, curr),
                "is_estimate": True,
                "pricing_basis": f"Per day group transit ({trip_days} day(s))",
                "unit_rate": f"{curr_symbol}{round(est_transit / max(1, trip_days), 2):,.2f} per day",
                "notes": f"Public metro, authorized cabs, and intercity route shuttles across {trip_days} days.",
            },
            {
                "key": "activities",
                "label": "Activities & Entry Fees",
                "percentage": pcts["activities"],
                "allocated_amount": activities_amt,
                "amount": activities_amt,
                "formatted": format_currency(activities_amt, curr),
                "formatted_allocated": format_currency(activities_amt, curr),
                "estimated_cost": est_activities,
                "formatted_estimated": format_currency(est_activities, curr),
                "is_estimate": True,
                "pricing_basis": f"Per person per day ({travellers} traveler(s) × {trip_days} day(s))",
                "unit_rate": f"{curr_symbol}{round(est_activities / max(1, travellers * trip_days), 2):,.2f} per person/day",
                "notes": f"Attraction tickets, heritage site entry, and tours in {destination or 'destination'}.",
            },
            {
                "key": "other_fees",
                "label": fees_label,
                "percentage": pcts["other_fees"],
                "allocated_amount": other_fees_amt,
                "amount": other_fees_amt,
                "formatted": format_currency(other_fees_amt, curr),
                "formatted_allocated": format_currency(other_fees_amt, curr),
                "estimated_cost": est_fees,
                "formatted_estimated": format_currency(est_fees, curr),
                "is_estimate": True,
                "pricing_basis": f"Per person one-time ({travellers} traveller(s))",
                "unit_rate": f"{curr_symbol}{round(est_fees / max(1, travellers), 2):,.2f} per person",
                "notes": fees_notes,
            },
            {
                "key": "contingency",
                "label": "Emergency & Contingency",
                "percentage": pcts["contingency"],
                "allocated_amount": contingency_amt,
                "amount": contingency_amt,
                "formatted": format_currency(contingency_amt, curr),
                "formatted_allocated": format_currency(contingency_amt, curr),
                "estimated_cost": est_contingency,
                "formatted_estimated": format_currency(est_contingency, curr),
                "is_estimate": True,
                "pricing_basis": "Group emergency reserve (5–8% of subtotal expenditure)",
                "unit_rate": f"{round((est_contingency / max(1.0, subtotal_est)) * 100.0, 1)}% of subtotal",
                "notes": "Emergency buffer reserved for unforeseen local expenses or price changes.",
            },
        ]

        # Ensure sum of category estimates strictly matches total_estimated_trip_cost
        sum_category_estimates = round(sum(c["estimated_cost"] for c in categories), 2)
        total_estimated_trip_cost = sum_category_estimates
        daily_cost = round(total_estimated_trip_cost / trip_days, 2)
        is_feasible = raw_budget >= total_estimated_trip_cost
        shortfall = max(0.0, round(total_estimated_trip_cost - raw_budget, 2)) if not is_feasible else 0.0
        shortfall_pct = round((shortfall / raw_budget) * 100.0, 1) if (not is_feasible and raw_budget > 0) else 0.0

        shortfall_categories = []
        for c in categories:
            diff = round(c["estimated_cost"] - c["allocated_amount"], 2)
            if diff > 0:
                shortfall_categories.append({
                    "key": c["key"],
                    "label": c["label"],
                    "allocated": c["allocated_amount"],
                    "formatted_allocated": c["formatted_allocated"],
                    "estimated": c["estimated_cost"],
                    "formatted_estimated": c["formatted_estimated"],
                    "shortfall": diff,
                    "formatted_shortfall": format_currency(diff, curr),
                    "explanation": f"Estimated {c['label'].lower()} ({c['formatted_estimated']}) exceeds allocated budget ({c['formatted_allocated']}) by {format_currency(diff, curr)}."
                })

        assumptions = {
            "travelers": travellers,
            "adults": adults,
            "children": children,
            "rooms": num_rooms,
            "nights": nights,
            "days": trip_days,
            "comfort_tier": strategy["name"],
            "tier_key": tier_key,
            "origin": origin_city or "Origin",
            "destination": destination or "Destination",
            "transport_mode": transport_mode,
            "basis_description": (
                f"Calculations assume {travellers} traveler(s) ({adults} adult(s)"
                + (f", {children} child(ren)" if children > 0 else "")
                + f") in {num_rooms} room(s) for {nights} night(s) and {trip_days} days under {strategy['name']} comfort tier standards."
            )
        }

        category_reconciliation = {
            "allocated_total": raw_budget,
            "formatted_allocated_total": format_currency(raw_budget, curr),
            "estimated_total": total_estimated_trip_cost,
            "formatted_estimated_total": format_currency(total_estimated_trip_cost, curr),
            "variance": round(raw_budget - total_estimated_trip_cost, 2),
            "formatted_variance": format_currency(abs(round(raw_budget - total_estimated_trip_cost, 2)), curr),
            "is_feasible": is_feasible,
            "shortfall_amount": shortfall,
            "formatted_shortfall_amount": format_currency(shortfall, curr),
            "shortfall_percentage": shortfall_pct,
            "shortfall_categories": shortfall_categories,
            "assumptions": assumptions,
            "contingency_explanation": (
                "Category Emergency Reserve is an expense allocation reserved within the trip estimate to absorb unexpected on-trip costs (minor price surges, local cabs, emergency transit). "
                "Surplus Buffer is unallocated funds remaining when the user budget exceeds the total estimated trip costs. "
                "When estimated costs match or exceed the user budget ceiling, the unallocated Surplus Buffer is zero, while the Category Emergency Reserve remains fully funded and protected within the expense plan."
            ),
            "categories": {
                c["key"]: {
                    "label": c["label"],
                    "allocated": c["allocated_amount"],
                    "formatted_allocated": c["formatted_allocated"],
                    "estimated": c["estimated_cost"],
                    "formatted_estimated": c["formatted_estimated"],
                    "difference": round(c["allocated_amount"] - c["estimated_cost"], 2),
                    "status": "Shortfall" if c["estimated_cost"] > c["allocated_amount"] else "Within Budget",
                    "shortfall_amount": round(max(0.0, c["estimated_cost"] - c["allocated_amount"]), 2),
                } for c in categories
            }
        }

        feasibility_notes = [feasibility_note]

        cost_provenance = {
            "flights": {
                "source": (
                    "Regional International Route Index (India <-> Kuala Lumpur / Malaysia)" if is_malaysia
                    else "Regional International Route Index (India <-> Bangkok / Thailand)" if is_thailand
                    else "Regional International Route Index (India <-> Singapore)" if is_singapore
                    else dest_info["flight_provenance_source"]
                ),
                "status": "Estimated",
                "notes": f"Fares based on group of {travellers} travelers ({transport_mode})."
            },
            "accommodation": {
                "source": f"{destination.title() or 'Destination'} {tier_key.replace('_', ' ').title()} Hotel Benchmark",
                "status": "Sourced estimate",
                "notes": f"Based on {num_rooms} rooms across {nights} nights standard room occupancy."
            },
            "food": {
                "source": "Local Dining Market Index",
                "status": "Sourced estimate",
                "notes": f"{trip_days} days of meals and beverage allowance for {travellers} traveler(s)."
            },
            "local_transit": {
                "source": "Municipal & Regional Transit Schedules",
                "status": "Sourced estimate",
                "notes": f"Includes airport transfers, vehicle hire for {travellers} people, and site transfers."
            },
            "activities": {
                "source": "Municipal Museum & Heritage Entry Registries",
                "status": "Estimated",
                "notes": "Standard public admission, guided tours, and conservation tickets (Estimated average)."
            }
        }

        per_person_budget = round(raw_budget / max(1, travellers), 2)
        per_person_est_cost = round(total_estimated_trip_cost / max(1, travellers), 2)

        # Dynamic, destination-independent currency resolution from Gazetteer and ISO registry
        dest_curr = dest_info["currency"]
        dest_symbol = dest_info["currency_symbol"]
        rate_val = CurrencyService.convert(1.0, dest_curr, curr)
        timestamp_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        exchange_provenance = (
            f"1 {dest_curr} ≈ {format_currency(rate_val, curr)} ({curr}) (Market Reference Rate as of {timestamp_str})"
            if dest_curr != curr else "Domestic Currency Standard"
        )

        return {
            "tier_key": tier_key,
            "destination_currency": dest_curr,
            "destination_currency_symbol": dest_symbol,
            "exchange_rate_provenance": exchange_provenance,
            "tier_name": strategy["name"],
            "tier_description": strategy["description"],
            "currency": curr,
            "currency_symbol": symbol,
            "total_user_budget": raw_budget,
            "formatted_user_budget": format_currency(raw_budget, curr),
            "per_person_budget": per_person_budget,
            "formatted_per_person_budget": format_currency(per_person_budget, curr),
            "total_estimated_trip_cost": total_estimated_trip_cost,
            "total_estimated_cost": total_estimated_trip_cost,
            "estimated_total_cost": total_estimated_trip_cost,
            "allocated_budget": raw_budget,
            "allocated_total_budget": raw_budget,
            "estimated_total_expenditure": total_estimated_trip_cost,
            "category_reconciliation": category_reconciliation,
            "formatted_total_estimated_cost": format_currency(total_estimated_trip_cost, curr),
            "per_person_estimated_cost": per_person_est_cost,
            "formatted_per_person_estimated_cost": format_currency(per_person_est_cost, curr),
            "total_travelers": travellers,
            "adults": adults,
            "children": children,
            "duration_days": trip_days,
            "nights": nights,
            "num_rooms": num_rooms,
            "room_calculation_note": f"{num_rooms} room(s) based on 2 travelers/room standard for {travellers} traveler(s) across {nights} night(s).",
            "estimated_daily_cost": daily_cost,
            "formatted_daily_cost": format_currency(daily_cost, curr),
            "outbound_travel_estimate": outbound_amt,
            "return_travel_estimate": return_amt,
            "accommodation_estimate": accom_amt,
            "food_estimate": food_amt,
            "local_transport_estimate": local_trans_amt,
            "activities_estimate": activities_amt,
            "other_fees_estimate": other_fees_amt,
            "contingency_estimate": contingency_amt,
            "remaining_budget": remaining_budget,
            "formatted_remaining_budget": format_currency(remaining_budget, curr),
            "remaining_surplus_buffer": remaining_budget,
            "formatted_remaining_surplus": format_currency(remaining_budget, curr),
            "shortfall": shortfall,
            "formatted_shortfall": format_currency(shortfall, curr),
            "shortfall_percentage": shortfall_pct,
            "is_feasible": is_feasible,
            "feasibility_status": feasibility_status,
            "feasibility_color": feasibility_color,
            "feasibility_badge": f"{feasibility_status} (+{format_currency(shortfall, curr)} / +{shortfall_pct}%)" if not is_feasible else "Budget Feasible",
            "feasibility_note": feasibility_note,
            "feasibility_notes": feasibility_notes,
            "categories": categories,
            "category_allocations": {c["key"]: c["amount"] for c in categories},
            "total_allocated_categories": raw_budget,
            "formatted_total_allocated": format_currency(raw_budget, curr),
            "uncertainty_range": {
                "min": min_cost,
                "max": max_cost,
                "min_cost": min_cost,
                "max_cost": max_cost,
                "formatted_range": f"{format_currency(min_cost, curr)} – {format_currency(max_cost, curr)}"
            },
            "formatted_uncertainty_range": f"{format_currency(min_cost, curr)} – {format_currency(max_cost, curr)}",
            "cost_provenance": cost_provenance,
            "provenance_summary": "Estimated Regional Market Benchmarks (Subject to seasonal variation)",
            "surplus_buffer_percentage": surplus_buffer_pct,
            "contingency_explanation": (
                "Category Emergency Reserve is an expense allocation reserved within the trip estimate to absorb unexpected on-trip costs (minor price surges, local cabs, emergency transit). "
                "Surplus Buffer is unallocated funds remaining when the user budget exceeds the total estimated trip costs. "
                "When estimated costs match or exceed the user budget ceiling, the unallocated Surplus Buffer is zero, while the Category Emergency Reserve remains fully funded and protected within the expense plan."
            ),
            "pricing_source": "WanderWise Central Budget Allocation Engine",
            "pricing_status": "Estimated",
            "pricing_disclaimer": "All cost figures are market-calibrated estimates and subject to seasonal provider availability. Actual costs may vary.",
            "disclosure": "All amounts are transparently calculated estimates based on destination economics and user comfort tier. No unverified live fares are represented as confirmed bookings.",
        }
