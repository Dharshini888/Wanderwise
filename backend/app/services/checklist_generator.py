from datetime import datetime, date, timezone, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from app.models.checklist import ChecklistItem
from app.models.trip import Trip
from app.models.user import User
from app.models.document import Document
from app.models.packing import PackingList
from app.models.budget import Budget
from app.models.expense import Expense
from app.models.trip_booking import TripBooking
from app.models.itinerary import ItineraryDay


def _to_datetime(val: Any) -> Optional[datetime]:
    if not val:
        return None
    if isinstance(val, datetime):
        if val.tzinfo is None:
            return val.replace(tzinfo=timezone.utc)
        return val
    if isinstance(val, date):
        return datetime.combine(val, datetime.min.time(), tzinfo=timezone.utc)
    if isinstance(val, str):
        try:
            clean = val.strip().replace("Z", "+00:00")
            if "T" in clean:
                dt = datetime.fromisoformat(clean)
            else:
                dt = datetime.strptime(clean, "%Y-%m-%d")
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except Exception:
            return None
    return None


def generate_checklist_for_trip(db: Session, trip_id: int, user_id: int) -> List[ChecklistItem]:
    """
    Deterministically generates or updates auto-generated checklist items for a trip based on real DB records.
    Prevents duplicate items on repeated generation calls.
    User custom items (source='USER', is_auto_generated=False) are preserved.
    """
    trip = db.query(Trip).filter(Trip.id == trip_id, Trip.user_id == user_id).first()
    if not trip:
        raise ValueError("Trip not found or unauthorized")

    user = db.query(User).filter(User.id == user_id).first()
    now_utc = datetime.now(timezone.utc)
    trip_start_dt = _to_datetime(trip.start_date)

    generated_specs: List[Dict[str, Any]] = []

    # ---------------------------------------------------------
    # 1. DOCUMENT RULES
    # ---------------------------------------------------------
    passports = db.query(Document).filter(
        Document.user_id == user_id,
        Document.is_deleted == False,
        (Document.category.ilike("Passport")) | (Document.document_type.ilike("Passport"))
    ).all()

    # Check for passport in Document model or User profile
    user_passport_exp = _to_datetime(getattr(user, 'passport_expiry', None)) if user else None

    if not passports and not user_passport_exp:
        generated_specs.append({
            "title": "Upload your passport",
            "description": "Ensure your passport is uploaded into Documents Vault before travel.",
            "category": "DOCUMENTS",
            "priority": "HIGH",
            "source": "DOCUMENTS",
            "action_type": "UPLOAD_PASSPORT",
            "action_target": "/documents",
            "due_date": trip_start_dt - timedelta(days=14) if trip_start_dt else None
        })
    else:
        # Check passport expiry
        exp_dt = None
        if passports:
            # find latest expiry date among uploaded passports
            for p in passports:
                p_exp = _to_datetime(p.expiry_date)
                if p_exp and (not exp_dt or p_exp > exp_dt):
                    exp_dt = p_exp

        if not exp_dt and user_passport_exp:
            exp_dt = user_passport_exp

        if not exp_dt:
            generated_specs.append({
                "title": "Verify passport expiry date",
                "description": "Your passport document is uploaded but expiry date is missing.",
                "category": "DOCUMENTS",
                "priority": "HIGH",
                "source": "DOCUMENTS",
                "action_type": "VERIFY_PASSPORT_EXPIRY",
                "action_target": "/documents",
                "due_date": trip_start_dt - timedelta(days=14) if trip_start_dt else None
            })
        elif exp_dt < now_utc:
            generated_specs.append({
                "title": "Passport has expired — renew before travel",
                "description": f"Your passport expired on {exp_dt.strftime('%Y-%m-%d')}.",
                "category": "DOCUMENTS",
                "priority": "URGENT",
                "source": "DOCUMENTS",
                "action_type": "PASSPORT_EXPIRED",
                "action_target": "/documents",
                "due_date": now_utc
            })
        elif exp_dt <= (trip_start_dt or (now_utc + timedelta(days=30))):
            generated_specs.append({
                "title": "Renew your passport",
                "description": f"Your passport expires on {exp_dt.strftime('%Y-%m-%d')}, which is too close to travel.",
                "category": "DOCUMENTS",
                "priority": "URGENT",
                "source": "DOCUMENTS",
                "action_type": "RENEW_PASSPORT",
                "action_target": "/documents",
                "due_date": trip_start_dt - timedelta(days=30) if trip_start_dt else now_utc
            })
        else:
            generated_specs.append({
                "title": "Passport is ready",
                "description": f"Passport is valid through {exp_dt.strftime('%Y-%m-%d')}.",
                "category": "DOCUMENTS",
                "priority": "LOW",
                "source": "DOCUMENTS",
                "action_type": "PASSPORT_READY",
                "action_target": "/documents",
                "due_date": trip_start_dt
            })

    # Visa checks (use existing user documents for visas)
    visas = db.query(Document).filter(
        Document.user_id == user_id,
        Document.is_deleted == False,
        (Document.category.ilike("Visa")) | (Document.document_type.ilike("Visa"))
    ).all()

    for visa in visas:
        visa_exp = _to_datetime(visa.expiry_date)
        if visa_exp and visa_exp <= (now_utc + timedelta(days=30)):
            generated_specs.append({
                "title": f"Check visa validity for {visa.name}",
                "description": f"Visa document '{visa.name}' expires on {visa_exp.strftime('%Y-%m-%d')}.",
                "category": "DOCUMENTS",
                "priority": "HIGH",
                "source": "DOCUMENTS",
                "action_type": "CHECK_VISA",
                "action_target": f"/documents/{visa.id}",
                "due_date": visa_exp
            })

    # ---------------------------------------------------------
    # 2. PACKING RULES
    # ---------------------------------------------------------
    packing_lists = db.query(PackingList).filter(PackingList.trip_id == trip_id).all()

    if not packing_lists:
        generated_specs.append({
            "title": "Create your packing list",
            "description": "Generate or create a packing checklist for your destination.",
            "category": "PACKING",
            "priority": "MEDIUM",
            "source": "PACKING",
            "action_type": "CREATE_PACKING",
            "action_target": "/packing",
            "due_date": trip_start_dt - timedelta(days=3) if trip_start_dt else None
        })
    else:
        pkg = packing_lists[0]
        categories = pkg.categories or []
        total_items = 0
        checked_items = 0
        if isinstance(categories, list):
            for cat in categories:
                if isinstance(cat, dict):
                    items = cat.get("items", [])
                    if isinstance(items, list):
                        for item in items:
                            total_items += 1
                            if isinstance(item, dict) and (item.get("packed") or item.get("checked")):
                                checked_items += 1

        is_complete = (total_items > 0 and checked_items == total_items) or ((pkg.packing_score or 0) >= 100.0)

        if is_complete:
            generated_specs.append({
                "title": "Packing list completed",
                "description": "All packing list items have been packed.",
                "category": "PACKING",
                "priority": "LOW",
                "source": "PACKING",
                "action_type": "PACKING_DONE",
                "action_target": "/packing",
                "due_date": trip_start_dt - timedelta(days=1) if trip_start_dt else None
            })
        else:
            generated_specs.append({
                "title": "Complete your packing list",
                "description": f"{checked_items}/{total_items} items packed." if total_items > 0 else "Review items on your packing list.",
                "category": "PACKING",
                "priority": "HIGH",
                "source": "PACKING",
                "action_type": "COMPLETE_PACKING",
                "action_target": "/packing",
                "due_date": trip_start_dt - timedelta(days=1) if trip_start_dt else None
            })

    # ---------------------------------------------------------
    # 3. BUDGET RULES
    # ---------------------------------------------------------
    budget_obj = db.query(Budget).filter(Budget.trip_id == trip_id).first()
    trip_budget = float(trip.budget or 0)
    total_budget = float(budget_obj.total_budget) if budget_obj else trip_budget

    expenses = db.query(Expense).filter(Expense.trip_id == trip_id).all()
    total_spent = sum(float(e.amount or 0) for e in expenses)
    if budget_obj and float(budget_obj.spent or 0) > 0:
        total_spent = max(total_spent, float(budget_obj.spent))

    if total_budget <= 0:
        generated_specs.append({
            "title": "Set a budget for this trip",
            "description": "Define a financial budget to track your travel expenses.",
            "category": "MONEY",
            "priority": "HIGH",
            "source": "BUDGET",
            "action_type": "SET_BUDGET",
            "action_target": "/budget",
            "due_date": trip_start_dt - timedelta(days=7) if trip_start_dt else None
        })
    elif total_spent >= total_budget:
        generated_specs.append({
            "title": "Trip budget exceeded — review expenses",
            "description": f"Spent ${total_spent:.2f} out of ${total_budget:.2f} budget limit.",
            "category": "MONEY",
            "priority": "URGENT",
            "source": "BUDGET",
            "action_type": "BUDGET_EXCEEDED",
            "action_target": "/budget",
            "due_date": now_utc
        })
    elif total_spent >= (total_budget * 0.8):
        generated_specs.append({
            "title": "Review your remaining trip budget",
            "description": f"Spent ${total_spent:.2f} ({(total_spent/total_budget)*100:.1f}%) of your ${total_budget:.2f} budget.",
            "category": "MONEY",
            "priority": "HIGH",
            "source": "BUDGET",
            "action_type": "REVIEW_BUDGET",
            "action_target": "/budget",
            "due_date": trip_start_dt
        })

    # ---------------------------------------------------------
    # 4. TRANSIT / BOOKING RULES
    # ---------------------------------------------------------
    bookings = db.query(TripBooking).filter(TripBooking.trip_id == trip_id).all()
    confirmed_bookings = [b for b in bookings if (b.status or "").lower() == "confirmed"]

    if confirmed_bookings:
        generated_specs.append({
            "title": "Review your transportation booking",
            "description": f"You have {len(confirmed_bookings)} confirmed booking(s).",
            "category": "BOOKINGS",
            "priority": "LOW",
            "source": "TRANSIT",
            "action_type": "REVIEW_BOOKING",
            "action_target": "/transit",
            "due_date": trip_start_dt - timedelta(days=3) if trip_start_dt else None
        })
    else:
        generated_specs.append({
            "title": "Confirm transportation for your trip",
            "description": "No verified transportation booking found for this trip.",
            "category": "BOOKINGS",
            "priority": "HIGH",
            "source": "TRANSIT",
            "action_type": "CONFIRM_TRANSIT",
            "action_target": "/transit",
            "due_date": trip_start_dt - timedelta(days=7) if trip_start_dt else None
        })

    # ---------------------------------------------------------
    # 5. ITINERARY RULES
    # ---------------------------------------------------------
    itinerary_days = db.query(ItineraryDay).filter(ItineraryDay.trip_id == trip_id).all()
    has_activities = any(len(d.activities) > 0 for d in itinerary_days) if itinerary_days else False

    if not itinerary_days or not has_activities:
        generated_specs.append({
            "title": "Create your trip itinerary",
            "description": "Plan your daily schedule and activities.",
            "category": "ITINERARY",
            "priority": "HIGH",
            "source": "TRIP",
            "action_type": "CREATE_ITINERARY",
            "action_target": f"/trips/{trip_id}",
            "due_date": trip_start_dt - timedelta(days=5) if trip_start_dt else None
        })
    else:
        generated_specs.append({
            "title": "Review your itinerary",
            "description": f"Your trip has {len(itinerary_days)} planned day(s).",
            "category": "ITINERARY",
            "priority": "LOW",
            "source": "TRIP",
            "action_type": "REVIEW_ITINERARY",
            "action_target": f"/trips/{trip_id}",
            "due_date": trip_start_dt
        })

    # ---------------------------------------------------------
    # 6. WEATHER RULES
    # ---------------------------------------------------------
    if trip.destination:
        generated_specs.append({
            "title": "Check the weather before packing",
            "description": f"Check live weather forecast for {trip.destination}.",
            "category": "WEATHER",
            "priority": "LOW",
            "source": "WEATHER",
            "action_type": "CHECK_WEATHER",
            "action_target": "/weather",
            "due_date": trip_start_dt - timedelta(days=2) if trip_start_dt else None
        })

    # ---------------------------------------------------------
    # DEDUPLICATION & PERSISTENCE
    # ---------------------------------------------------------
    # Fetch existing auto-generated items for this trip
    existing_items = db.query(ChecklistItem).filter(
        ChecklistItem.trip_id == trip_id,
        ChecklistItem.user_id == user_id,
        ChecklistItem.is_auto_generated == True
    ).all()

    # Key existing by (source, category) or action_type
    existing_by_key: Dict[str, ChecklistItem] = {}
    for item in existing_items:
        key = item.action_type or f"{item.source}_{item.category}"
        existing_by_key[key] = item

    current_keys = set()
    result_items: List[ChecklistItem] = []

    for spec in generated_specs:
        key = spec["action_type"] or f"{spec['source']}_{spec['category']}"
        current_keys.add(key)

        if key in existing_by_key:
            # Update existing auto-generated item in place
            item = existing_by_key[key]
            item.title = spec["title"]
            item.description = spec["description"]
            item.category = spec["category"]
            item.priority = spec["priority"]
            item.source = spec["source"]
            item.action_target = spec["action_target"]
            item.due_date = spec["due_date"]
            result_items.append(item)
        else:
            # Create new auto-generated item
            new_item = ChecklistItem(
                user_id=user_id,
                trip_id=trip_id,
                title=spec["title"],
                description=spec["description"],
                category=spec["category"],
                priority=spec["priority"],
                status="PENDING",
                due_date=spec["due_date"],
                source=spec["source"],
                action_type=spec["action_type"],
                action_target=spec["action_target"],
                is_auto_generated=True,
            )
            db.add(new_item)
            result_items.append(new_item)

    # Clean up obsolete auto-generated items for category groups that were superseded
    # (e.g. 'UPLOAD_PASSPORT' superseded by 'PASSPORT_READY' when user uploaded passport)
    for key, item in existing_by_key.items():
        if key not in current_keys:
            # If an item was marked COMPLETED by user, keep it or remove obsolete item if pending
            if item.status == "PENDING":
                db.delete(item)

    db.commit()

    # Return all checklist items (auto-generated + user custom) sorted by priority & status
    all_items = db.query(ChecklistItem).filter(
        ChecklistItem.trip_id == trip_id,
        ChecklistItem.user_id == user_id
    ).all()

    return all_items


def calculate_readiness_score(items: List[ChecklistItem]) -> Dict[str, Any]:
    total = len(items)
    completed = sum(1 for item in items if item.status == "COMPLETED")
    pending = sum(1 for item in items if item.status == "PENDING")
    skipped = sum(1 for item in items if item.status == "SKIPPED")
    urgent = sum(1 for item in items if item.priority == "URGENT" and item.status == "PENDING")

    readiness_percentage = round((completed / total) * 100) if total > 0 else 0

    return {
        "total": total,
        "completed": completed,
        "pending": pending,
        "skipped": skipped,
        "urgent": urgent,
        "readiness_percentage": readiness_percentage
    }
