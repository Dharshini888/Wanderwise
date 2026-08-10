from typing import Dict, List, Any

def format_hrs(hrs: float) -> str:
    h = int(hrs)
    m = int(round((hrs - h) * 60))
    if h == 0:
        return f"{m}m"
    if m == 0:
        return f"{h}h"
    return f"{h}h {m}m"

def rank_and_score_modes(distance_km: float, duration_mins: float, budget_inr: float, preferred_mode: str, weather_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Evaluates multi-modal transportation options (Train, Bus, Taxi, Flight, Walk, Cycle)
    against distance, duration, weather, and budget constraints.
    - Hides Flight completely if distance_km < 250.
    - Returns 8 Category Alternatives: Best Overall, Fastest, Cheapest, Greenest, Most Comfortable, Least Walking, Fewest Transfers, Most Reliable.
    """
    raw_modes = []

    # 1. Walk / Cycle (if distance_km <= 15)
    if distance_km <= 3.0:
        walk_time_hrs = max(round(distance_km / 4.0, 1), 0.1)
        raw_modes.append({
            "mode": "Walk",
            "time_hrs": walk_time_hrs,
            "time_str": format_hrs(walk_time_hrs),
            "cost_inr": 0,
            "carbon_kg": 0.0,
            "comfort": 5, "safety": 8, "weather": 6, "traffic": 10, "reliability": 10,
            "transfers": 0, "walking_m": int(distance_km * 1000)
        })

    if distance_km <= 15.0:
        cycle_time_hrs = max(round(distance_km / 12.0, 1), 0.1)
        raw_modes.append({
            "mode": "Bicycle",
            "time_hrs": cycle_time_hrs,
            "time_str": format_hrs(cycle_time_hrs),
            "cost_inr": 0,
            "carbon_kg": 0.0,
            "comfort": 6, "safety": 7, "weather": 6, "traffic": 8, "reliability": 9,
            "transfers": 0, "walking_m": 50
        })

    # 2. Taxi / Self Drive
    car_time_hrs = max(round(duration_mins / 60.0, 1), 0.2)
    car_cost = max(50, int(distance_km * 12))
    raw_modes.append({
        "mode": "Taxi / Self Drive",
        "time_hrs": car_time_hrs,
        "time_str": format_hrs(car_time_hrs),
        "cost_inr": car_cost,
        "carbon_kg": round(distance_km * 0.14, 1),
        "comfort": 8, "safety": 8, "weather": 8, "traffic": 6, "reliability": 8,
        "transfers": 0, "walking_m": 50
    })

    # 3. Train (if distance >= 20km)
    if distance_km >= 20:
        train_time_hrs = max(round((distance_km / 65.0) + 0.4, 1), 0.5)
        train_cost = max(30, int(distance_km * 2.2))
        raw_modes.append({
            "mode": "Intercity Train",
            "time_hrs": train_time_hrs,
            "time_str": format_hrs(train_time_hrs),
            "cost_inr": train_cost,
            "carbon_kg": round(distance_km * 0.03, 1),
            "comfort": 8, "safety": 9, "weather": 9, "traffic": 10, "reliability": 9,
            "transfers": 1, "walking_m": 350
        })

    # 4. Bus (if distance < 800km)
    if distance_km < 800:
        bus_time_hrs = max(round((distance_km / 45.0) + 0.3, 1), 0.4)
        bus_cost = max(20, int(distance_km * 1.5))
        raw_modes.append({
            "mode": "Express Bus",
            "time_hrs": bus_time_hrs,
            "time_str": format_hrs(bus_time_hrs),
            "cost_inr": bus_cost,
            "carbon_kg": round(distance_km * 0.05, 1),
            "comfort": 6, "safety": 7, "weather": 7, "traffic": 6, "reliability": 7,
            "transfers": 1, "walking_m": 250
        })

    # 5. Flight (ONLY IF distance_km >= 250 km - STRICT TRUTH RULE)
    if distance_km >= 250:
        flight_time_hrs = round((distance_km / 500.0) + 2.5, 1)
        flight_cost = int(distance_km * 7.5) + 2500
        raw_modes.append({
            "mode": "Flight",
            "time_hrs": flight_time_hrs,
            "time_str": format_hrs(flight_time_hrs),
            "cost_inr": flight_cost,
            "carbon_kg": round(distance_km * 0.25, 1),
            "comfort": 9, "safety": 9, "weather": 7, "traffic": 9, "reliability": 8,
            "transfers": 2, "walking_m": 600
        })

    # Calculate vector scores (0-10) for each mode
    for m in raw_modes:
        time_score = max(1, min(10, 10 - int(m["time_hrs"] / 3)))
        cost_score = 10 if m["cost_inr"] == 0 else max(1, min(10, 10 - int((m["cost_inr"] / max(budget_inr, 1)) * 5)))
        carbon_score = max(1, min(10, 10 - int(m["carbon_kg"] / 35)))

        m["scores"] = {
            "Time": time_score,
            "Cost": cost_score,
            "Comfort": m["comfort"],
            "Weather": m["weather"],
            "Safety": m["safety"],
            "Carbon": carbon_score,
            "Traffic": m["traffic"],
            "Reliability": m["reliability"]
        }

        overall = round((
            time_score * 2.0 +
            cost_score * 2.0 +
            m["comfort"] * 1.2 +
            m["safety"] * 1.5 +
            carbon_score * 1.0 +
            m["reliability"] * 1.3
        ) / 9.0 * 10)

        m["score_overall"] = max(15, min(99, overall))

    # Strategy Selection & Sorting
    pm_clean = (preferred_mode or "fastest").strip().lower()

    if "cheap" in pm_clean:
        ranked = sorted(raw_modes, key=lambda x: x["cost_inr"])
        best_mode = ranked[0]
        reasons = [
            f"Lowest fare option (est. {best_mode['cost_inr']} base units)",
            f"Walking distance: {best_mode['walking_m']}m",
            f"Carbon footprint: {best_mode['carbon_kg']} kg CO\u2082"
        ]
    elif "green" in pm_clean or "eco" in pm_clean:
        ranked = sorted(raw_modes, key=lambda x: x["carbon_kg"])
        best_mode = ranked[0]
        reasons = [
            f"Lowest emissions: {best_mode['carbon_kg']} kg CO\u2082",
            f"Reliability score: {best_mode['reliability']}/10",
            f"Mode: {best_mode['mode']} — est. fare applies"
        ]
    elif "walk" in pm_clean:
        ranked = sorted(raw_modes, key=lambda x: x["walking_m"])
        best_mode = ranked[0]
        reasons = [
            f"Minimal walking distance: {best_mode['walking_m']}m",
            f"Direct boarding without station transfers",
            f"Duration: {best_mode['time_str']}"
        ]
    elif "comfort" in pm_clean:
        ranked = sorted(raw_modes, key=lambda x: (-x["comfort"], x["time_hrs"]))
        best_mode = ranked[0]
        reasons = [
            f"Highest comfort score: {best_mode['comfort']}/10",
            f"Direct journey with zero hassle",
            f"Reliability: {best_mode['reliability']}/10"
        ]
    elif "safe" in pm_clean:
        ranked = sorted(raw_modes, key=lambda x: (-x["safety"], x["cost_inr"]))
        best_mode = ranked[0]
        reasons = [
            f"Highest safety rating: {best_mode['safety']}/10",
            f"Monitored corridor with high reliability",
            f"Duration: {best_mode['time_str']}"
        ]
    else: # fastest or best overall
        ranked = sorted(raw_modes, key=lambda x: (-x["score_overall"], x["time_hrs"]))
        best_mode = ranked[0]
        reasons = [
            f"Optimal time-to-cost ratio ({best_mode['time_str']}, est. fare applies)",
            f"Overall score: {best_mode['score_overall']}% (AI estimate)",
            f"Reliability: {best_mode['reliability']}/10"
        ]

    # Build 8 Category Alternatives Map
    alternatives = {
        "best_overall": max(raw_modes, key=lambda x: x["score_overall"]),
        "fastest": min(raw_modes, key=lambda x: x["time_hrs"]),
        "cheapest": min(raw_modes, key=lambda x: x["cost_inr"]),
        "greenest": min(raw_modes, key=lambda x: x["carbon_kg"]),
        "most_comfortable": max(raw_modes, key=lambda x: x["comfort"]),
        "least_walking": min(raw_modes, key=lambda x: x["walking_m"]),
        "fewest_transfers": min(raw_modes, key=lambda x: x["transfers"]),
        "most_reliable": max(raw_modes, key=lambda x: x["reliability"])
    }

    formatted_alts = {}
    for k, v in alternatives.items():
        formatted_alts[k] = {
            "name": v["mode"],
            "time": v["time_str"],
            "cost": v["cost_inr"],
            "carbon": f"{v['carbon_kg']} kg CO₂",
            "transfers": v["transfers"],
            "walking_m": v["walking_m"]
        }

    return {
        "recommended": best_mode,
        "confidence": best_mode["score_overall"],
        "reasons": reasons,
        "ranked_options": raw_modes,
        "alternatives": formatted_alts
    }
