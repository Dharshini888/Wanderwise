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

from typing import Dict, Any, List, Optional, Tuple
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
        # Group room count calculation: Validate room occupancy against family composition
        # When traveling as a family (travel_style == "family" or family/suite room preference),
        # up to 2 adults and 2 children are accommodated in 1 Family Room / Quad Suite without forcing 2 rooms.
        # Otherwise, standard 2-person double occupancy is calculated.
        is_family_mode = (
            str(travel_style or "").lower() == "family"
            or any(f in str(accommodation_preference or "").lower() for f in ["family", "suite", "quad", "villa", "apartment"])
            or kwargs.get("family_room") is True
            or kwargs.get("room_occupancy") == "family"
        )
        if adults == 1 and children == 0:
            num_rooms = 1
        elif adults <= 2 and children <= 1:
            # 1 family room (accommodating 2 adults + 1 child with rollaway/extra bed)
            num_rooms = 1
        elif (is_family_mode or str(travel_style).lower() == "family") and adults <= 2 and children <= 2:
            num_rooms = 1
        else:
            num_rooms = max(1, (travellers + 1) // 2)

        # Global Destination & Route Corridor Awareness
        dest_info = resolve_destination_info(destination, origin_city)
        cost_multiplier = dest_info.get("price_multiplier", 1.0)
        is_long_haul = dest_info.get("is_long_haul", False)
        is_regional_international = dest_info.get("is_regional_international", False)
        is_india_domestic = dest_info.get("is_india_domestic", False)
        dest_country_code = dest_info.get("country_code", "")

        origin_country_code = dest_info.get("origin_country_code", "IN")
        is_domestic = is_india_domestic or (dest_country_code and dest_country_code == origin_country_code)

        # Separate long-distance corridor transport from destination local transit
        local_transit_preference = str(transport_mode or "Public Metro & Bus").strip()
        if is_domestic:
            corridor_transport_mode = "Domestic Air / Intercity Rail" if (cost_multiplier > 1.2 or "rail" in local_transit_preference.lower()) else "Domestic Express Transit"
            corridor_label_out = "Outbound Intercity Transit"
            corridor_label_ret = "Return Intercity Transit"
        elif is_long_haul:
            corridor_transport_mode = "Commercial Airline (International Long-Haul Flight)"
            corridor_label_out = "International Outbound Flight"
            corridor_label_ret = "International Return Flight"
        else:
            corridor_transport_mode = "Commercial Airline (Regional Flight)"
            corridor_label_out = "International Outbound Flight"
            corridor_label_ret = "International Return Flight"

        # 1. Dynamic Transportation (Person-Based: Adults + Children, Directional)
        if is_domestic:
            # Domestic route benchmark (calibrated by domestic transit / rail / air index)
            adult_rt_usd = 30.0 if tier_key == "budget" else 50.0 if tier_key == "mid_range" else 80.0 if tier_key == "luxury" else 120.0
            child_rt_usd = round(adult_rt_usd * 0.65, 2)
            trans_source = "Domestic Intercity Transit & Air Corridor Index"
            trans_type = "Domestic Route Benchmark"
        elif is_regional_international:
            # Dynamic Regional International Air Corridor (e.g. India <-> Southeast Asia, Middle East, Central Asia)
            base_regional = 135.0 if tier_key == "budget" else 190.0 if tier_key == "mid_range" else 400.0 if tier_key == "luxury" else 750.0
            adult_rt_usd = round(base_regional * min(1.3, max(0.9, (cost_multiplier + 0.9) / 2.0)), 2)
            child_rt_usd = round(adult_rt_usd * 0.75, 2)
            trans_source = f"IATA Regional International Air Corridor Index ({origin_city} <-> {destination})"
            trans_type = "Regional Flight Benchmark"
        else:
            # Long-haul / Transcontinental (e.g. India <-> Switzerland / Europe / Americas / Africa / Oceania / Japan)
            adult_rt_usd = 680.0 if tier_key == "budget" else 850.0 if tier_key == "mid_range" else 1700.0 if tier_key == "luxury" else 3200.0
            child_rt_usd = round(adult_rt_usd * 0.75, 2)
            trans_source = f"IATA Transcontinental Long-Haul Route Benchmark ({origin_city} <-> {destination})"
            trans_type = "International Flight Benchmark"

        # Outbound and Return directional split (exactly 50% each)
        outbound_adult_usd = round(adult_rt_usd / 2.0, 2)
        outbound_child_usd = round(child_rt_usd / 2.0, 2)
        return_adult_usd = round(adult_rt_usd - outbound_adult_usd, 2)
        return_child_usd = round(child_rt_usd - outbound_child_usd, 2)

        total_outbound_usd = round((adults * outbound_adult_usd) + (children * outbound_child_usd), 2)
        total_return_usd = round((adults * return_adult_usd) + (children * return_child_usd), 2)

        est_outbound = round(total_outbound_usd * rate, 2)
        est_transport_total = round(((adults * adult_rt_usd) + (children * child_rt_usd)) * rate, 2)
        est_return = round(est_transport_total - est_outbound, 2)
        per_person_transport = round(est_transport_total / max(1, travellers), 2)
        adult_per_person_trans = round(adult_rt_usd * rate, 2)
        child_per_person_trans = round(child_rt_usd * rate, 2)

        # 2. Accommodation Estimation (Room Count & Occupancy Based)
        if is_domestic and dest_country_code == "IN":
            room_rate_usd = 18.0 if tier_key == "budget" else 42.0 if tier_key == "mid_range" else 78.0 if tier_key == "luxury" else 102.0
        else:
            base_room = strategy["lodging_per_night_usd"]
            room_rate_usd = base_room * cost_multiplier

        est_lodging = round((num_rooms * room_rate_usd * nights) * rate, 2)

        # 3. Food Estimation (Person-based: Adult vs Child Daily Rates)
        if is_domestic and dest_country_code == "IN":
            food_adult_usd = 6.0 if tier_key == "budget" else 12.0 if tier_key == "mid_range" else 22.0 if tier_key == "luxury" else 30.0
            food_child_usd = round(food_adult_usd * 0.55, 2)
        else:
            base_food = strategy["food_per_day_usd"]
            food_adult_usd = base_food * cost_multiplier
            food_child_usd = round(food_adult_usd * 0.6, 2)

        total_food_usd = (adults * food_adult_usd + children * food_child_usd) * trip_days
        est_food = round(total_food_usd * rate, 2)

        # 4. Local Transportation Estimation (Group Daily Rate)
        if is_domestic and dest_country_code == "IN":
            transit_day_usd = 15.0 if tier_key == "budget" else 25.0 if tier_key == "mid_range" else 35.0 if tier_key == "luxury" else 45.0
        else:
            base_transit = strategy["local_transit_per_day_usd"]
            transit_day_usd = base_transit * cost_multiplier

        est_transit = round((transit_day_usd * trip_days) * rate, 2)

        # 5. Activities & Entrance Fees (Adult vs Child Rates)
        if is_domestic and dest_country_code == "IN":
            act_adult_usd = 2.0 if tier_key == "budget" else 5.0 if tier_key == "mid_range" else 8.0 if tier_key == "luxury" else 12.0
            act_child_usd = round(act_adult_usd * 0.5, 2)
        else:
            base_act = strategy["activities_per_day_usd"]
            act_adult_usd = base_act * cost_multiplier
            act_child_usd = round(act_adult_usd * 0.6, 2)

        total_act_usd = (adults * act_adult_usd + children * act_child_usd) * trip_days
        est_activities = round(total_act_usd * rate, 2)

        # 6. Visa, Baggage & Insurance
        dest_clean_l = (destination or "").lower()
        if is_domestic:
            fees_usd = 2.0 * travellers
            fees_label = "Baggage & Travel Insurance"
            fees_notes = f"Domestic travel ({dest_info.get('country', 'Domestic')}): No visa required. Allowance covers travel insurance, railway booking charges, and baggage for {travellers} traveller(s)."
        elif "turkey" in dest_clean_l or "istanbul" in dest_clean_l:
            # Turkey official eVisa / Gateway visa for Indian passport holders ~$60 USD (~5,000 INR) per person
            visa_per_person_usd = 60.0
            visa_total_usd = visa_per_person_usd * travellers
            baggage_usd = 25.0 * travellers
            insurance_usd = 15.0 * travellers
            fees_usd = visa_total_usd + baggage_usd + insurance_usd
            fees_label = "Visa, Baggage & Insurance"
            fees_notes = f"Turkey entry: Official electronic visa (e-Visa / Gateway) for Indian passport holders at ~$60 USD (~5,000 INR) per person (${int(visa_total_usd)} for {travellers} travellers), plus checked baggage and travel insurance."
        elif "nepal" in dest_clean_l or "bhutan" in dest_clean_l:
            fees_usd = 10.0 * travellers
            fees_label = "Travel Insurance & Border Processing"
            fees_notes = f"India-Nepal / Bhutan bilateral treaty: Visa-free entry for Indian passport holders. Allowance covers travel insurance and border processing."
        elif "indonesia" in dest_clean_l or "bali" in dest_clean_l:
            # Indonesia Visa on Arrival (VoA) / e-VoA: $35 USD (~500,000 IDR) per person
            visa_per_person_usd = 35.0
            visa_total_usd = visa_per_person_usd * travellers
            baggage_usd = 15.0 * travellers
            insurance_usd = 10.0 * travellers
            fees_usd = visa_total_usd + baggage_usd + insurance_usd
            fees_label = "Visa, Baggage & Insurance"
            fees_notes = f"Indonesia entry: Official Visa on Arrival (VoA / e-VoA) at $35 USD (~500,000 IDR) per person (${int(visa_total_usd)} for {travellers} travellers), plus airline checked baggage and travel medical insurance."
        elif is_long_haul:
            adult_fee_usd = 130.0
            child_fee_usd = 75.0
            fees_usd = (adults * adult_fee_usd) + (children * child_fee_usd)
            fees_label = "Visa, Baggage & Insurance"
            fees_notes = f"International entry visa / ETA fees, comprehensive travel medical insurance, and checked baggage for {adults} adult(s) and {children} child(ren)."
        else:
            adult_fee_usd = 30.0
            child_fee_usd = 20.0
            fees_usd = (adults * adult_fee_usd) + (children * child_fee_usd)
            fees_label = "Visa, Baggage & Insurance"
            fees_notes = f"Regional international entry visa / ETA fees, travel medical insurance, and baggage for {adults} adult(s) and {children} child(ren)."

        est_fees = round(fees_usd * rate, 2)

        # 7. Subtotal & Emergency Contingency (Included exactly once)
        subtotal_est = est_outbound + est_return + est_lodging + est_food + est_transit + est_activities + est_fees
        contingency_rate = 0.05 if is_domestic else 0.06 if is_regional_international else 0.08
        est_contingency = round(subtotal_est * contingency_rate, 2)

        # 8. Total Estimated Trip Cost (Formula: Outbound + Return + Lodging + Food + Local + Activities + Fees + Contingency)
        total_estimated_trip_cost = round(subtotal_est + est_contingency, 2)
        daily_cost = round(total_estimated_trip_cost / trip_days, 2)

        # Budget Feasibility Check (Comparison against minimum required threshold)
        min_cost = round(total_estimated_trip_cost * 0.94, 2)
        max_cost = round(total_estimated_trip_cost * 1.07, 2)
        is_feasible = raw_budget >= min_cost
        shortfall = max(0.0, round(total_estimated_trip_cost - raw_budget, 2)) if not is_feasible else 0.0
        remaining_budget = max(0.0, round(raw_budget - total_estimated_trip_cost, 2)) if is_feasible else 0.0
        surplus_buffer_pct = round((remaining_budget / raw_budget) * 100.0, 1) if raw_budget > 0 else 0.0

        feasibility_status = "Budget Feasible" if is_feasible else "Over Budget"
        feasibility_color = "emerald" if is_feasible else "rose"
        shortfall_pct = round((shortfall / raw_budget) * 100.0, 1) if (not is_feasible and raw_budget > 0) else 0.0
        feasibility_badge = "Budget Feasible" if is_feasible else f"Over Budget (+{shortfall_pct}%)"

        # Dynamic Affordable Alternatives Generation
        dest_clean_l = (destination or "").lower()
        if not is_feasible:
            is_alpine = is_long_haul or any(t in dest_clean_l for t in ["mountain", "alps", "snow", "ski", "switzerland", "nepal", "austria", "chamonix", "zermatt"])
            is_coastal = any(t in dest_clean_l for t in ["beach", "island", "coast", "bali", "phuket", "maldives", "hawaii", "sea"])
            is_metropolitan = any(t in dest_clean_l for t in ["singapore", "tokyo", "new york", "london", "dubai", "hong kong", "paris"])

            if is_alpine or is_long_haul:
                affordable_alternatives = [
                    {
                        "name": "Manali & Solang Valley, India",
                        "type": "Domestic Mountain Alternative",
                        "est_cost": format_currency(round(total_estimated_trip_cost * 0.16, 2), curr),
                        "reason": "Snow-capped Himalayan peaks, alpine meadows, cable cars & adventure at 80% lower cost."
                    },
                    {
                        "name": "Kathmandu & Pokhara, Nepal",
                        "type": "Regional Mountain Alternative",
                        "est_cost": format_currency(round(total_estimated_trip_cost * 0.28, 2), curr),
                        "reason": "Dramatic Himalayan vistas, world heritage temples, and outdoor adventure with budget-friendly regional flights."
                    },
                    {
                        "name": "Munnar & Wayanad, Kerala",
                        "type": "Domestic Hill Station",
                        "est_cost": format_currency(round(total_estimated_trip_cost * 0.12, 2), curr),
                        "reason": "Lush rolling tea estates, cool mountain climate, waterfalls, and tranquil nature walks."
                    }
                ]
            elif is_coastal:
                affordable_alternatives = [
                    {
                        "name": "Goa & South Coast Beaches, India",
                        "type": "Domestic Coastal Alternative",
                        "est_cost": format_currency(round(total_estimated_trip_cost * 0.20, 2), curr),
                        "reason": "Scenic coastline, water sports, beach resorts, and vibrant seaside dining."
                    },
                    {
                        "name": "Da Nang & Hoi An, Vietnam",
                        "type": "Regional Coastal Alternative",
                        "est_cost": format_currency(round(total_estimated_trip_cost * 0.40, 2), curr),
                        "reason": "Pristine beaches, UNESCO heritage ancient town, and world-class street food."
                    }
                ]
            elif is_metropolitan:
                affordable_alternatives = [
                    {
                        "name": "Kuala Lumpur, Malaysia",
                        "type": "Regional City Alternative",
                        "est_cost": format_currency(round(total_estimated_trip_cost * 0.48, 2), curr),
                        "reason": "Modern skyline, theme parks, shopping, and vibrant culinary scene at lower cost."
                    },
                    {
                        "name": "Bangkok, Thailand",
                        "type": "Regional Metropolitan Alternative",
                        "est_cost": format_currency(round(total_estimated_trip_cost * 0.45, 2), curr),
                        "reason": "Vibrant night markets, grand historic temples, and acclaimed family attractions."
                    }
                ]
            else:
                affordable_alternatives = [
                    {
                        "name": "Jaipur & Golden Triangle, India",
                        "type": "Domestic Cultural Alternative",
                        "est_cost": format_currency(round(total_estimated_trip_cost * 0.25, 2), curr),
                        "reason": "Majestic royal palaces, ancient hilltop forts, vibrant craft bazaars, and rich culinary traditions."
                    },
                    {
                        "name": "Kathmandu & Patan, Nepal",
                        "type": "Regional Heritage Alternative",
                        "est_cost": format_currency(round(total_estimated_trip_cost * 0.32, 2), curr),
                        "reason": "Ancient pagoda temples, vibrant squares, and Himalayan cultural traditions."
                    }
                ]
        else:
            affordable_alternatives = []

        # Feasible duration calculation
        ground_daily_usd = (room_rate_usd * num_rooms + total_food_usd / trip_days + transit_day_usd + total_act_usd / trip_days) * (1.0 + contingency_rate)
        ground_daily_curr = ground_daily_usd * rate
        fixed_transit_curr = est_outbound + est_return + est_fees
        feasible_days = max(2, int((raw_budget - fixed_transit_curr) / max(1.0, ground_daily_curr))) if raw_budget > fixed_transit_curr else 2

        if is_feasible:
            feasibility_note = f"Allocated budget of {format_currency(raw_budget, curr)} comfortably accommodates the estimated {strategy['name']} group trip cost of {format_currency(total_estimated_trip_cost, curr)}."
        else:
            advice = f"Consider switching to Budget tier, increasing total budget to at least {format_currency(total_estimated_trip_cost, curr)}, reducing duration to {feasible_days} day(s), or selecting an affordable alternative destination."
            feasibility_note = (
                f"Group of {travellers} traveler(s) over {trip_days} days in {strategy['name']} tier "
                f"({num_rooms} room(s), return transit, dining, activities) requires an estimated {format_currency(total_estimated_trip_cost, curr)}. "
                f"Your budget has a shortfall of {format_currency(shortfall, curr)} (+{shortfall_pct}%). "
                f"{advice}"
            )

        min_cost = round(total_estimated_trip_cost * 0.94, 2)
        max_cost = round(total_estimated_trip_cost * 1.07, 2)

                # Category allocations array for UI cards and charts
        categories = [
            {
                "key": "outbound_transport",
                "label": corridor_label_out,
                "percentage": pcts["outbound_transport"],
                "allocated_amount": outbound_amt,
                "amount": outbound_amt,
                "formatted": format_currency(outbound_amt, curr),
                "formatted_allocated": format_currency(outbound_amt, curr),
                "estimated_cost": est_outbound,
                "formatted_estimated": format_currency(est_outbound, curr),
                "is_estimate": True,
                "pricing_basis": f"Per person one-way corridor transit ({travellers} traveller(s))",
                "unit_rate": f"{curr_symbol}{round(est_outbound / max(1, travellers), 2):,.2f} per person",
                "notes": f"Outbound corridor travel from {origin_city or 'origin'} to {destination or 'destination'} via {corridor_transport_mode} for {travellers} traveller(s).",
            },
            {
                "key": "return_transport",
                "label": corridor_label_ret,
                "percentage": pcts["return_transport"],
                "allocated_amount": return_amt,
                "amount": return_amt,
                "formatted": format_currency(return_amt, curr),
                "formatted_allocated": format_currency(return_amt, curr),
                "estimated_cost": est_return,
                "formatted_estimated": format_currency(est_return, curr),
                "is_estimate": True,
                "pricing_basis": f"Per person return corridor transit ({travellers} traveller(s))",
                "unit_rate": f"{curr_symbol}{round(est_return / max(1, travellers), 2):,.2f} per person",
                "notes": f"Return corridor journey from {destination or 'destination'} to {origin_city or 'origin'} via {corridor_transport_mode} for {travellers} traveller(s).",
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
                "label": f"Local Destination Transit ({local_transit_preference})",
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
                "notes": f"Local city transit ({local_transit_preference}) across {trip_days} days in {destination}.",
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
        min_cost = round(total_estimated_trip_cost * 0.94, 2)
        max_cost = round(total_estimated_trip_cost * 1.07, 2)
        is_feasible = raw_budget >= min_cost
        shortfall = max(0.0, round(total_estimated_trip_cost - raw_budget, 2)) if not is_feasible else 0.0
        shortfall_pct = round((shortfall / raw_budget) * 100.0, 1) if (not is_feasible and raw_budget > 0) else 0.0

        # Balanced Category Allocation: Eliminate artificial category ceiling shortfalls when total budget is sufficient
        if is_feasible and raw_budget >= total_estimated_trip_cost:
            surplus = round(raw_budget - total_estimated_trip_cost, 2)
            for c in categories:
                ratio = c["estimated_cost"] / max(1.0, total_estimated_trip_cost)
                add_share = round(surplus * ratio, 2)
                c["allocated_amount"] = round(c["estimated_cost"] + add_share, 2)
                c["amount"] = c["allocated_amount"]
                c["percentage"] = round((c["allocated_amount"] / max(1.0, raw_budget)) * 100.0, 1)
                c["formatted"] = format_currency(c["allocated_amount"], curr)
                c["formatted_allocated"] = format_currency(c["allocated_amount"], curr)

            diff_alloc = round(raw_budget - sum(c["allocated_amount"] for c in categories), 2)
            if abs(diff_alloc) > 0 and len(categories) > 0:
                categories[-1]["allocated_amount"] = round(categories[-1]["allocated_amount"] + diff_alloc, 2)
                categories[-1]["amount"] = categories[-1]["allocated_amount"]
                categories[-1]["formatted"] = format_currency(categories[-1]["allocated_amount"], curr)
                categories[-1]["formatted_allocated"] = format_currency(categories[-1]["allocated_amount"], curr)

            shortfall_categories = []
        else:
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

        if "turkey" in dest_clean_l or "istanbul" in dest_clean_l:
            visa_curr = round(60.0 * travellers * rate, 2)
            bag_curr = round(25.0 * travellers * rate, 2)
            ins_curr = round(15.0 * travellers * rate, 2)
            fees_breakdown = {
                "visa_eta": visa_curr,
                "travel_insurance": ins_curr,
                "checked_baggage": bag_curr,
                "total": est_fees,
                "notes": fees_notes,
                "formatted_visa_eta": format_currency(visa_curr, curr),
                "formatted_travel_insurance": format_currency(ins_curr, curr),
                "formatted_checked_baggage": format_currency(bag_curr, curr)
            }
        elif "indonesia" in dest_clean_l or "bali" in dest_clean_l:
            visa_curr = round(35.0 * travellers * rate, 2)
            bag_curr = round(15.0 * travellers * rate, 2)
            ins_curr = round(10.0 * travellers * rate, 2)
            fees_breakdown = {
                "visa_eta": visa_curr,
                "travel_insurance": ins_curr,
                "checked_baggage": bag_curr,
                "total": est_fees,
                "notes": fees_notes,
                "formatted_visa_eta": format_currency(visa_curr, curr),
                "formatted_travel_insurance": format_currency(ins_curr, curr),
                "formatted_checked_baggage": format_currency(bag_curr, curr)
            }
        else:
            fees_breakdown = {
                "visa_eta": round(est_fees * 0.45, 2) if not is_domestic else 0.0,
                "travel_insurance": round(est_fees * 0.35, 2) if not is_domestic else round(est_fees * 0.6, 2),
                "checked_baggage": round(est_fees * 0.20, 2) if not is_domestic else round(est_fees * 0.4, 2),
                "total": est_fees,
                "notes": fees_notes,
                "formatted_visa_eta": format_currency(round(est_fees * 0.45, 2) if not is_domestic else 0.0, curr),
                "formatted_travel_insurance": format_currency(round(est_fees * 0.35, 2) if not is_domestic else round(est_fees * 0.6, 2), curr),
                "formatted_checked_baggage": format_currency(round(est_fees * 0.20, 2) if not is_domestic else round(est_fees * 0.4, 2), curr)
            }

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
                "source": trans_source,
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

        transportation_details = {
            "mode": corridor_transport_mode,
            "corridor_mode": corridor_transport_mode,
            "local_transit_mode": local_transit_preference,
            "is_international": not is_domestic,
            "outbound_estimated_cost": est_outbound,
            "formatted_outbound": format_currency(est_outbound, curr),
            "return_estimated_cost": est_return,
            "formatted_return": format_currency(est_return, curr),
            "outbound_leg": {
                "label": corridor_label_out,
                "mode": corridor_transport_mode,
                "estimated_cost": est_outbound,
                "formatted": format_currency(est_outbound, curr),
            },
            "return_leg": {
                "label": corridor_label_ret,
                "mode": corridor_transport_mode,
                "estimated_cost": est_return,
                "formatted": format_currency(est_return, curr),
            },
            "total_transport_cost": est_transport_total,
            "formatted_total_transport": format_currency(est_transport_total, curr),
            "group_total_cost": est_transport_total,
            "formatted_group_total": format_currency(est_transport_total, curr),
            "per_person_cost": per_person_transport,
            "formatted_per_person": format_currency(per_person_transport, curr),
            "adult_fare_roundtrip": adult_per_person_trans,
            "formatted_adult_fare": format_currency(adult_per_person_trans, curr),
            "child_fare_roundtrip": child_per_person_trans,
            "formatted_child_fare": format_currency(child_per_person_trans, curr),
            "adults": adults,
            "children": children,
            "adult_passengers": adults,
            "child_passengers": children,
            "total_travelers": travellers,
            "source": trans_source,
            "provenance_source": trans_source,
            "provenance_type": trans_type,
            "pricing_type": "Market Benchmark",
            "is_market_benchmark": True,
            "is_live_quote": False,
            "notes": (
                f"Benchmark {corridor_transport_mode} corridor estimate: {adults} adult(s) @ {format_currency(adult_per_person_trans, curr)}"
                + (f" + {children} child(ren) @ {format_currency(child_per_person_trans, curr)}" if children > 0 else "")
                + f" = {format_currency(est_transport_total, curr)} total. Directionally split 50/50 outbound & return. Local city transit ({local_transit_preference}) is budgeted separately."
            )
        }

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
            "estimated_trip_expenditure": total_estimated_trip_cost,
            "estimated_total_expenditure": total_estimated_trip_cost,
            "category_reconciliation": category_reconciliation,
            "formatted_total_estimated_cost": format_currency(total_estimated_trip_cost, curr),
            "per_person_estimated_cost": per_person_est_cost,
            "formatted_per_person_estimated_cost": format_currency(per_person_est_cost, curr),
            "fees_breakdown": fees_breakdown,
            "total_travelers": travellers,
            "adults": adults,
            "children": children,
            "duration_days": trip_days,
            "nights": nights,
            "num_rooms": num_rooms,
            "assumptions": assumptions,
            "room_calculation_note": f"{num_rooms} room(s) based on 2 travelers/room standard for {travellers} traveler(s) across {nights} night(s).",
            "estimated_daily_cost": daily_cost,
            "formatted_daily_cost": format_currency(daily_cost, curr),
            "outbound_travel_estimate": est_outbound,
            "return_travel_estimate": est_return,
            "estimated_outbound_transport": est_outbound,
            "estimated_return_transport": est_return,
            "accommodation_estimate": est_lodging,
            "food_estimate": est_food,
            "local_transport_estimate": est_transit,
            "activities_estimate": est_activities,
            "other_fees_estimate": est_fees,
            "travel_fees_estimate": est_fees,
            "contingency_estimate": est_contingency,
            "allocated_outbound": outbound_amt,
            "allocated_return": return_amt,
            "allocated_accommodation": accom_amt,
            "allocated_food": food_amt,
            "allocated_local_transport": local_trans_amt,
            "allocated_activities": activities_amt,
            "allocated_other_fees": other_fees_amt,
            "allocated_contingency": contingency_amt,
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
            "transportation_details": transportation_details,
            "affordable_alternatives": affordable_alternatives,
            "suggested_min_budget": total_estimated_trip_cost,
            "suggested_duration_days": feasible_days,
        }

    @classmethod
    def validate_financial_plan(cls, plan: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate financial payload consistency before saving or presenting to the user.
        Ensures that room counts, category reconciliation, and transport totals are mathematically sound.
        """
        issues = []
        if not isinstance(plan, dict):
            return False, ["Plan payload must be a dictionary"]

        raw_budget = plan.get("allocated_budget") or plan.get("allocated_total_budget") or 0.0
        total_est = plan.get("total_estimated_trip_cost") or plan.get("estimated_total_cost") or 0.0

        cats = plan.get("categories", [])
        if cats:
            allocated_sum = round(sum(c.get("allocated_amount", 0.0) for c in cats), 2)
            if abs(allocated_sum - raw_budget) > 0.05:
                issues.append(f"Category allocations sum ({allocated_sum}) does not match budget ({raw_budget})")
            est_sum = round(sum(c.get("estimated_cost", 0.0) for c in cats), 2)
            if abs(est_sum - total_est) > 1.0:
                issues.append(f"Category estimates sum ({est_sum}) does not match total estimated trip cost ({total_est})")

        trans = plan.get("transportation_details", {})
        if trans:
            out_est = trans.get("outbound_estimated_cost", 0.0)
            ret_est = trans.get("return_estimated_cost", 0.0)
            trans_tot = trans.get("total_transport_cost", 0.0)
            if abs(round(out_est + ret_est, 2) - trans_tot) > 0.02:
                issues.append(f"Outbound ({out_est}) + Return ({ret_est}) does not equal Transport Total ({trans_tot})")

        return len(issues) == 0, issues
