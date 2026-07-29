import google.generativeai as genai
import os
import json
import urllib.parse
from groq import Groq

from dotenv import load_dotenv

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Try models in order — fall back if quota/unavailable
MODELS = ["gemini-2.5-flash", "gemini-2.0-flash-lite", "gemini-1.5-flash-latest", "gemini-1.5-pro-latest"]
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = "llama-3.3-70b-versatile"


def _groq(prompt: str, system: str = None) -> str:
    """Call Groq API using the official SDK."""
    if not GROQ_API_KEY:
        return "⚠️ AI quota exceeded and no Groq API key configured."
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
            # Fall through to next model on quota OR model-not-found errors
            if (
                "429" in err
                or "quota" in err.lower()
                or "ResourceExhausted" in err
                or "404" in err
                or "NotFound" in err
                or "not found" in err.lower()
                or "not supported" in err.lower()
            ):
                continue
            raise  # Re-raise unexpected errors

    # All Gemini models exhausted — try Groq
    try:
        return _groq(prompt, system)
    except Exception as e:
        return f"⚠️ All AI providers failed. Last error: {str(e)}"


# ──────────────────────────────────────────────
# ITINERARY
# ──────────────────────────────────────────────

def check_budget_alert(destination: str, days: int, budget: float, currency: str = "USD") -> dict:
    """Analyze budget and return warning dict if budget is below minimum threshold."""
    min_per_day_usd = 50.0
    rate_map = {"INR": 1800.0, "EUR": 45.0, "GBP": 40.0, "JPY": 6000.0, "AUD": 70.0, "CAD": 65.0}
    min_per_day = rate_map.get(currency.upper(), min_per_day_usd)
    estimated_minimum = min_per_day * max(days, 1)

    if budget > 0 and budget < estimated_minimum:
        return {
            "has_warning": True,
            "estimated_minimum": estimated_minimum,
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
    return {"has_warning": False, "estimated_minimum": estimated_minimum, "user_budget": budget, "currency": currency}


def generate_complete_itinerary(destination: str, days: int, budget: float,
                                interests: str, travel_type: str,
                                group_size: int = 1, currency: str = "USD",
                                origin_city: str = "Coimbatore",
                                is_budget_friendly: bool = False) -> str:
    """Generate a 100% complete, non-truncated multi-part itinerary with day validation."""
    days = max(1, min(days, 30))
    budget_note = "Focus on budget hostels, free sights, street food, and public transit." if is_budget_friendly else ""
    origin = origin_city if origin_city else "Coimbatore"

    parts = []

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
    - **Time Zone**: GMT+9
    - **Emergency Numbers**: Police: 110 | Ambulance: 119
    - **Visa Required**: Verify local passport rules
    - **Estimated Total Cost**: {currency} {budget*0.85:,.0f}
    - **Budget Remaining**: {currency} {budget*0.15:,.0f}
    - **Overall AI Match**: 98%
    - **Trip Difficulty**: Easy / Moderate
    - **Average Walking**: 6-8 km/day

    ## ✈️ Transport from {origin} to {destination}
    - **Recommended Flight**: IndiGo / ANA (~11 hrs, {currency} {budget*0.25:,.0f}) | Bag: 23kg
    - **Alternative Flight**: Air India (~13 hrs, {currency} {budget*0.28:,.0f})
    - **Budget Option**: Low-Cost Transit (~15 hrs, {currency} {budget*0.20:,.0f})
    - **Local Airport Transport**: Airport Express Metro / Taxi ({currency} {budget*0.02:,.0f})

    ## 🏨 Hotel Recommendations
    - 🌟 **Recommended**: Central City Hotel ({currency} {budget*0.05:,.0f}/night) | 0.5 km from metro
    - 💰 **Budget Hostels**: Backpacker Hub ({currency} {budget*0.02:,.0f}/night)
    - 💎 **Luxury Stay**: Grand Resort ({currency} {budget*0.12:,.0f}/night)

    ---
    Generate Days 1 to {min(days, 3)} now.
    For EVERY Day include:
    - **Weather Suggestion**: Temp, Rain Chance, UV Index, Clothing Tip.
    - **Daily Timeline**: 8:00 AM Breakfast -> 9:00 AM Travel -> 9:30 AM Explore -> 12:00 PM Lunch -> 2:00 PM Activity -> 6:00 PM Dinner -> 8:00 PM Evening Walk.
    - **Morning, Afternoon, Evening, Night** Schedule.
    - **Transport Between Attractions**: Previous Place -> Next Place (Distance km, Travel Time, Preferred Transport, Alternatives with fares, Google Maps search link, coordinates).
    - **AI Tips**: Best photo spot, hidden spot, crowd avoidance, washroom, ATM.
    - **Restaurant Recommendations**: Breakfast, Lunch, Dinner, Local Specialty, Veg option.
    - **Daily Expense Breakdown**: Food, Transport, Entry Fees, Shopping, Hotel, Daily Total.
    """
    try:
        part1 = _ai(p1_prompt)
        parts.append(part1)

        # PART 2: Subsequent Days in 3-day Chunks if days > 3
        current_day = 4
        while current_day <= days:
            end_chunk = min(current_day + 2, days)
            p_chunk_prompt = f"""
            Continue the {destination} travel planner. Generate ONLY Days {current_day} to {end_chunk}.
            Origin City: {origin} | Total Days: {days} | Currency: {currency} | Budget: {budget}

            For EACH Day ({current_day} to {end_chunk}), include:
            ### Day X: [Catchy Day Title]
            - **Weather Suggestion**: Temp, Rain Chance %, Clothing Recommendation.
            - **Daily Timeline**: 8:00 AM Breakfast -> 9:00 AM Transport -> 9:30 AM Sightseeing ...
            - **Morning, Afternoon, Evening, Night** activities with place name, hours, duration, fee.
            - **Transport Between Attractions**: Previous Place -> Next Place (Distance km, Travel Time, Preferred Transport, Alternatives with fares, Google Maps link, coordinates).
            - **AI Travel Tips**: Best Photo Spot, Hidden Spot, Avoid Crowds, Waiting Time, ATM.
            - **Restaurant Recommendations**: Breakfast, Lunch, Dinner, Local Specialty.
            - **Daily Expense Breakdown**: Breakfast, Lunch, Dinner, Transport, Entry Tickets, Hotel, Daily Total.

            Do NOT repeat Overview or Hotel Info. Output ONLY Day {current_day} to Day {end_chunk}.
            """
            chunk_text = _ai(p_chunk_prompt)
            parts.append(chunk_text)
            current_day = end_chunk + 1

        # PART 3: Return Journey Plan & Overall Budget Calculation
        p_final_prompt = f"""
        Provide the Return Journey Plan and Overall Budget Summary for {destination} trip ({days} days, budget: {budget} {currency}, origin: {origin}).

        MUST INCLUDE:
        ## 🔄 Return Journey Plan
        - **Route**: {destination} -> Airport / Main Station -> Flight / Train -> {origin}
        - **Estimated Return Cost**: {currency} {budget*0.25:,.0f}
        - **Total Round Trip Transit Cost**: {currency} {budget*0.50:,.0f}

        ## 💵 Overall Budget Calculation
        - ✈️ **Round-trip Flights/Transit**: {currency} {budget*0.45:,.0f}
        - 🏨 **Hotels / Accommodation**: {currency} {budget*0.25:,.0f}
        - 🍲 **Food & Dining**: {currency} {budget*0.15:,.0f}
        - 🚕 **Local Transport**: {currency} {budget*0.05:,.0f}
        - 🎟️ **Entry Tickets & Activities**: {currency} {budget*0.05:,.0f}
        - 🛡️ **Emergency Buffer & Visa**: {currency} {budget*0.05:,.0f}
        - ---
        - 💳 **Grand Total Estimated Cost**: {currency} {budget*0.90:,.0f}
        - 💰 **Remaining Budget**: {currency} {budget*0.10:,.0f}
        - 📊 **Budget Usage**: 90%

        ## 🧳 Smart Packing Recommendations
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
                repair_prompt = f"""
                Generate missing Day {md} for {destination} travel planner ({days} days, currency: {currency}).
                Include Daily Timeline, Morning, Afternoon, Evening, Night, Transport Between Attractions, AI Tips, Restaurants, and Daily Expense Breakdown.
                """
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
    prompt = f"""
    You are an AI travel assistant. The user wants to modify their existing itinerary.
    
    Current Itinerary:
    {current_itinerary}
    
    User's modification request:
    {modification_request}
    
    Please provide the updated itinerary in the exact same complete format as the original, 
    incorporating the requested changes smoothly without omitting any existing days.
    """
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

def generate_packing_list(destination: str, duration: int,
                          travel_type: str, weather: str = "") -> str:
    prompt = f"""
    Generate a smart AI packing checklist for a trip to {destination}.
    Duration: {duration} days
    Travel type: {travel_type}
    Expected weather: {weather if weather else 'unknown'}

    Format your response as a JSON object with these categories:
    {{
      "Clothing": ["item1", "item2", ...],
      "Documents": ["item1", ...],
      "Electronics": ["item1", ...],
      "Health & Hygiene": ["item1", ...],
      "Accessories": ["item1", ...],
      "Destination Specific": ["item1", ...]
    }}

    Only return the JSON. No extra text.
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
      "overall_score": <integer 0-100>,
      "overall_label": "<Safe | Moderate Risk | High Risk>",
      "weather_risk": <integer 0-100>,
      "crowd_risk": <integer 0-100>,
      "safety_risk": <integer 0-100>,
      "top_recommendations": ["...", "...", "..."],
      "emergency_numbers": {{"police": "<local police number>", "ambulance": "<local ambulance number>", "fire": "<local fire number>", "tourist_helpline": "<if applicable>"}}
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

    These should be places most tourists don't know about — local favorites, lesser-known spots.

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
    Current weather: {weather_desc}, {temperature}°C

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
    prompt = f"""
    Generate a warm, poetic AI travel memory summary for a completed trip.

    Trip details:
    - Destination: {destination}
    - Dates: {start_date} to {end_date}
    - Total spent: ${total_spent:.0f}
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
    You are WanderWise AI Companion — a proactive travel guide.
    
    Traveler info:
    - Destination: {destination}
    - Day {current_day} of {total_days}
    - Current weather: {weather if weather else 'not specified'}
    - Today's planned activities: {itinerary_snippet[:500] if itinerary_snippet else 'free day'}

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
      "progress_message": "You're on day X of Y — keep exploring!"
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
                                  accommodation_preference: str = "hotel",
                                  transportation: str = "flight",
                                  travel_companion: str = "solo",
                                  start_date: str = "", end_date: str = "",
                                  trip_preferences: dict = None) -> dict:
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
        "interests": interests,
        "trip_preferences": trip_preferences or {}
    }
    
    engine = AIEngine()
    response_envelope = engine.generate_trip(context_dict)
    
    trip_data = response_envelope.get("trip", {})
    if "days" not in trip_data and "itinerary_days" in trip_data:
        trip_data["days"] = trip_data["itinerary_days"]

    days_list = trip_data.get("days", [])
    print(f"[Pipeline Diagnostic Log] Destination: '{destination}' | Total Days: {days} | Generated Days: {len(days_list)}")

    # Guarantee fallback if days_list is empty
    if not days_list or len(days_list) == 0:
        from app.services.poi_service import fetch_real_pois_for_destination
        print(f"[Pipeline Warning Log] Generated days list was empty for '{destination}'. Invoking fetch_real_pois_for_destination fallback.")
        pois = fetch_real_pois_for_destination(destination)
        fallback_days = []
        time_slots = [
            ("08:30", "09:30", "morning", 60),
            ("09:45", "11:45", "morning", 120),
            ("12:00", "13:15", "afternoon", 75),
            ("13:30", "16:00", "afternoon", 150),
            ("16:30", "18:30", "evening", 120)
        ]
        for d in range(1, max(days, 1) + 1):
            acts = []
            for p_idx, poi in enumerate(pois[:5]):
                st, et, slot, dur_m = time_slots[min(p_idx, len(time_slots) - 1)]
                acts.append({
                    "start_time": st, "end_time": et, "duration_minutes": dur_m, "time_slot": slot,
                    "title": f"📍 Explore {poi['name']}",
                    "description": poi.get("description") or f"Visit {poi['name']} in {destination}.",
                    "place": poi,
                    "cost": {"amount": poi.get("ticket_price", 0.0), "currency": currency, "symbol": curr_info.symbol, "estimated": False},
                    "ticket_price": poi.get("ticket_price", 0.0),
                    "transport_mode": "Walking", "transport_duration": "8 mins", "distance": "0.6 km",
                    "weather_suitability": "Mixed", "crowd_level": poi.get("crowd", "Moderate"),
                    "ai_reason": poi.get("ai_reason") or f"✓ Best visited in the morning\n✓ Walking distance\n✓ 4.7★ reviews",
                    "confidence_score": poi.get("confidence", 0.98),
                    "metadata": {"tips": [poi.get("tip") or f"Visit early to enjoy quiet atmosphere."], "nearby": poi.get("nearby", [])}
                })
            fallback_days.append({"day_number": d, "title": f"Day {d}: {destination.title()} Highlights", "theme_note": "Explore top attractions & local culture", "activities": acts})
        trip_data["days"] = fallback_days

    return trip_data



def regenerate_day_itinerary(destination: str, day_number: int,
                             locked_activities: list = None, notes: str = None) -> list:
    """
    Regenerate activities for a single day while respecting user locked activities.
    """
    locked_str = json.dumps(locked_activities or [])
    system_instruction = "You are WanderWise AI. Return ONLY a valid JSON array of 4-5 activity objects for a single day."
    prompt = f"""
    Regenerate Day {day_number} itinerary for {destination}.
    Special Requests / Notes: {notes if notes else 'Fresh new mix of attractions'}
    LOCKED ACTIVITIES (DO NOT CHANGE OR OMIT THESE): {locked_str}

    Return a JSON array of 4-5 activity objects with start_time, end_time, time_slot, title, description, location, place_category, estimated_duration, ticket_price, transport_mode, weather_suitability, crowd_level, ai_reason, confidence_score.
    Ensure locked activities are preserved exactly in their original time slots.
    Only return JSON array.
    """
    try:
        raw_resp = _ai(prompt, system=system_instruction)
        res = _clean_json_response(raw_resp)
        return res if isinstance(res, list) else res.get("activities", [])
    except Exception:
        return locked_activities or []
