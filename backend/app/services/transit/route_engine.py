import hashlib
import random

def calculate_distance(origin: str, destination: str) -> int:
    s = f"{origin.lower().strip()}-{destination.lower().strip()}"
    h = int(hashlib.md5(s.encode()).hexdigest(), 16)
    # Scale between 50km and 2500km
    return 50 + (h % 2450)

def calculate_travel_modes(distance: int):
    # Depending on distance, some modes are hidden
    modes = []
    
    if distance < 5:
        modes.append({"mode": "Walking", "speed": 5, "cost_per_km": 0, "carbon_per_km": 0})
        modes.append({"mode": "Bike", "speed": 15, "cost_per_km": 0.5, "carbon_per_km": 0})
        
    if distance < 50:
        modes.append({"mode": "Auto", "speed": 35, "cost_per_km": 15, "carbon_per_km": 0.1})
        modes.append({"mode": "Metro", "speed": 40, "cost_per_km": 2, "carbon_per_km": 0.02})
        
    if distance < 800:
        modes.append({"mode": "Taxi", "speed": 50, "cost_per_km": 12, "carbon_per_km": 0.15})
        modes.append({"mode": "Bus", "speed": 50, "cost_per_km": 1.5, "carbon_per_km": 0.05})
        
    if distance >= 50:
        modes.append({"mode": "Train", "speed": 65, "cost_per_km": 2.5, "carbon_per_km": 0.03})
        
    if distance >= 300:
        modes.append({"mode": "Flight", "speed": 500, "cost_per_km": 8, "carbon_per_km": 0.25, "base_time": 2.5}) # 2.5 hours airport buffer
        modes.append({"mode": "Mixed (Flight+Taxi)", "speed": 300, "cost_per_km": 9, "carbon_per_km": 0.23, "base_time": 3})

    # Add fallback if somehow empty
    if not modes:
        modes.append({"mode": "Taxi", "speed": 50, "cost_per_km": 12, "carbon_per_km": 0.15})
        
    return modes

def format_time(hrs: float) -> str:
    h = int(hrs)
    m = int((hrs - h) * 60)
    if h == 0:
        return f"{m}m"
    return f"{h}h {m}m"

def calculate_eta_cost(distance: int, modes: list, budget: int):
    results = []
    for m in modes:
        time_hrs = (distance / m["speed"]) + m.get("base_time", 0)
        cost = int(distance * m["cost_per_km"])
        if m["mode"] in ["Flight", "Mixed (Flight+Taxi)"]:
            cost += 3000 # Base airport fees
        
        results.append({
            "mode": m["mode"],
            "time_hrs": time_hrs,
            "time_str": format_time(time_hrs),
            "cost": cost,
            "carbon_kg": int(distance * m["carbon_per_km"]),
        })
    return results

def calculate_ai_decision_panel(options: list, preferred_mode: str, budget: int):
    # Calculate scores for each option
    for opt in options:
        # Time Score: Faster is better
        opt["score_time"] = max(1, min(10, 10 - int(opt["time_hrs"] / 5)))
        # Cost Score: Cheaper is better, penalize if over budget
        opt["score_cost"] = max(1, min(10, 10 - int((opt["cost"] / max(budget, 1)) * 5)))
        if opt["cost"] > budget:
            opt["score_cost"] -= 3
        # Carbon Score: Less is better
        opt["score_carbon"] = max(1, min(10, 10 - int(opt["carbon_kg"] / 50)))
        
        # Hardcoded subjective metrics based on mode
        mode = opt["mode"]
        if mode == "Train":
            opt["score_comfort"] = 8
            opt["score_safety"] = 9
            opt["score_weather"] = 9
            opt["score_traffic"] = 10
            opt["score_reliability"] = 8
        elif mode == "Flight":
            opt["score_comfort"] = 9
            opt["score_safety"] = 9
            opt["score_weather"] = 7
            opt["score_traffic"] = 9
            opt["score_reliability"] = 7
        elif mode == "Bus":
            opt["score_comfort"] = 5
            opt["score_safety"] = 7
            opt["score_weather"] = 7
            opt["score_traffic"] = 6
            opt["score_reliability"] = 6
        elif mode == "Taxi":
            opt["score_comfort"] = 8
            opt["score_safety"] = 8
            opt["score_weather"] = 8
            opt["score_traffic"] = 5
            opt["score_reliability"] = 7
        else:
            opt["score_comfort"] = 6
            opt["score_safety"] = 7
            opt["score_weather"] = 6
            opt["score_traffic"] = 7
            opt["score_reliability"] = 8
            
        # Boost preferred mode
        if preferred_mode.lower() in mode.lower():
            opt["score_comfort"] += 1
            
        # Overall
        opt["score_overall"] = round((opt["score_time"] * 1.5 + opt["score_cost"] * 1.5 + opt["score_carbon"] + opt["score_safety"] * 1.2 + opt["score_comfort"] + opt["score_reliability"]) / 7.2 * 10)
        opt["score_overall"] = max(10, min(100, opt["score_overall"]))

    # Sort by overall score
    options.sort(key=lambda x: x["score_overall"], reverse=True)
    best = options[0]
    
    reasons = []
    if best["score_cost"] >= 8: reasons.append("Lowest cost")
    if best["score_time"] >= 8: reasons.append("Fastest travel time")
    if best["score_safety"] >= 8: reasons.append("High safety rating")
    if best["score_carbon"] >= 8: reasons.append("Eco-friendly choice")
    if best["score_traffic"] >= 8: reasons.append("Avoids road traffic")
    
    if not reasons:
        reasons.append("Best balanced option")

    return {
        "ranked_options": options,
        "recommended": best,
        "panel": {
            "Cost": best["score_cost"],
            "Time": best["score_time"],
            "Weather": best["score_weather"],
            "Safety": best["score_safety"],
            "Comfort": best["score_comfort"],
            "Carbon": best["score_carbon"],
            "Traffic": best["score_traffic"],
            "Reliability": best["score_reliability"]
        },
        "confidence": best["score_overall"],
        "reasons": reasons
    }

def calculate_timeline(origin: str, destination: str, best_option: dict):
    mode = best_option["mode"]
    time_hrs = best_option["time_hrs"]
    
    t = []
    
    if "Flight" in mode:
        t = [
            {"time": "6:00 AM", "action": f"Leave {origin}", "status": "completed"},
            {"time": "7:00 AM", "action": "Reach Airport", "status": "completed"},
            {"time": "8:30 AM", "action": "Board Flight", "status": "current"},
            {"time": "9:00 AM", "action": "Takeoff", "status": "upcoming"},
            {"time": "11:00 AM", "action": f"Arrive at {destination}", "status": "upcoming"},
            {"time": "11:45 AM", "action": "Taxi to Hotel", "status": "upcoming"}
        ]
    elif "Train" in mode:
        t = [
            {"time": "7:15 AM", "action": f"Leave {origin}", "status": "completed"},
            {"time": "7:50 AM", "action": "Reach Railway Station", "status": "completed"},
            {"time": "8:25 AM", "action": "Train Departure", "status": "current"},
            {"time": "9:30 AM", "action": "⚠ Train delayed by 18 mins", "status": "upcoming", "alert": True},
            {"time": "11:10 AM", "action": f"Arrive {destination} Junction", "status": "upcoming"},
            {"time": "11:40 AM", "action": "Reach Hotel", "status": "upcoming"}
        ]
    else:
        t = [
            {"time": "8:00 AM", "action": f"Leave {origin}", "status": "completed"},
            {"time": "8:15 AM", "action": f"Begin journey via {mode}", "status": "current"},
            {"time": "10:30 AM", "action": "Rest Stop", "status": "upcoming"},
            {"time": "1:00 PM", "action": f"Arrive at {destination}", "status": "upcoming"}
        ]
        
    return t

def calculate_weather(origin: str, destination: str, distance: int):
    # Deterministic weather
    h_orig = int(hashlib.md5(origin.encode()).hexdigest(), 16)
    h_dest = int(hashlib.md5(destination.encode()).hexdigest(), 16)
    
    temp_orig = 20 + (h_orig % 15)
    temp_dest = 20 + (h_dest % 15)
    
    stops = []
    stops.append({"location": origin, "temp": f"{temp_orig}°C", "icon": "☀️" if temp_orig > 25 else "⛅"})
    
    if distance > 200:
        stops.append({"location": "Midway Point", "temp": f"{(temp_orig+temp_dest)//2}°C", "icon": "⛅"})
        
    stops.append({"location": destination, "temp": f"{temp_dest}°C", "icon": "🌧️" if temp_dest < 24 else "☀️"})
    
    warnings = []
    if temp_dest < 24:
        warnings = ["Rain expected", "Carry umbrella", "Roads may be slippery"]
    elif temp_dest > 32:
        warnings = ["Heat Advisory", "Carry Water", "Stay Hydrated"]
    else:
        warnings = ["Clear weather", "Safe for sightseeing", "Good visibility"]
        
    return {
        "stops": stops,
        "warnings": warnings,
        "rain_probability": (h_dest % 100),
        "visibility": "Low" if temp_dest < 24 else "High"
    }

def calculate_budget(base_cost: int, best_mode: str):
    return {
        "breakdown": {
            "Transport": base_cost,
            "Accommodation": int(base_cost * 1.5),
            "Food": int(base_cost * 0.8),
            "Activities": int(base_cost * 0.5),
            "Emergency Buffer": int(base_cost * 0.2),
            "Shopping": int(base_cost * 0.4),
            "Taxes": int(base_cost * 0.1)
        },
        "total": int(base_cost * 4.5),
        "savings": [
            {"action": f"Book {best_mode} on Tuesday", "amount": int(base_cost * 0.15)},
            {"action": "Stay 3 km outside city", "amount": int(base_cost * 0.4)},
            {"action": "Use public metro locally", "amount": int(base_cost * 0.1)}
        ]
    }

def calculate_safety(destination: str):
    h = int(hashlib.md5(destination.encode()).hexdigest(), 16)
    return {
        "Overall": 75 + (h % 20),
        "Women Safety": 70 + ((h+1) % 25),
        "Night Safety": 65 + ((h+2) % 25),
        "Medical Facilities": "Excellent" if h % 2 == 0 else "Good",
        "Police Stations": 2 + (h % 5),
        "Emergency Numbers": "112, 100, 108",
        "Safe Zones": "City Center, Tourist Hubs",
        "Scam Risk": "Low" if h % 3 == 0 else "Moderate"
    }

def calculate_assistant_feed(destination: str, distance: int, weather: dict):
    feed = []
    if "Rain" in str(weather.get("warnings")):
        feed.append(f"🚨 Heavy rain expected near {destination}. Leave 15 minutes early.")
    elif "Heat" in str(weather.get("warnings")):
        feed.append(f"🚨 High temperatures in {destination}. Keep hydrated.")
        
    if distance > 100:
        feed.append("🚨 Fuel station 5 km away.")
        feed.append("🚨 Toll payment accepted through FASTag.")
        
    feed.append("🚨 Hotel check-in starts in 40 mins.")
    feed.append("🚨 Restaurant nearby matches your food preferences.")
    
    return feed

def calculate_nearby(destination: str):
    # Just generic for the layout
    return [
        {"type": "Hospital", "name": f"{destination} General", "dist": "1.2 km", "rating": 4.5},
        {"type": "Police", "name": f"{destination} Central Station", "dist": "2.4 km", "rating": 4.0},
        {"type": "ATM", "name": "Global Bank ATM", "dist": "0.3 km", "rating": 5.0},
        {"type": "Fuel", "name": "Express Petrol", "dist": "3.1 km", "rating": 4.2},
        {"type": "Pharmacy", "name": "24x7 Meds", "dist": "0.8 km", "rating": 4.8}
    ]

def calculate_carbon(best_option: dict):
    carbon = best_option["carbon_kg"]
    saved = int(carbon * 1.5)
    return {
        "current": carbon,
        "saved": saved,
        "trees": max(1, saved // 20),
        "electricity_kwh": saved * 2,
        "score": 100 - min(80, carbon // 10)
    }

def calculate_route(origin: str, destination: str, date: str, budget: int, preferred_mode: str):
    # 1. Master Distance
    dist = calculate_distance(origin, destination)
    
    # 2. Modes
    modes = calculate_travel_modes(dist)
    
    # 3. ETA & Cost
    options = calculate_eta_cost(dist, modes, budget)
    
    # 4. Decision Panel
    decision = calculate_ai_decision_panel(options, preferred_mode, budget)
    best = decision["recommended"]
    
    # 5. Timeline
    timeline = calculate_timeline(origin, destination, best)
    
    # 6. Weather
    weather = calculate_weather(origin, destination, dist)
    
    # 7. Budget
    budget_data = calculate_budget(best["cost"], best["mode"])
    
    # 8. Safety
    safety = calculate_safety(destination)
    
    # 9. Feed
    feed = calculate_assistant_feed(destination, dist, weather)
    
    # 10. Nearby
    nearby = calculate_nearby(destination)
    
    # 11. Carbon
    carbon = calculate_carbon(best)
    
    return {
        "origin": origin,
        "destination": destination,
        "distance_km": dist,
        "status": "Ready",
        "recommended": best,
        "all_options": decision["ranked_options"],
        "decision_panel": decision,
        "timeline": timeline,
        "weather": weather,
        "budget": budget_data,
        "safety": safety,
        "feed": feed,
        "nearby": nearby,
        "carbon": carbon
    }
