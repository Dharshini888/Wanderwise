from decimal import Decimal
from typing import Dict, Any
from sqlalchemy.orm import Session
from app.models.trip import Trip
from app.services.expense_service import get_trip_budget_analytics
from app.utils.currency_formatter import format_currency

def generate_ai_expense_insights(db: Session, trip_id: int) -> Dict[str, Any]:
    """
    AI Expense Insights Engine (Read-Only GET).
    Calculates spending score, forecast, risk levels, smart alerts, and money-saving recommendations.
    """
    analytics = get_trip_budget_analytics(db, trip_id)
    if not analytics:
        return {
            "budget_score": 100,
            "health": "Healthy",
            "forecast": "No expenses recorded yet.",
            "projected_spend": Decimal("0.00"),
            "remaining_budget": Decimal("1000.00"),
            "daily_limit_remaining": Decimal("200.00"),
            "recommended_today_spend": Decimal("150.00"),
            "highest_category": "None",
            "highest_day": "Day 1",
            "overspending_risk": "Low",
            "top_savings": ["Plan meal spending in advance."],
            "risk_items": [],
            "smart_alerts": ["No active budget alerts."]
        }

    pct = analytics["budget_used_percentage"]
    rem = analytics["remaining_budget"]
    tot_b = analytics["total_budget"]
    daily_avg = analytics["daily_average"]
    proj_spend = analytics["projected_final_spend"]
    highest_cat = analytics["highest_spending_category"]
    highest_day = analytics["highest_spending_day"]

    # Calculate score (100 - pct overrun factor)
    if pct <= 50:
        score = 92
        health = "Healthy"
        risk = "Low"
        forecast = f"You will finish approximately {round(100 - (float(proj_spend) / float(tot_b) * 100), 1)}% under budget."
    elif pct <= 80:
        score = 80
        health = "On Track"
        risk = "Medium"
        forecast = "Your spending matches your target daily pace."
    elif pct <= 100:
        score = 65
        health = "Warning"
        risk = "High"
        forecast = "You are approaching your maximum trip budget."
    else:
        score = 40
        health = "Over Budget"
        risk = "Critical"
        forecast = f"Current spending exceeds your budget by {round(pct - 100, 1)}%."

    # Compute daily limit remaining
    daily_rem = Decimal(str(round(float(rem) / 3.0, 2))) if float(rem) > 0 else Decimal("0.00")
    rec_today = Decimal(str(round(float(daily_rem) * 0.85, 2))) if float(daily_rem) > 0 else Decimal("0.00")

    smart_alerts = [
        f"You've used {pct}% of your overall trip budget.",
        f"Highest spending category is {highest_cat}.",
        f"Peak daily expenditure occurred on {highest_day}."
    ]
    if pct > 70:
        smart_alerts.append(f"Caution: Spending on {highest_cat} is higher than average.")

    top_savings = [
        f"Switching to local transit instead of private taxis can save up to 25% on {highest_cat}.",
        "Reserve mid-range lunch dining to preserve evening dinner allowance.",
        "Consider booking sightseeing passes online in advance for group discounts."
    ]

    risk_items = []
    if float(proj_spend) > float(tot_b):
        risk_items.append(f"Projected total spend ({format_currency(float(proj_spend))}) exceeds budget ({format_currency(float(tot_b))}).")

    return {
        "budget_score": score,
        "health": health,
        "forecast": forecast,
        "projected_spend": proj_spend,
        "remaining_budget": rem,
        "daily_limit_remaining": daily_rem,
        "recommended_today_spend": rec_today,
        "highest_category": highest_cat,
        "highest_day": highest_day,
        "overspending_risk": risk,
        "top_savings": top_savings,
        "risk_items": risk_items,
        "smart_alerts": smart_alerts
    }
