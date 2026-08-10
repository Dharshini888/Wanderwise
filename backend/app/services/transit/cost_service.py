# Cost and Budget Optimizer service

def get_budget_optimization(origin: str, destination: str, current_cost: int):
    return {
        "current_cost": current_cost,
        "suggestions": [
            { "text": "Choose Train instead of Flight", "savings": int(current_cost * 0.3) },
            { "text": f"Move hotel 2 km from {destination} center", "savings": int(current_cost * 0.1) },
            { "text": "Travel one day earlier", "savings": int(current_cost * 0.15) }
        ],
        "total_savings_potential": int(current_cost * 0.55)
    }

def get_cost_breakdown(base_cost: int):
    return {
        "Flight": int(base_cost * 0.7),
        "Taxi": int(base_cost * 0.1),
        "Food": int(base_cost * 0.1),
        "Airport Transfer": int(base_cost * 0.1),
        "Hotel Shuttle": 0,
        "Total": base_cost
    }
