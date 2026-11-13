import google.generativeai as genai
import os
import json
import urllib.parse
from typing import List, Dict, Any, Optional
from groq import Groq

from dotenv import load_dotenv

load_dotenv()

class AIServiceUnavailable(Exception):
    pass

class AIProviderAuthenticationError(Exception):
    pass

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

import logging
logger = logging.getLogger(__name__)

# Try models in order — fall back if quota/unavailable
MODELS = ["gemini-2.5-flash", "gemini-2.0-flash-lite", "gemini-1.5-flash-latest", "gemini-1.5-pro-latest"]
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = "llama-3.3-70b-versatile"

gemini_key = os.getenv("GEMINI_API_KEY", "")
logger.info(f"[AI] Provider: Gemini")
logger.info(f"[AI] API key configured: {'true' if gemini_key else 'false'}")
logger.info(f"[AI] API key length: {len(gemini_key)}")

logger.info(f"[AI] Provider: Groq")
logger.info(f"[AI] API key configured: {'true' if GROQ_API_KEY else 'false'}")
logger.info(f"[AI] API key length: {len(GROQ_API_KEY)}")


def _groq(prompt: str, system: str = None) -> str:
    """Call Groq API using the official SDK."""
    if not GROQ_API_KEY:
        raise AIProviderAuthenticationError("No Groq API key configured.")
    client = Groq(api_key=GROQ_API_KEY)
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    completion = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=messages,
        temperature=0.7,
        max_tokens=2048,
    )
    return completion.choices[0].message.content


def _ai(prompt: str, system: str = None) -> str:
    """Helper: call Gemini with automatic model fallback, then Groq."""
    for model_name in MODELS:
        try:
            kwargs = {"model_name": model_name}
            if system:
                kwargs["system_instruction"] = system
            model = genai.GenerativeModel(**kwargs)
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            err = str(e)
            if (
                "401" in err
                or "403" in err
                or "invalid authentication" in err.lower()
                or "api key" in err.lower()
            ):
                # We could raise AIProviderAuthenticationError immediately, but we want to fall back to Groq
                pass

            if (
                "429" in err
                or "quota" in err.lower()
                or "ResourceExhausted" in err
                or "404" in err
                or "NotFound" in err
                or "not found" in err.lower()
                or "not supported" in err.lower()
                or "401" in err
                or "403" in err
                or "invalid authentication" in err.lower()
                or "api key" in err.lower()
            ):
                continue
            
            # If it's a completely unexpected error, we'll still log it but try to fall back to Groq
            print(f"Gemini API Error: {err}")
            break # Break out of Gemini loop and try Groq

    # All Gemini models exhausted — try Groq
    try:
        return _groq(prompt, system)
    except AIProviderAuthenticationError:
        raise
    except Exception as e:
        err_msg = str(e).lower()
        if "401" in err_msg or "invalid_api_key" in err_msg or "authentication" in err_msg:
            raise AIProviderAuthenticationError(f"Groq authentication failed: {str(e)}")
        raise AIServiceUnavailable(f"All AI providers failed. Last error: {str(e)}")


# ──────────────────────────────────────────────
# ITINERARY
# ──────────────────────────────────────────────

def check_budget_alert(
    destination: str,
    days: int,
    budget: float,
    currency: str = "USD",
    adults: int = 1,
    children: int = 0,
    origin_city: str = "Coimbatore",
    tier: str = "mid_range"
) -> dict:
    """Analyze budget using Central Budget Allocation Engine and return validation result."""
    try:
        from app.services.budget_allocation_service import BudgetAllocationService
        plan = BudgetAllocationService.calculate_plan(
            total_budget=budget,
            currency=currency,
            tier=tier,
            destination=destination,
            origin_city=origin_city,
            days=days,
            adults=adults,
            children=children
        )
        if not plan["is_feasible"]:
            return {
                "has_warning": True,
                "is_feasible": False,
                "estimated_minimum": plan["total_estimated_trip_cost"],
                "total_estimated_trip_cost": plan["total_estimated_trip_cost"],
                "shortfall": plan["shortfall"],
                "shortfall_pct": plan["shortfall_percentage"],
                "user_budget": budget,
                "currency": currency,
                "message": plan["feasibility_note"],
                "categories": plan["categories"],
                "transportation_details": plan.get("transportation_details"),
                "affordable_alternatives": plan.get("affordable_alternatives", []),
                "suggestions": [
                    f"Increase travel budget to at least {plan['formatted_total_estimated_cost']}",
                    f"Reduce travel duration to {plan.get('suggested_duration_days', 2)} days",
                    "Choose an affordable alternative destination"
                ]
            }
        return {
            "has_warning": False,
            "is_feasible": True,
            "estimated_minimum": plan["total_estimated_trip_cost"],
            "total_estimated_trip_cost": plan["total_estimated_trip_cost"],
            "user_budget": budget,
            "currency": currency,
            "transportation_details": plan.get("transportation_details")
        }
    except Exception as e:
        print(f"[check_budget_alert fallback]: {e}")
        min_per_day_usd = 60.0
        rate_map = {"INR": 3500.0, "EUR": 70.0, "GBP": 60.0, "JPY": 9000.0, "AUD": 90.0, "CAD": 85.0}
        min_per_day = rate_map.get(currency.upper(), min_per_day_usd)
        estimated_minimum = min_per_day * max(days, 1) * max(1, adults + children)

        if budget > 0 and budget < estimated_minimum:
            return {
                "has_warning": True,
                "is_feasible": False,
                "estimated_minimum": estimated_minimum,
                "shortfall": round(estimated_minimum - budget, 2),
                "user_budget": budget,
                "currency": currency,
                "message": f"⚠️ Budget Alert: Your budget ({currency} {budget:,.0f}) is lower than the estimated minimum cost ({currency} {estimated_minimum:,.0f}) for {days} day(s) in {destination}.",
                "suggestions": [
                    "Increase travel budget",
                    "Reduce travel days",
                    "Choose budget hotels or hostels",
                    "Skip paid attractions and visit free sights",
                    "Travel during off season",
                    "Use public buses and metros instead of taxis"
                ]
            }
        return {"has_warning": False, "is_feasible": True, "estimated_minimum": estimated_minimum, "user_budget": budget, "currency": currency}


from .poi_service import fetch_real_pois_for_destination

def schedule_unique_multiday_itinerary(destination: str, days: int) -> Dict[int, Dict[str, Any]]:
    """
    Unique Itinerary Scheduler:
    1. Collects all real POIs for destination via OpenStreetMap / Wikipedia APIs.
    2. De-duplicates POIs and maintains a `used_places` set across ALL days.
    3. Distributes POIs intelligently:
       - Morning -> Sightseeing / Nature / Park
       - Afternoon -> Museum / Culture / Heritage
       - Lunch -> Local Restaurant / Dining
       - Evening -> Shopping / Viewpoint / Market
    4. If days exceed available unique POIs:
       - Schedules day trips to nearby towns, scenic drives, cultural workshops, or food trails.
       - Appends notice: "Additional exploration day generated due to limited unique attractions."
    5. Zero generic placeholder names.
    """
    pois = fetch_real_pois_for_destination(destination)
    used_places = set()
    daily_schedule = {}

    for d in range(1, days + 1):
        day_pois = []
        is_extended_exploration = False

        # Morning: Sightseeing / Nature / Park
        m_poi = next((p for p in pois if p["name"] not in used_places and p.get("category") in ["Sightseeing", "Viewpoint"]), None)
        if not m_poi:
            m_poi = next((p for p in pois if p["name"] not in used_places), None)
        if m_poi:
            used_places.add(m_poi["name"])
            day_pois.append({"time": "Morning (09:00 AM)", "category": "Sightseeing", "name": m_poi["name"], "desc": m_poi.get("description", "")})

        # Lunch: Local Dining
        l_poi = next((p for p in pois if p["name"] not in used_places and p.get("category") == "Restaurant"), None)
        if not l_poi:
            l_poi = next((p for p in pois if p["name"] not in used_places), None)
        if l_poi:
            used_places.add(l_poi["name"])
            day_pois.append({"time": "Lunch (01:00 PM)", "category": "Restaurant", "name": l_poi["name"], "desc": l_poi.get("description", "")})

        # Afternoon: Museum / Culture / Heritage
        a_poi = next((p for p in pois if p["name"] not in used_places and p.get("category") in ["Museum", "Culture"]), None)
        if not a_poi:
            a_poi = next((p for p in pois if p["name"] not in used_places), None)
        if a_poi:
            used_places.add(a_poi["name"])
            day_pois.append({"time": "Afternoon (03:00 PM)", "category": "Museum/Culture", "name": a_poi["name"], "desc": a_poi.get("description", "")})

        # Evening: Shopping / Viewpoint / Market
        e_poi = next((p for p in pois if p["name"] not in used_places and p.get("category") in ["Shopping", "Viewpoint"]), None)
        if not e_poi:
            e_poi = next((p for p in pois if p["name"] not in used_places), None)
        if e_poi:
            used_places.add(e_poi["name"])
            day_pois.append({"time": "Evening (06:00 PM)", "category": "Shopping/Viewpoint", "name": e_poi["name"], "desc": e_poi.get("description", "")})

        # If day has fewer than 2 unique POIs, schedule an extended exploration activity
        if len(day_pois) < 2:
            is_extended_exploration = True
            from app.services.route_optimizer import destination_has_rail
            has_rail = destination_has_rail(destination)
            rail_act_name = "Scenic Mountain Railway & Leisure Trail" if has_rail else f"Scenic Nature & Coastal Trail in {destination}"
            rail_act_desc = f"Enjoy scenic train journeys and relaxing nature trails near {destination}." if has_rail else f"Enjoy scenic road drives and relaxing nature trails near {destination}."

            extended_activities = [
                {"name": f"Day Trip to Nearby Towns & Countryside around {destination}", "desc": f"Explore picturesque villages and scenic landscapes surrounding {destination}."},
                {"name": f"Local Culinary & Cooking Workshop in {destination}", "desc": f"Learn authentic regional recipes from local chefs in {destination}."},
                {"name": f"Heritage Walking Trail & Local Artisan Craft Experience", "desc": f"Walk through historic quarters and meet traditional artisans in {destination}."},
                {"name": rail_act_name, "desc": rail_act_desc}
            ]
            ext = extended_activities[(d - 1) % len(extended_activities)]
            day_pois.append({"time": "Full Day", "category": "Extended Experience", "name": ext["name"], "desc": ext["desc"]})

        daily_schedule[d] = {
            "day": d,
            "pois": day_pois,
            "is_extended_exploration": is_extended_exploration,
            "notice": "Additional exploration day generated due to limited unique attractions." if is_extended_exploration else None
        }

    return daily_schedule

def generate_complete_itinerary(destination: str, days: int, budget: float,
                                interests: str, travel_type: str,
                                group_size: int = 1, currency: str = "USD",
                                origin_city: str = "Coimbatore",
                                is_budget_friendly: bool = False) -> str:
    """Generate a 100% complete, non-truncated multi-part itinerary with day validation."""
    days = max(1, min(days, 30))
    budget_note = "Focus on budget hostels, free sights, street food, and public transit." if is_budget_friendly else ""
    origin = origin_city if origin_city else "Coimbatore"

    # Pre-calculate unique POI assignments across all days
    unique_schedule = schedule_unique_multiday_itinerary(destination, days)

    parts = []

    # Format assigned POIs for Days 1 to min(days, 3)
    p1_day_assignments = []
    for d in range(1, min(days, 3) + 1):
        sched = unique_schedule[d]
        p_list = "\n".join([f"  - {p['time']}: {p['name']} ({p['category']})" for p in sched["pois"]])
        note_str = f"\n  - Note: {sched['notice']}" if sched["notice"] else ""
        p1_day_assignments.append(f"Day {d} Assigned Unique Sights:\n{p_list}{note_str}")
    p1_assigned_str = "\n\n".join(p1_day_assignments)

    # PART 1: Overview, Home-to-Destination Transport, Hotel Options, and Initial Days (1..min(days, 3))
    p1_prompt = f"""
    You are WanderWise Senior AI Travel Planner. Create Part 1 of a complete {days}-day Travel Planner.
    Origin City: {origin}
    Destination: {destination}
    Duration: {days} Days
    Total Budget: {budget} {currency}
    Interests: {interests}
    Travel Style: {travel_type}
    Group Size: {group_size} person(s)
    {budget_note}

    ASSIGNED UNIQUE POIS (MUST USE EXACTLY THESE NAMES FOR EACH DAY. DO NOT REUSE NAMES OR INVENT PLACEHOLDERS LIKE 'HERITAGE PROMENADE'):
    {p1_assigned_str}

    MUST INCLUDE IN THIS EXACT FORMAT:

    # 🌍 {days}-Day Complete Travel Planner: {destination}

    ## 📋 Trip Overview
    - **Destination**: {destination}
    - **Origin City**: {origin}
    - **Duration**: {days} Days
    - **Travel Style**: {travel_type.title()}
    - **Budget**: {currency} {budget:,.0f}
    - **Best Season**: Spring / Autumn
    - **Currency**: {currency}
    - **Language**: Local Language
    - **Emergency Numbers**: Police: 110 | Ambulance: 119
    - **Estimated Total Cost**: {currency} {budget*0.85:,.0f}

    ## ✈️ Transport from {origin} to {destination}
    - **Recommended Flight**: Express Transit (~11 hrs, {currency} {budget*0.25:,.0f}) | Bag: 23kg
    - **Alternative Option**: Connecting Train / Flight (~14 hrs, {currency} {budget*0.28:,.0f})

    ## 🏨 Hotel Recommendations
    - 🌟 **Recommended**: Central City Hotel ({currency} {budget*0.05:,.0f}/night)
    - 💰 **Budget Hostels**: Backpacker Hub ({currency} {budget*0.02:,.0f}/night)

    ---
    Generate Days 1 to {min(days, 3)} now.
    For EVERY Day include:
    - **Weather Suggestion**: Temp, Rain Chance, UV Index, Clothing Tip.
    - **Daily Timeline**: Timeline featuring the assigned unique POIs for this day.
    - **Morning, Afternoon, Evening, Night** Schedule using assigned POIs.
    - **Transport Between Attractions**: Previous Place -> Next Place (Distance km, Travel Time, Preferred Transport).
    - **AI Tips**: Best photo spot, hidden spot, crowd avoidance.
    - **Restaurant Recommendations**: Breakfast, Lunch, Dinner.
    - **Daily Expense Breakdown**: Food, Transport, Entry Fees, Shopping, Hotel, Daily Total.
    """
    try:
        part1 = _ai(p1_prompt)
        parts.append(part1)

        # PART 2: Subsequent Days in 3-day Chunks if days > 3
        current_day = 4
        while current_day <= days:
            end_chunk = min(current_day + 2, days)

            chunk_assignments = []
            for cd in range(current_day, end_chunk + 1):
                sched = unique_schedule[cd]
                p_list = "\n".join([f"  - {p['time']}: {p['name']} ({p['category']})" for p in sched["pois"]])
                note_str = f"\n  - Note: {sched['notice']}" if sched["notice"] else ""
                chunk_assignments.append(f"Day {cd} Assigned Unique Sights:\n{p_list}{note_str}")
            chunk_assigned_str = "\n\n".join(chunk_assignments)

            p_chunk_prompt = f"""
            Continue the {destination} travel planner. Generate ONLY Days {current_day} to {end_chunk}.
            Origin City: {origin} | Total Days: {days} | Currency: {currency} | Budget: {budget}

            ASSIGNED UNIQUE POIS FOR THESE DAYS (STRICT ZERO DUPLICATE RULE - DO NOT INVENT PLACEHOLDERS):
            {chunk_assigned_str}

            For EACH Day ({current_day} to {end_chunk}), include:
            ### Day X: [Catchy Day Title]
            - **Weather Suggestion**: Temp, Rain Chance %, Clothing Recommendation.
            - **Daily Timeline**: Timeline using assigned unique POIs.
            - **Morning, Afternoon, Evening, Night** activities with place name, hours, duration, fee.
            - **Transport Between Attractions**: Previous Place -> Next Place.
            - **AI Travel Tips**: Best Photo Spot, Hidden Spot, Avoid Crowds.
            - **Restaurant Recommendations**: Breakfast, Lunch, Dinner.
            - **Daily Expense Breakdown**: Daily Total.
            """

            chunk_text = _ai(p_chunk_prompt)
            parts.append(chunk_text)
            current_day = end_chunk + 1

        # PART 3: Return Journey Plan & Overall Budget Calculation
        ret_cost = int(budget * 0.25)
        round_transit = int(budget * 0.50)
        acc_cost = int(budget * 0.25)
        food_cost = int(budget * 0.15)
        local_cost = int(budget * 0.05)
        act_cost = int(budget * 0.05)
        buf_cost = int(budget * 0.05)
        grand_total = int(budget * 0.90)
        rem_budget = int(budget * 0.10)

        p_final_prompt = f"""
        Provide the Return Journey Plan and Overall Budget Summary for {destination} trip ({days} days, budget: {budget} {currency}, origin: {origin}).

        MUST INCLUDE:
        ## Return Journey Plan
        - **Route**: {destination} -> Airport / Main Station -> Flight / Train -> {origin}
        - **Estimated Return Cost**: {currency} {ret_cost:,}
        - **Total Round Trip Transit Cost**: {currency} {round_transit:,}

        ## Overall Budget Calculation
        - **Round-trip Flights/Transit**: {currency} {round_transit:,}
        - **Hotels / Accommodation**: {currency} {acc_cost:,}
        - **Food & Dining**: {currency} {food_cost:,}
        - **Local Transport**: {currency} {local_cost:,}
        - **Entry Tickets & Activities**: {currency} {act_cost:,}
        - **Emergency Buffer & Visa**: {currency} {buf_cost:,}
        - ---
        - **Grand Total Estimated Cost**: {currency} {grand_total:,}
        - **Remaining Budget**: {currency} {rem_budget:,}
        - **Budget Usage**: 90%

        ## Smart Packing Recommendations
        - Clothing for local climate, Walking Shoes, Universal Power Adapter, Travel Documents.
        """
        final_summary = _ai(p_final_prompt)
        parts.append(final_summary)

        full_itinerary = "\n\n".join(parts)

        # VALIDATION & AUTO-REPAIR LOOP
        # Ensure Day 1 to Day N exist in full_itinerary
        missing_days = []
        for d in range(1, days + 1):
            if f"Day {d}" not in full_itinerary and f"day {d}" not in full_itinerary.lower():
                missing_days.append(d)

        if missing_days:
            for md in missing_days:
                repair_prompt = (
                    "Generate missing Day " + str(md) + " for " + str(destination) + " travel planner (" + str(days) + " days, currency: " + str(currency) + ").\n"
                    "Include Daily Timeline, Morning, Afternoon, Evening, Night, Transport Between Attractions, AI Tips, Restaurants, and Daily Expense Breakdown."
                )
                repaired_day = _ai(repair_prompt)
                full_itinerary += f"\n\n### Day {md}: Additional Highlights of {destination}\n" + repaired_day

        return full_itinerary

    except Exception:
        return _fallback_itinerary(destination, days, budget, currency, origin)


def generate_itinerary(destination: str, days: int, budget: float,
                       interests: str, travel_type: str,
                       group_size: int = 1, currency: str = "USD",
                       is_budget_friendly: bool = False,
                       origin_city: str = "Coimbatore") -> str:
    return generate_complete_itinerary(
        destination=destination,
        days=days,
        budget=budget,
        interests=interests,
        travel_type=travel_type,
        group_size=group_size,
        currency=currency,
        origin_city=origin_city,
        is_budget_friendly=is_budget_friendly
    )


def replan_itinerary(current_itinerary: str, modification_request: str) -> str:
    prompt = (
        "You are an AI travel assistant. The user wants to modify their existing itinerary.\n\n"
        "Current Itinerary:\n" + str(current_itinerary) + "\n\n"
        "User's modification request:\n" + str(modification_request) + "\n\n"
        "Please provide the updated itinerary in the exact same complete format as the original, "
        "incorporating the requested changes smoothly without omitting any existing days."
    )
    try:
        return _ai(prompt)
    except Exception as e:
        raise


def _fallback_itinerary(destination: str, days: int, budget: float, currency: str = "USD", origin_city: str = "Coimbatore") -> str:
    daily = budget / max(days, 1)
    trans_cost = budget * 0.20
    acc_cost = budget * 0.35
    food_cost = budget * 0.20
    act_cost = budget * 0.15
    buf_cost = budget * 0.10
    origin = origin_city if origin_city else "Coimbatore"

    lines = [f"# 🌍 {days}-Day Complete Travel Planner: {destination}\n"]
    lines.append("## 📋 Trip Overview")
    lines.append(f"- **Destination**: {destination} | **Origin City**: {origin}")
    lines.append(f"- **Duration**: {days} Days | **Budget**: {currency} {budget:,.0f}")
    lines.append(f"- **Currency**: {currency} | **Language**: Local | **Emergency Numbers**: 110 / 119")
    lines.append(f"- **Overall AI Match**: 98% | **Trip Difficulty**: Easy | **Avg Walking**: 7 km/day\n")

    lines.append(f"## ✈️ Transport from {origin} to {destination}")
    lines.append(f"- ✈️ **Recommended Flight**: Express Airline (~11 hrs, {currency} {trans_cost*0.8:.0f}) | Bag: 23kg")
    lines.append(f"- 🚆 **Alternative Option**: Connecting Train / Flight (~14 hrs, {currency} {trans_cost*0.9:.0f})")
    lines.append(f"- 🚕 **Airport Taxi / Metro Cost**: {currency} {trans_cost*0.1:.0f}\n")

    lines.append("## 🏨 Hotel Recommendations")
    lines.append(f"- 🌟 **Recommended**: Central City Hotel ({currency} {acc_cost/days:.0f}/night)")
    lines.append(f"- 💰 **Budget Option**: Backpacker Hostel ({currency} {acc_cost/days*0.5:.0f}/night)")
    lines.append(f"- 💎 **Luxury Stay**: Grand Resort ({currency} {acc_cost/days*2:.0f}/night)\n")

    for d in range(1, days + 1):
        lines.append(f"### Day {d}: Exploring Best Highlights of {destination}")
        lines.append(f"🌤️ **Weather Suggestion**: 22°C, 10% Rain | Clothing: Comfortable walking gear")
        lines.append(f"⏰ **Daily Timeline**: 8:00 AM Breakfast → 9:00 AM Sightseeing → 1:00 PM Lunch → 3:00 PM Cultural Spot → 7:00 PM Dinner → 9:00 PM Evening Walk")
        
        lines.append(f"🌅 **Morning**: Main Heritage Landmark & City Gardens")
        lines.append(f"   - *Hours*: 09:00 AM - 12:30 PM | *Duration*: 3.5 hrs | *Entry*: {currency} {act_cost/days*0.5:.0f}")
        lines.append(f"   - *AI Tip*: Arrive 15 mins early for photo spots without crowds")

        lines.append(f"🚕 **Transport to Afternoon Attraction**:")
        lines.append(f"   - *Route*: Heritage Landmark → Old Town Square (1.8 km, 15 mins)")
        lines.append(f"   - *Preferred Transport*: Metro Line 1 ({currency} {trans_cost/days*0.3:.0f}) | Alt: Taxi ({currency} {trans_cost/days*0.8:.0f}) / Walk (Free)")
        lines.append(f"   - *Google Maps*: [View Map Route](https://www.google.com/maps/search/?api=1&query={urllib.parse.quote('Old Town ' + destination)})")


        lines.append(f"☀️ **Afternoon**: Historic District & Traditional Market")
        lines.append(f"   - *Hours*: 01:00 PM - 05:00 PM | *Entry*: Free")

        lines.append(f"🌆 **Evening**: Scenic Sunset Viewpoint")
        lines.append(f"🌙 **Night**: Local Food Market & Nightlife")

        lines.append(f"🍱 **Restaurants**: Breakfast: Hotel Cafe | Lunch: Local Market Stall | Dinner: Regional Specialty Dining")
        lines.append(f"💰 **Daily Expense Breakdown**: Food: {currency} {food_cost/days:.0f} | Transport: {currency} {trans_cost/days:.0f} | Hotel: {currency} {acc_cost/days:.0f} | Daily Total: {currency} {daily:.0f}\n")

    lines.append("## 🔄 Return Journey Plan")
    lines.append(f"- **Route**: {destination} Hotel → Airport → Flight → {origin}")
    lines.append(f"- **Estimated Return Cost**: {currency} {trans_cost*0.8:.0f}")
    lines.append(f"- **Total Round-trip Transit Cost**: {currency} {trans_cost*1.6:.0f}\n")

    lines.append("## 💵 Overall Budget Calculation")
    lines.append(f"- ✈️ **Round-trip Flights/Transit**: {currency} {trans_cost*1.6:.0f}")
    lines.append(f"- 🏨 **Hotels / Accommodation**: {currency} {acc_cost:.0f}")
    lines.append(f"- 🍲 **Food & Dining**: {currency} {food_cost:.0f}")
    lines.append(f"- 🎟️ **Activities & Entry Fees**: {currency} {act_cost:.0f}")
    lines.append(f"- 🛡️ **Emergency Buffer**: {currency} {buf_cost:.0f}")
    lines.append(f"---")
    lines.append(f"### 💳 **Grand Total**: {currency} {budget:,.0f} | **Remaining Budget**: {currency} 0")
    return "\n".join(lines)


# ──────────────────────────────────────────────
# AI CHAT
# ──────────────────────────────────────────────

def chat_with_assistant(user_message: str, destination: str = "") -> str:
    system_prompt = """You are WanderWise, an AI travel assistant.
    Help users with travel planning, recommendations, local tips,
    transportation guidance, and any travel-related questions.
    Be friendly, concise, and practical."""

    context = f"User is traveling to: {destination}" if destination else ""
    full_prompt = f"{context}\n\n{user_message}".strip()
    return _ai(full_prompt, system=system_prompt)


# ──────────────────────────────────────────────
# PACKING LIST
# ──────────────────────────────────────────────

def generate_packing_list(destination: str, start_date: str, end_date: str, duration: int,
                          travel_type: str, daily_activities: list, weather: str = "", season: str = "", climate: str = "") -> str:
    import json
    daily_activities_str = json.dumps(daily_activities, indent=2) if daily_activities else "[]"
    prompt = f"""
    You are an expert AI Travel Packing Assistant. Generate a highly personalized packing list.
    
    Context:
    - Destination: {destination}
    - Dates: {start_date} to {end_date}
    - Duration: {duration} days
    - Travel Style: {travel_type}
    - Season: {season}
    - Climate: {climate}
    - Expected Weather: {weather if weather else 'Unknown'}
    - Planned Daily Activities & Recommended Gear: {daily_activities_str}

    Rules:
    1. The itinerary provided is authoritative. Never invent dummy activities (e.g. no "Explore Hawaii" placeholders).
    2. Use the supplied daily activities and their mapped recommended gear to plan the packing.
    3. Calculate quantities logically based on duration, climate, and laundry availability (e.g., for 13 days, suggest 5-7 shirts, not 13).
    4. Exclude completely irrelevant items (e.g., no heavy coats for a tropical summer trip).
    5. Avoid 1 item per trip day, and avoid unnecessary duplicate items. Provide context-aware overpacking warnings.
    6. Calculate a packing_score out of 100 based on preparedness for the specific climate and activities.
    
    Output exactly this JSON structure and nothing else:
    {{
      "context": {{
        "destination": "{destination}",
        "start_date": "{start_date}",
        "end_date": "{end_date}",
        "duration_days": {duration},
        "season": "{season}",
        "climate": "{climate}",
        "temperature": "estimated temperature range",
        "rain_probability": "estimated rain probability",
        "weather_source": "LLM seasonal estimation based on destination and dates",
        "activities": {daily_activities_str}
      }},
      "categories": [
        {{
          "name": "Clothing",
          "items": [
            {{
              "name": "Item Name",
              "quantity": 1,
              "weight_kg": 0.5,
              "essential": true,
              "rationale": "Reason for inclusion based on climate/activity",
              "packed": false
            }}
          ]
        }}
      ],
      "warnings": [
        {{
          "type": "overpacking",
          "message": "Specific contextual warning"
        }}
      ],
      "missing_essentials": ["Item that is highly recommended but often forgotten"],
      "packing_score": 85,
      "daily_gear": [
        {{
          "day": 1,
          "date": "2026-08-08",
          "activities": [
            {{
              "name": "Actual DB activity name",
              "recommended_gear": [
                "sunscreen",
                "water bottle"
              ]
            }}
          ]
        }}
      ]
    }}
    
    CRITICAL JSON RULES:
    1. You MUST return ONLY valid JSON.
    2. Do not use Markdown. Do not wrap the response in ```json or ``` blocks.
    3. Do not include any explanations before or after the JSON.
    4. Use double quotes for every JSON key and every string value. Never use Python single-quoted strings.
    5. Booleans must be true/false (lowercase). Null must be null.
    6. No comments, no trailing commas.
    7. The activities field must be a valid JSON array of strings.
    
    The response must be directly parseable using JSON.parse / json.loads.
    """
    return _ai(prompt)


# ──────────────────────────────────────────────
# SMART TRANSIT
# ──────────────────────────────────────────────

def transit_guide(from_location: str, to_location: str, city: str) -> str:
    prompt = f"""
    You are a smart public transport navigator for {city}.
    A traveler wants to go from "{from_location}" to "{to_location}".

    Provide a detailed step-by-step transit guide in this exact JSON format:
    {{
      "summary": "Brief route summary",
      "total_time": "Estimated time e.g. 45 minutes",
      "total_fare": "Estimated fare e.g. ₹40 or $2",
      "walking_distance": "Total walking distance e.g. 800m",
      "steps": [
        {{
          "type": "walk|bus|metro|train|auto",
          "instruction": "Walk to XYZ Bus Stop",
          "detail": "Head north on Main Street for 200m",
          "duration": "5 min",
          "fare": "Free"
        }}
      ],
      "tips": ["Tip 1", "Tip 2"],
      "alternatives": [
        {{"name": "Fastest Route", "time": "30 min", "cost": "$5", "mode": "Taxi"}},
        {{"name": "Cheapest Route", "time": "60 min", "cost": "$1", "mode": "Bus"}}
      ]
    }}

    Only return the JSON. No extra text.
    """
    res = _ai(prompt)
    if "quota exceeded" in res.lower() or "⚠️" in res:
        return f"""
        {{
          "summary": "⚠️ AI quota exceeded. Showing an estimated generic route for {city}.",
          "total_time": "30 mins",
          "total_fare": "Local standard fare",
          "walking_distance": "500m",
          "steps": [
            {{
              "type": "walk",
              "instruction": "Walk towards the nearest main transit hub",
              "detail": "Head straight for about 5 minutes",
              "duration": "5 min",
              "fare": "Free"
            }},
            {{
              "type": "taxi",
              "instruction": "Take a local taxi or transit to {to_location}",
              "detail": "Ask the driver or staff for the fastest route",
              "duration": "25 min",
              "fare": "Standard fare"
            }}
          ],
          "tips": ["Always carry small change", "Verify the destination before boarding"],
          "alternatives": []
        }}
        """
    return res


# ──────────────────────────────────────────────
# RISK ANALYZER
# ──────────────────────────────────────────────

def analyze_travel_risk(destination: str, travel_dates: str, budget: float) -> str:
    prompt = f"""
    You are a travel risk analyzer. Analyze travel risks for:
    Destination: {destination}
    Travel dates: {travel_dates}
    Budget: ${budget}

    Return a JSON object with scores out of 100 (where 100 = 100% risk / highest danger, 0 = 0% risk / totally safe).
    Format exactly like this:
    {{
      "overall_score": 20,
      "overall_label": "Safe | Moderate Risk | High Risk",
      "weather_risk": 15,
      "crowd_risk": 30,
      "safety_risk": 10,
      "top_recommendations": ["...", "...", "..."],
      "emergency_numbers": {{"police": "112", "ambulance": "108", "fire": "101", "tourist_helpline": "1363"}}
    }}

    Only return JSON.
    """
    return _ai(prompt)


# ──────────────────────────────────────────────
# SCAM ALERTS
# ──────────────────────────────────────────────

def get_scam_alerts(destination: str) -> str:
    prompt = f"""
    List common tourist scams and safety alerts for travelers visiting {destination}.

    Return JSON:
    {{
      "destination": "{destination}",
      "safety_rating": "<Safe | Moderate | Caution>",
      "scams": [
        {{
          "name": "<Name of a specific local scam>",
          "severity": "<High | Medium | Low>",
          "description": "<How this specific scam works in {destination}>",
          "warning_signs": ["<sign 1>", "<sign 2>"],
          "how_to_avoid": "<Practical advice>"
        }}
      ],
      "general_safety_tips": ["<tip 1>", "<tip 2>"],
      "safe_areas": ["<area 1>", "<area 2>"],
      "avoid_areas": ["<area 1>"]
    }}

    Only return JSON.
    """
    return _ai(prompt)


# ──────────────────────────────────────────────
# RECOMMENDATIONS
# ──────────────────────────────────────────────

def get_recommendations(destination: str, category: str,
                        budget_level: str = "mid-range",
                        interests: str = "") -> str:
    prompt = f"""
    Recommend the best {category} for travelers visiting {destination}.
    Budget level: {budget_level}
    Interests: {interests if interests else 'general'}

    Return JSON array of 6 items:
    [
      {{
        "name": "Place/Hotel/Restaurant name",
        "description": "2-3 sentence description",
        "rating": 4.5,
        "price_range": "$ | $$ | $$$",
        "highlight": "One key highlight",
        "location": "Area/neighborhood",
        "best_for": "couples | families | solo | groups",
        "tip": "Insider tip"
      }}
    ]

    Only return the JSON array.
    """
    return _ai(prompt)


def get_hidden_gems(destination: str, interests: str = "") -> str:
    prompt = f"""
    Discover hidden gems, offbeat attractions, and authentic local experiences in {destination}.
    Interests: {interests if interests else 'general'}

    These should be places most tourists do not know about - local favorites, lesser-known spots.

    Return JSON array of 6 items:
    [
      {{
        "name": "Place name",
        "type": "Nature | Market | Cultural | Food | Adventure",
        "description": "What makes this place special",
        "why_hidden": "Why tourists miss this",
        "best_time": "Best time to visit",
        "local_tip": "What locals recommend doing there",
        "crowd_level": "Very Low | Low | Moderate",
        "location": "Approximate area"
      }}
    ]

    Only return the JSON array.
    """
    return _ai(prompt)


def get_categorized_recommendations(destination: str, interests: str = "",
                                   budget_level: str = "mid-range",
                                   travel_style: str = "solo",
                                   season: str = "current",
                                   user_prefs: dict = None) -> str:
    prefs_str = json.dumps(user_prefs) if user_prefs else "{}"
    prompt = f"""
    You are an expert AI travel concierge. Generate categorized place recommendations for {destination}.
    User Interests: {interests if interests else 'Sightseeing, Culture, Local Cuisine'}
    Budget Level: {budget_level}
    Travel Style: {travel_style}
    Season/Time: {season}
    User Preferences Profile: {prefs_str}

    Provide recommendations structured into 10 categories:
    1. Top Attractions
    2. Hidden Gems
    3. Cafes
    4. Restaurants
    5. Nature Spots
    6. Shopping Places
    7. Local Experiences
    8. Nightlife
    9. Historical Places
    10. AI Recommended Places

    Return a single JSON object formatted exactly like this:
    {{
      "destination": "{destination}",
      "ai_match_score": 95,
      "summary": "AI tailored recommendations based on your preferences.",
      "categories": {{
        "Top Attractions": [
          {{
            "name": "Attraction Name",
            "category": "Top Attractions",
            "description": "Engaging description",
            "address": "Location/Neighborhood, City",
            "rating": 4.8,
            "price_range": "$$",
            "budget_badge": "Budget Friendly",
            "ai_match_score": 98,
            "match_reasons": ["Matches Photography", "Budget Friendly", "Less Crowded"],
            "tags": ["Iconic", "Historic"],
            "open_status": "Open Now (9:00 AM - 6:00 PM)",
            "distance": "1.5 km from center",
            "crowd_prediction": "Moderate",
            "weather_badge": "Pleasant Weather",
            "transport_icon": "metro"
          }}
        ],
        "Hidden Gems": [],
        "Cafes": [],
        "Restaurants": [],
        "Nature Spots": [],
        "Shopping Places": [],
        "Local Experiences": [],
        "Nightlife": [],
        "Historical Places": [],
        "AI Recommended Places": []
      }}
    }}

    Each category should have 2-4 items. Make sure match_reasons explain personalized match score %!
    Return ONLY valid JSON.
    """
    return _ai(prompt)


# ──────────────────────────────────────────────
# WEATHER ACTIVITY ADVISOR
# ──────────────────────────────────────────────

def weather_activity_advisor(destination: str, weather_desc: str,
                              temperature: float) -> str:
    prompt = f"""
    A traveler is in {destination}.
    Current weather: {weather_desc}, {temperature} deg C

    Suggest smart activity recommendations based on this weather.

    Return JSON:
    {{
      "weather_summary": "Brief interpretation",
      "indoor_activities": [
        {{"name": "Activity", "reason": "Why good for this weather", "duration": "2 hours"}}
      ],
      "outdoor_activities": [
        {{"name": "Activity", "reason": "Why good for this weather", "duration": "3 hours"}}
      ],
      "what_to_wear": ["item1", "item2"],
      "ai_suggestion": "One proactive suggestion from WanderWise AI"
    }}

    Only return JSON.
    """
    return _ai(prompt)


# ──────────────────────────────────────────────
# AI TRAVEL MEMORY GENERATOR
# ──────────────────────────────────────────────

def generate_trip_memory(destination: str, start_date: str, end_date: str,
                         journal_entries: list, total_spent: float,
                         attractions_count: int = 0) -> str:
    entries_text = "\n".join(
        [f"- {e.get('title', 'Entry')}: {e.get('content', '')[:200]}" for e in journal_entries[:10]]
    )
    spent_val = int(total_spent)
    prompt = f"""
    Generate a warm, poetic AI travel memory summary for a completed trip.

    Trip details:
    - Destination: {destination}
    - Dates: {start_date} to {end_date}
    - Total spent: ${spent_val:,}
    - Attractions visited: {attractions_count}
    - Journal entries:
    {entries_text if entries_text else "No journal entries recorded."}

    Write a 3-4 paragraph travel memory that:
    1. Highlights the journey and key moments
    2. References specific journal entries warmly
    3. Includes stats naturally in the narrative
    4. Ends with an inspiring closing line

    Make it personal, vivid, and emotionally resonant.
    """
    return _ai(prompt)


# ──────────────────────────────────────────────
# AI COMPANION MODE
# ──────────────────────────────────────────────

def companion_suggestions(destination: str, current_day: int, total_days: int,
                          itinerary_snippet: str, weather: str = "") -> str:
    prompt = f"""
    You are WanderWise AI Companion - a proactive travel guide.
    
    Traveler info:
    - Destination: {destination}
    - Day {current_day} of {total_days}
    - Current weather: {weather if weather else 'not specified'}
    - Todays planned activities: {itinerary_snippet[:500] if itinerary_snippet else "free day"}

    Generate proactive, real-time travel companion suggestions.

    Return JSON:
    {{
      "greeting": "Personalized good morning/afternoon message",
      "weather_alert": null or "Alert message if weather affects plans",
      "suggestions": [
        {{"type": "timing | safety | food | transport | activity", "message": "Suggestion", "priority": "high|medium|low"}}
      ],
      "reminders": ["Reminder 1", "Reminder 2"],
      "did_you_know": "An interesting local fact about the destination",
      "progress_message": "You are on day X of Y - keep exploring!"
    }}

    Only return JSON.
    """
    return _ai(prompt)

# ──────────────────────────────────────────────
# DASHBOARD WIDGETS AI
# ──────────────────────────────────────────────

def get_language_guide(destination: str) -> str:
    prompt = f"""
    Provide a brief language guide for {destination}.
    Return JSON:
    {{
      "primary_language": "Language Name",
      "hello": "Translation for hello",
      "thank_you": "Translation for thank you",
      "help": "Translation for help me",
      "how_much": "Translation for how much is this",
      "goodbye": "Translation for goodbye",
      "cultural_tip": "A brief 1-sentence cultural tip about communication"
    }}
    Only return JSON.
    """
    return _ai(prompt)

def personalized_destinations(past_destinations: list) -> str:
    past_str = ", ".join(past_destinations) if past_destinations else "None yet"
    prompt = f"""
    A traveler has previously visited: {past_str}.
    Recommend 3 new, unique destinations they might like.
    Return JSON array:
    [
      {{
        "destination": "Name of new destination",
        "reason": "Why they would like it based on past trips",
        "vibe": "E.g., Relaxing, Adventure, Historic"
      }}
    ]
    Only return JSON array.
    """
    return _ai(prompt)

def translate_text(text: str, destination: str) -> str:
    prompt = f"""
    You are a real-time translator for a traveler in {destination}.
    Translate the following text into the primary local language of {destination}.
    If the text is already in the local language, translate it to English.
    Text to translate: "{text}"
    
    Return JSON format exactly like this:
    {{
      "original": "{text}",
      "translated": "<The translation>",
      "target_language": "<The name of the language translated to>"
    }}
    
    Only return JSON.
    """
    return _ai(prompt)


# ──────────────────────────────────────────────
# STRUCTURED FLEXIBLE ITINERARY ENGINE (Phase 1)
# ──────────────────────────────────────────────

def _clean_json_response(raw_text: str) -> dict:
    """Helper to strip markdown code blocks and load JSON cleanly."""
    clean = raw_text.strip()
    if clean.startswith("```json"):
        clean = clean[7:]
    if clean.startswith("```"):
        clean = clean[3:]
    if clean.endswith("```"):
        clean = clean[:-3]
    clean = clean.strip()
    return json.loads(clean)


def generate_structured_itinerary(destination: str, days: int, budget: float,
                                  interests: str = "sightseeing", travel_style: str = "solo",
                                  group_size: int = 1, currency: str = "USD",
                                  country: str = "", origin_city: str = "Coimbatore",
                                  origin_airport: str = "", destination_airport: str = "",
                                  accommodation_preference: str = "hotel",
                                  transportation: str = "flight",
                                  travel_companion: str = "solo",
                                  start_date: str = "", end_date: str = "",
                                  trip_preferences: dict = None,
                                  language: str = "English",
                                  generation_id: str = "") -> dict:
    """
    Generate day-by-day structured activities using AIEngine Orchestrator and 5-stage validation pipeline.
    """
    from app.ai.engine import AIEngine
    from app.core.currencies import get_currency_info
    from app.config.budget_presets import get_budget_preset

    curr_info = get_currency_info(currency)
    budget_breakdown = get_budget_preset(travel_style)
    activities_alloc = round(budget * (budget_breakdown.get("Activities", 15.0) / 100.0), 2)
    
    context_dict = {
        "destination": destination,
        "country": country if country else destination,
        "total_days": max(days, 1),
        "budget": budget,
        "currency_code": curr_info.code,
        "currency_symbol": curr_info.symbol,
        "currency_country": curr_info.country,
        "activities_budget": activities_alloc,
        "travel_style": travel_style,
        "group_size": group_size,
        "interests": interests,
        "origin_city": origin_city,
        "origin_airport": origin_airport,
        "destination_airport": destination_airport,
        "accommodation_preference": accommodation_preference,
        "transportation": transportation,
        "travel_companion": travel_companion,
        "start_date": start_date,
        "end_date": end_date,
        "trip_preferences": trip_preferences or {},
        "dietary_preferences": (trip_preferences or {}).get("dietary_preferences"),
        "preferred_climate": (trip_preferences or {}).get("preferred_climate"),
        "budget_tier": (trip_preferences or {}).get("budget_type") or (trip_preferences or {}).get("preferred_budget"),
        "language": language,
        "generation_id": generation_id
    }
    
    engine = AIEngine()
    response_envelope = engine.generate_trip(context_dict)
    
    trip_data = response_envelope.get("trip", {})
    if "days" not in trip_data and "itinerary_days" in trip_data:
        trip_data["days"] = trip_data["itinerary_days"]

    days_list = trip_data.get("days", [])
    print(f"[Pipeline Diagnostic Log] Destination: '{destination}' | Total Days: {days} | Generated Days: {len(days_list)}")

    has_empty_days = any(not d.get("activities") or len(d.get("activities")) == 0 for d in days_list)
    # Guarantee fallback if days_list is empty, incomplete, or contains zero-activity days
    if not days_list or len(days_list) < days or has_empty_days:
        print(f"[Pipeline Warning Log] Generated days incomplete or empty for '{destination}'. Invoking Unique Itinerary Scheduler fallback.")
        sched = schedule_unique_multiday_itinerary(destination, days)
        fallback_days = []
        time_slots = [
            ("08:30", "09:30", "morning", 60),
            ("09:45", "11:45", "morning", 120),
            ("12:00", "13:15", "afternoon", 75),
            ("13:30", "16:00", "afternoon", 150),
            ("16:30", "18:30", "evening", 120)
        ]
        for d in range(1, max(days, 1) + 1):
            existing = next((ex for ex in days_list if ex.get("day_number") == d and len(ex.get("activities", [])) > 0), None)
            if existing:
                fallback_days.append(existing)
                continue

            day_info = sched[d]
            acts = []
            for p_idx, poi in enumerate(day_info["pois"]):
                st, et, slot, dur_m = time_slots[min(p_idx, len(time_slots) - 1)]
                acts.append({
                    "start_time": st, "end_time": et, "duration_minutes": dur_m, "time_slot": slot,
                    "title": f"Explore {poi['name']}",
                    "description": poi.get("desc") or f"Experience {poi['name']} in {destination}.",
                    "place": {"name": poi['name'], "category": poi.get('category')},
                    "cost": {"amount": 0.0, "currency": currency, "symbol": curr_info.symbol, "estimated": False},
                    "ticket_price": 0.0,
                    "transport_mode": transportation or "walking", "transport_duration": "15 mins", "distance": "1.2 km",
                    "weather_suitability": "all-weather", "crowd_level": "moderate",
                    "ai_reason": f"System selected verified POI matching travel style",
                    "confidence_score": 0.98,
                    "metadata": {"tips": [f"Enjoy {poi['name']} at your own pace."], "nearby": []}
                })
            theme_title = f"Day {d}: {destination.title()} Exploration" if not day_info["is_extended_exploration"] else f"Day {d}: Extended Experience & Scenic Trail"
            fallback_days.append({
                "day_number": d,
                "title": theme_title,
                "theme_note": day_info["notice"] or "Explore unique top attractions & local culture",
                "activities": acts
            })
        trip_data["days"] = fallback_days

    # Validation check via FinalItineraryValidator
    from app.ai.validators.final_itinerary_validator import FinalItineraryValidator
    try:
        from datetime import datetime, date, timedelta
        s_date = datetime.strptime(start_date, "%Y-%m-%d").date() if start_date else date.today()
        e_date = datetime.strptime(end_date, "%Y-%m-%d").date() if end_date else s_date + timedelta(days=max(days, 1)-1)
    except Exception:
        from datetime import date, timedelta
        s_date = date.today()
        e_date = s_date + timedelta(days=max(days, 1)-1)

    is_valid, val_issues, validated_days = FinalItineraryValidator.validate_itinerary_payload(
        days_data=trip_data.get("days", []),
        destination=destination,
        start_date=s_date,
        end_date=e_date,
        expected_days=max(days, 1),
        currency=currency,
        interests=interests,
        directives=(trip_preferences or {}).get("ai_directives"),
        pace=(trip_preferences or {}).get("pace", "balanced"),
        transport_mode=transportation,
        accommodation_preference=accommodation_preference,
        dietary_preferences=(trip_preferences or {}).get("dietary_preferences") or (trip_preferences or {}).get("food"),
        travelers_count=group_size,
        adults_count=int((trip_preferences or {}).get("adults") or ((trip_preferences or {}).get("travelers") or {}).get("adults") or max(1, group_size - int((trip_preferences or {}).get("children") or ((trip_preferences or {}).get("travelers") or {}).get("children") or 0))),
        children_count=int((trip_preferences or {}).get("children") or ((trip_preferences or {}).get("travelers") or {}).get("children") or 0)
    )
    if validated_days:
        trip_data["days"] = validated_days
        if hasattr(FinalItineraryValidator, "last_interest_coverage_report") and FinalItineraryValidator.last_interest_coverage_report:
            if not isinstance(trip_data.get("metadata"), dict):
                trip_data["metadata"] = {}
            trip_data["metadata"]["interest_coverage_report"] = FinalItineraryValidator.last_interest_coverage_report
            trip_data["interest_coverage_report"] = FinalItineraryValidator.last_interest_coverage_report

    return trip_data



def regenerate_day_itinerary(destination: str, day_number: int,
                             locked_activities: list = None,
                             notes: str = "",
                             exclude_poi_names: list = None,
                             generation_id: str = "") -> list:
    """
    Regenerate activities for a single day while respecting user locked activities
    and strictly avoiding duplicate attractions already scheduled on other days.
    """
    locked_str = json.dumps(locked_activities or [])
    notes_val = notes if notes else "Fresh new mix of attractions"
    exclude_list = list(exclude_poi_names or [])
    from app.services.pricing.canonical_pricing_registry import normalize_place_entity_key
    seen_keys = {normalize_place_entity_key(n) for n in exclude_list if n}

    # Extract keys of locked activities
    for l_act in (locked_activities or []):
        l_name = l_act.get("title") or (l_act.get("place", {}).get("name") if isinstance(l_act.get("place"), dict) else "")
        if l_name:
            seen_keys.add(normalize_place_entity_key(l_name))

    system_instruction = "You are WanderWise AI. Return ONLY a valid JSON array of 3-4 activity objects for a single day."
    prompt = (
        f"Regenerate Day {day_number} itinerary for {destination}.\n"
        f"Special Requests / Notes: {notes_val}\n"
        f"LOCKED ACTIVITIES (DO NOT CHANGE OR OMIT THESE): {locked_str}\n"
        f"AVOID THESE VENUES (ALREADY VISITED ON OTHER DAYS): {json.dumps(exclude_list[:15])}\n\n"
        "Return a JSON array of 3-4 activity objects with start_time, end_time, time_slot, title, description, place, ticket_price, transport_mode, ai_reason.\n"
        "Ensure locked activities are preserved exactly in their original time slots.\n"
        "Only return JSON array."
    )
    raw_res = None
    try:
        raw_resp = _ai(prompt, system=system_instruction)
        res = _clean_json_response(raw_resp)
        raw_res = res if isinstance(res, list) else (res.get("activities", []) if isinstance(res, dict) else [])
    except Exception:
        raw_res = []

    # Combine locked activities with newly generated activities, ensuring no duplicate venues
    final_acts = list(locked_activities or [])
    for act in (raw_res or []):
        p_name = act.get("title") or (act.get("place", {}).get("name") if isinstance(act.get("place"), dict) else "")
        p_key = normalize_place_entity_key(p_name)
        if p_key and p_key not in seen_keys:
            seen_keys.add(p_key)
            final_acts.append(act)

    # If count is below 3 (e.g. LLM failure or offline), backfill from authentic POIs
    if len(final_acts) < 3:
        from app.services.poi_service import fetch_real_pois_for_destination
        real_pois = fetch_real_pois_for_destination(destination)
        for poi in real_pois:
            poi_key = normalize_place_entity_key(poi["name"])
            if poi_key not in seen_keys:
                seen_keys.add(poi_key)
                is_din = poi.get("is_dining") or any(k in poi.get("category", "").lower() for k in ["restaurant", "cafe", "dining"])
                final_acts.append({
                    "start_time": "14:00" if len(final_acts) == 1 else "16:30",
                    "end_time": "15:30" if len(final_acts) == 1 else "18:00",
                    "duration_minutes": 90,
                    "time_slot": "afternoon" if len(final_acts) == 1 else "evening",
                    "title": f"Explore {poi['name']}" if not is_din else f"Dining at {poi['name']}",
                    "description": poi.get("description") or f"Experience {poi['name']} in {destination}.",
                    "place": poi,
                    "ticket_price": float(poi.get("ticket_price") or 0.0) if not is_din else 0.0,
                    "meal_cost": float(poi.get("meal_cost") or 25.0) if is_din else None,
                    "activity_type": "meal" if is_din else "sightseeing",
                    "transport_mode": "Public Transit / Walking",
                    "ai_reason": f"✓ Fresh verified landmark in {destination}",
                    "confidence_score": 0.95
                })
                if len(final_acts) >= 3:
                    break

    return final_acts


# Canonical alias for itinerary day generation
generate_trip_days = generate_structured_itinerary
