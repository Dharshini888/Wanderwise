# AI Route Optimizer service
import hashlib

def get_pseudo_distance(origin: str, destination: str) -> int:
    # Deterministic pseudo-distance based on string hashing (100 to 3000 km)
    s = f"{origin.lower()}-{destination.lower()}"
    h = int(hashlib.md5(s.encode()).hexdigest(), 16)
    return 100 + (h % 2900)

def optimize_routes(origin: str, destination: str, preferred_mode: str, budget: int):
    distance = get_pseudo_distance(origin, destination)
    
    # Heuristics based on distance
    flight_time_hrs = distance / 500.0 + 2.0  # 500km/h + 2h airport time
    train_time_hrs = distance / 80.0          # 80km/h
    bus_time_hrs = distance / 50.0            # 50km/h
    
    flight_cost = int(distance * 8)           # 8 INR per km
    train_cost = int(distance * 2.5)          # 2.5 INR per km
    bus_cost = int(distance * 1.5)            # 1.5 INR per km
    
    def format_time(hrs):
        h = int(hrs)
        m = int((hrs - h) * 60)
        return f"{h}h {m}m"

    # Generates a ranked list of multi-modal routes
    routes = [
        {
            "mode": "Flight",
            "time_str": format_time(flight_time_hrs),
            "cost_inr": flight_cost,
            "carbon_rating": "High",
            "comfort": "High",
            "score": 90
        },
        {
            "mode": "Train",
            "time_str": format_time(train_time_hrs),
            "cost_inr": train_cost,
            "carbon_rating": "Low",
            "comfort": "Medium",
            "score": 75
        },
        {
            "mode": "Bus",
            "time_str": format_time(bus_time_hrs),
            "cost_inr": bus_cost,
            "carbon_rating": "Very Low",
            "comfort": "Low",
            "score": 60
        }
    ]

    # Adjust ranking based on preferred_mode and distance
    if preferred_mode == "Cheapest":
        for r in routes:
            if r["mode"] == "Train": r["score"] += 25
            if r["mode"] == "Bus": r["score"] += 35
    elif preferred_mode == "Eco Friendly":
        for r in routes:
            if r["mode"] == "Train": r["score"] += 30
            if r["mode"] == "Bus": r["score"] += 20
            if r["mode"] == "Flight": r["score"] -= 20
    else: # Fastest
        for r in routes:
            if r["mode"] == "Flight": r["score"] += 20

    # Ensure cost constraint
    for r in routes:
        if r["cost_inr"] > budget:
            r["score"] -= 40 # Heavily penalize if over budget

    # Sort descending by score
    routes.sort(key=lambda x: x["score"], reverse=True)
    return routes
