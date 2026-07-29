from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional
from app.database.connection import get_db
from app.models.trip import Trip
from app.models.expense import Expense
from app.models.user import User
from app.routes.auth import get_current_user_optional

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])


@router.get("")
@router.get("/")
@router.get("/{user_id}")
def get_analytics(
    user_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    target_user_id = current_user.id if current_user else user_id
    if not target_user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User identification required")

    trips = db.query(Trip).filter(Trip.user_id == target_user_id).all()

    if not trips:
        return {
            "total_trips": 0,
            "cities_visited": 0,
            "countries_visited": 0,
            "total_budget": 0,
            "total_spent": 0,
            "budget_utilization": 0,
            "spending_by_category": {},
            "trips_by_type": {},
            "recent_trips": [],
        }

    destinations = [t.destination for t in trips]
    cities = len(set(destinations))
    countries = set()
    for d in destinations:
        parts = d.split(",")
        if len(parts) >= 2:
            countries.add(parts[-1].strip())
        else:
            countries.add(d.strip())

    total_budget = sum(t.budget for t in trips if t.budget)

    # Aggregate expenses for this user's trips only
    trip_ids = [t.id for t in trips]
    all_expenses = db.query(Expense).filter(Expense.trip_id.in_(trip_ids)).all() if trip_ids else []
    total_spent = sum(e.amount for e in all_expenses)

    spending_by_category: dict = {}
    for e in all_expenses:
        cat = e.category.value if hasattr(e.category, "value") else (e.category or "Other")
        spending_by_category[cat] = spending_by_category.get(cat, 0) + float(e.amount)

    spending_by_category = {k: round(v, 2) for k, v in spending_by_category.items()}

    trips_by_type: dict = {}
    for t in trips:
        tt = t.travel_type or "leisure"
        trips_by_type[tt] = trips_by_type.get(tt, 0) + 1

    budget_utilization = round((float(total_spent) / float(total_budget) * 100) if total_budget > 0 else 0, 1)

    recent_trips = [
        {
            "id": t.id,
            "destination": t.destination,
            "start_date": str(t.start_date),
            "end_date": str(t.end_date),
            "budget": t.budget,
            "travel_type": t.travel_type,
        }
        for t in sorted(trips, key=lambda x: x.start_date, reverse=True)[:5]
    ]

    return {
        "total_trips": len(trips),
        "cities_visited": cities,
        "countries_visited": len(countries),
        "total_budget": round(float(total_budget), 2),
        "total_spent": round(float(total_spent), 2),
        "budget_utilization": budget_utilization,
        "spending_by_category": spending_by_category,
        "trips_by_type": trips_by_type,
        "recent_trips": recent_trips,
    }
