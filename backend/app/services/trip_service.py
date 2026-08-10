import secrets
from datetime import date, datetime, timedelta
from typing import List, Optional, Dict, Any
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, func

from app.models.trip import Trip
from app.models.itinerary import ItineraryDay, ItineraryActivity
from app.models.place import Place
from app.models.expense import Expense
from app.schemas.trip_schemas import (
    TripCreate, TripUpdate, ActivityCreate, ActivityUpdate, ActivityReorder, FilterTripsRequest
)


def to_decimal(value: Any) -> Decimal:
    """Defensive helper to safely convert float, int, str, Decimal, or None to Decimal('0')."""
    if value is None:
        return Decimal("0")
    try:
        return Decimal(str(value))
    except Exception:
        return Decimal("0")


def calculate_trip_metrics(trip: Trip, db: Session) -> Dict[str, Any]:
    """Calculate duration, countdown, progress, and budget metrics for a Trip object safely using Decimal math."""
    today = date.today()
    start = trip.start_date
    end = trip.end_date
    
    number_of_days = max(1, (end - start).days + 1) if (start and end) else 1
    days_left = (start - today).days if start else 0
    
    # Trip Progress percentage (0.0 to 100.0)
    if not start or not end or today < start:
        trip_progress = 0.0
        countdown = f"{days_left} day{'s' if days_left != 1 else ''} to departure" if start else "Upcoming"
    elif today > end:
        trip_progress = 100.0
        countdown = "Trip Completed"
    else:
        elapsed = (today - start).days + 1
        trip_progress = round(min(100.0, max(0.0, (elapsed / number_of_days) * 100.0)), 1)
        countdown = f"In Progress (Day {elapsed} of {number_of_days})"

    group_size = max(1, trip.group_size or 1)
    
    budget_dec = to_decimal(trip.budget)
    num_days_dec = Decimal(str(number_of_days))
    group_size_dec = Decimal(str(group_size))

    estimated_daily_budget = float(round(budget_dec / num_days_dec, 2))
    budget_per_person = float(round(budget_dec / group_size_dec, 2))

    # Calculate actual expenses from Expense model safely using Decimal
    total_expenses_dec = Decimal("0")
    try:
        expense_records = db.query(Expense).filter(Expense.trip_id == trip.id).all()
        total_expenses_dec = sum((to_decimal(e.amount) for e in expense_records), Decimal("0"))
    except Exception:
        pass

    total_budget_remaining_dec = max(Decimal("0"), budget_dec - total_expenses_dec)
    total_budget_remaining = float(round(total_budget_remaining_dec, 2))

    return {
        "number_of_days": number_of_days,
        "days_left": max(0, days_left),
        "trip_progress": trip_progress,
        "countdown": countdown,
        "estimated_daily_budget": estimated_daily_budget,
        "budget_per_person": budget_per_person,
        "total_budget_remaining": total_budget_remaining
    }


def enrich_trip_response(trip: Trip, db: Session) -> Dict[str, Any]:
    """Convert SQLAlchemy Trip object to dictionary enriched with dynamic metrics, SQL aggregations, and serialized itinerary."""
    from app.utils.currency_formatter import format_currency
    from app.core.currencies import get_currency_symbol
    from app.services.cover_image_service import CoverImageService

    today = date.today()
    start = trip.start_date
    end = trip.end_date

    duration_days = max(1, (end - start).days + 1) if (start and end) else 1
    days_to_start = (start - today).days if start else 0

    # 1. Status Determination
    if trip.status == "Cancelled":
        trip_status = "Cancelled"
    elif not start or not end or today < start:
        trip_status = "Upcoming"
    elif start <= today <= end:
        trip_status = "Active"
    else:
        trip_status = "Completed"

    countdown_days = max(0, days_to_start) if start else 0

    current_trip_day = None
    if trip_status == "Active" and start:
        current_trip_day = (today - start).days + 1

    # 2. SQL Aggregations for Activity & Expense Metrics
    activities_total = db.query(func.count(ItineraryActivity.id)).join(ItineraryDay).filter(ItineraryDay.trip_id == trip.id).scalar() or 0
    activities_completed = db.query(func.count(ItineraryActivity.id)).join(ItineraryDay).filter(
        ItineraryDay.trip_id == trip.id,
        ItineraryActivity.is_completed == True
    ).scalar() or 0

    spent_dec = db.query(func.coalesce(func.sum(Expense.amount), Decimal("0"))).filter(Expense.trip_id == trip.id).scalar() or Decimal("0")
    budget_spent = float(spent_dec)
    budget_dec = to_decimal(trip.budget)
    budget_remaining = float(max(Decimal("0"), budget_dec - spent_dec))

    budget_usage_percentage = round((budget_spent / float(budget_dec) * 100.0), 1) if float(budget_dec) > 0 else 0.0
    if budget_usage_percentage > 100.0:
        budget_health = "Exceeded"
    elif budget_usage_percentage >= 80.0:
        budget_health = "Warning"
    else:
        budget_health = "Healthy"

    # Trip Progress percentage
    if activities_total > 0:
        trip_progress = round((activities_completed / activities_total) * 100.0, 1)
    elif trip_status == "Active":
        trip_progress = round(((current_trip_day or 1) / duration_days) * 100.0, 1)
    elif trip_status == "Completed":
        trip_progress = 100.0
    else:
        trip_progress = 0.0

    # 3. Cover Image Resolution
    cover_image = CoverImageService.get_cover_image(trip.destination, trip.image_url)

    # 4. Smart Weather Integration (Only Active or Upcoming within 7 days)
    weather_summary = None
    if trip_status == "Active" or (trip_status == "Upcoming" and 0 <= days_to_start <= 7):
        try:
            from app.routes.weather import get_weather
            w_data = get_weather(trip.destination)
            curr = w_data.get("current", {})
            desc = curr.get("description", "Sunny")
            temp = curr.get("temperature", 31.0)
            weather_summary = f"{desc} • {int(round(temp))}°C"
        except Exception:
            weather_summary = "Sunny • 30°C"

    # 5. Next Activity & Quick Insights
    next_activity = None
    if trip_status == "Active":
        raw_next = db.query(ItineraryActivity).join(ItineraryDay).filter(
            ItineraryDay.trip_id == trip.id,
            ItineraryActivity.is_completed == False
        ).order_by(ItineraryDay.day_number.asc(), ItineraryActivity.order_index.asc()).first()

        if raw_next:
            next_activity = {
                "id": raw_next.id,
                "title": raw_next.title,
                "start_time": raw_next.start_time or "09:00",
                "time_slot": raw_next.time_slot or "morning",
                "estimated_duration": raw_next.estimated_duration or "90 mins"
            }

    quick_insights = {
        "activities": activities_total,
        "attractions": activities_total,
        "walking_distance": f"{round(activities_total * 0.8, 1)} km",
        "travel_time": f"{max(1, activities_total * 30 // 60)}h {(activities_total * 30) % 60}m"
    }

    metrics = calculate_trip_metrics(trip, db)
    curr_code = trip.currency or "USD"
    curr_symbol = get_currency_symbol(curr_code)

    serialized_days = []
    days = sorted(trip.itinerary_days or [], key=lambda d: d.day_number)
    for day in days:
        acts = sorted(day.activities or [], key=lambda a: a.order_index)
        serialized_acts = []
        for act in acts:
            place_dict = None
            if act.place:
                place_dict = {
                    "id": act.place.id,
                    "name": act.place.name,
                    "category": act.place.category,
                    "city": act.place.city,
                    "country": act.place.country,
                    "latitude": act.place.latitude,
                    "longitude": act.place.longitude,
                    "address": act.place.address,
                    "rating": act.place.rating,
                    "ticket_price": float(to_decimal(act.place.ticket_price)),
                    "google_maps_url": act.place.google_maps_url,
                    "google_place_id": getattr(act.place, "google_place_id", None),
                    "osm_id": getattr(act.place, "osm_id", None),
                    "timezone": getattr(act.place, "timezone", None)
                }

            cost_amt = float(to_decimal(act.ticket_price))
            cost_obj = {
                "amount": cost_amt,
                "currency": curr_code,
                "symbol": curr_symbol,
                "estimated": True
            }
            formatted_cost_str = format_currency(cost_amt, curr_code)

            serialized_acts.append({
                "id": act.id,
                "day_id": act.day_id,
                "place_id": act.place_id,
                "time_slot": act.time_slot,
                "start_time": act.start_time,
                "end_time": act.end_time,
                "duration_minutes": getattr(act, "duration_minutes", 90) or 90,
                "order_index": act.order_index,
                "title": act.title,
                "description": act.description,
                "estimated_duration": act.estimated_duration,
                "ticket_price": cost_amt,
                "cost": cost_obj,
                "formatted_cost": formatted_cost_str,
                "transport_mode": act.transport_mode,
                "transport_duration": act.transport_duration,
                "weather_suitability": act.weather_suitability,
                "crowd_level": act.crowd_level,
                "ai_reason": act.ai_reason,
                "confidence_score": act.confidence_score,
                "is_locked": act.is_locked,
                "completed": bool(getattr(act, "is_completed", False)),
                "completed_at": act.completed_at.isoformat() if getattr(act, "completed_at", None) else None,
                "place": place_dict,
                "metadata": getattr(act, "activity_metadata", None)
            })

        serialized_days.append({
            "id": day.id,
            "trip_id": day.trip_id,
            "day_number": day.day_number,
            "date": day.date.isoformat() if hasattr(day.date, "isoformat") else str(day.date),
            "title": day.title,
            "theme_note": day.theme_note,
            "activities": serialized_acts
        })

    budget_val = float(to_decimal(trip.budget)) if trip.budget is not None else None

    return {
        "id": trip.id,
        "user_id": trip.user_id,
        "title": trip.title or f"Trip to {trip.destination}",
        "destination": trip.destination,
        "country": trip.country,
        "origin_city": trip.origin_city,
        "origin_airport": trip.origin_airport,
        "destination_airport": trip.destination_airport,
        "start_date": trip.start_date.isoformat() if hasattr(trip.start_date, "isoformat") else str(trip.start_date),
        "end_date": trip.end_date.isoformat() if hasattr(trip.end_date, "isoformat") else str(trip.end_date),
        "budget": budget_val if budget_val is not None else trip.budget,
        "currency": curr_code,
        "currency_symbol": curr_symbol,
        "travel_type": trip.travel_type,
        "travel_style": trip.travel_style,
        "transportation": trip.transportation,
        "accommodation_preference": trip.accommodation_preference,
        "interests": trip.interests,
        "travel_companion": trip.travel_companion,
        "group_size": trip.group_size,
        "visibility": trip.visibility,
        "notes": trip.notes,
        "status": trip.status,
        "trip_status": trip_status,
        "countdown_days": countdown_days,
        "current_trip_day": current_trip_day,
        "duration_days": duration_days,
        "activities_total": activities_total,
        "activities_completed": activities_completed,
        "budget_spent": budget_spent,
        "budget_remaining": budget_remaining,
        "budget_usage_percentage": budget_usage_percentage,
        "budget_health": budget_health,
        "trip_progress": trip_progress,
        "cover_image": cover_image,
        "weather_summary": weather_summary,
        "next_activity": next_activity,
        "quick_insights": quick_insights,
        "last_opened_at": trip.last_opened_at.isoformat() if (hasattr(trip, "last_opened_at") and trip.last_opened_at) else None,
        "is_favorite": trip.is_favorite,
        "is_archived": trip.is_archived,
        "color_theme": trip.color_theme,
        "image_url": trip.image_url,
        "share_token": trip.share_token,
        "trip_preferences": getattr(trip, "trip_preferences", None),
        "created_at": trip.created_at.isoformat() if hasattr(trip.created_at, "isoformat") else str(trip.created_at),
        "updated_at": trip.updated_at.isoformat() if (trip.updated_at and hasattr(trip.updated_at, "isoformat")) else str(trip.updated_at or ""),
        "number_of_days": metrics["number_of_days"],
        "days_left": metrics["days_left"],
        "countdown": metrics["countdown"],
        "estimated_daily_budget": metrics["estimated_daily_budget"],
        "budget_per_person": metrics["budget_per_person"],
        "total_budget_remaining": metrics["total_budget_remaining"],
        "itinerary_days": serialized_days
    }


DESTINATION_ALIASES = {
    "nyc": "New York",
    "new york city": "New York",
    "ny": "New York",
    "blr": "Bengaluru",
    "bangalore": "Bengaluru",
    "bombay": "Mumbai",
    "bom": "Mumbai",
    "calcutta": "Kolkata",
    "ccu": "Kolkata",
    "madras": "Chennai",
    "maa": "Chennai",
    "cochin": "Kochi",
    "cok": "Kochi",
    "saigon": "Ho Chi Minh City",
}


def normalize_destination(dest: Optional[str]) -> str:
    if not dest:
        return ""
    clean = dest.strip().lower()
    if clean in DESTINATION_ALIASES:
        return DESTINATION_ALIASES[clean]
    return dest.strip().title()


def check_duplicate_trip(db: Session, user_id: int, destination: str, start_date: date) -> Dict[str, Any]:
    norm_target = normalize_destination(destination).lower()
    trips = db.query(Trip).filter(Trip.user_id == user_id, Trip.is_archived == False).all()
    for t in trips:
        if normalize_destination(t.destination).lower() == norm_target:
            if t.start_date and abs((t.start_date - start_date).days) <= 7:
                return {
                    "has_duplicate": True,
                    "existing_trip_id": t.id,
                    "existing_trip_title": t.title or t.destination,
                    "existing_start_date": t.start_date.isoformat() if hasattr(t.start_date, "isoformat") else str(t.start_date),
                    "message": f"You already have a trip to {normalize_destination(destination)} starting on {t.start_date}. Continue anyway?"
                }
    return {"has_duplicate": False}


def get_user_trip_stats(db: Session, user_id: int) -> Dict[str, Any]:
    today = date.today()
    user_trips = db.query(Trip).filter(Trip.user_id == user_id, Trip.is_archived == False).all()

    total_trips = len(user_trips)
    active_count = 0
    upcoming_count = 0
    completed_count = 0
    countries = set()
    total_budget_dec = Decimal("0")
    days_travelled = 0

    for t in user_trips:
        if t.country:
            countries.add(t.country.strip().title())
        elif t.destination:
            countries.add(t.destination.strip().title())
        total_budget_dec += to_decimal(t.budget)

        st = t.start_date
        en = t.end_date
        num_days = max(1, (en - st).days + 1) if (st and en) else 1

        if t.status == "Cancelled":
            pass
        elif st and en:
            if today < st:
                upcoming_count += 1
            elif st <= today <= en:
                active_count += 1
                days_travelled += (today - st).days + 1
            else:
                completed_count += 1
                days_travelled += num_days

    acts_planned = db.query(func.count(ItineraryActivity.id)).join(ItineraryDay).join(Trip).filter(
        Trip.user_id == user_id,
        Trip.is_archived == False
    ).scalar() or 0

    return {
        "totalTrips": total_trips,
        "active": active_count,
        "upcoming": upcoming_count,
        "completed": completed_count,
        "countriesVisited": len(countries),
        "totalBudget": float(round(total_budget_dec, 2)),
        "daysTravelled": days_travelled,
        "activitiesPlanned": acts_planned
    }


def get_active_trip_spotlight(db: Session, user_id: int) -> Optional[Dict[str, Any]]:
    today = date.today()
    active_trips = db.query(Trip).filter(
        Trip.user_id == user_id,
        Trip.is_archived == False,
        Trip.start_date <= today,
        today <= Trip.end_date,
        Trip.status != "Cancelled"
    ).all()

    if not active_trips:
        return None

    # Priority tie-breaker: 1. Nearest ending (end_date asc), 2. Most recently started (start_date desc), 3. Lowest ID (id asc)
    active_trips.sort(key=lambda t: (t.end_date, -int(t.start_date.strftime("%Y%m%d")), t.id))
    selected_trip = active_trips[0]
    return enrich_trip_response(selected_trip, db)


def touch_trip(db: Session, trip_id: int, user_id: int) -> Dict[str, Any]:
    trip = db.query(Trip).filter(Trip.id == trip_id, Trip.user_id == user_id).first()
    if trip:
        trip.last_opened_at = datetime.now()
        db.commit()
        db.refresh(trip)
        return enrich_trip_response(trip, db)
    return {"message": "Trip not found"}


def get_recently_viewed_trip(db: Session, user_id: int) -> Optional[Dict[str, Any]]:
    trip = db.query(Trip).filter(
        Trip.user_id == user_id,
        Trip.is_archived == False,
        Trip.last_opened_at.isnot(None)
    ).order_by(Trip.last_opened_at.desc()).first()

    if not trip:
        trip = db.query(Trip).filter(
            Trip.user_id == user_id,
            Trip.is_archived == False
        ).order_by(Trip.id.desc()).first()

    if trip:
        return enrich_trip_response(trip, db)
    return None


def get_paginated_user_trips(
    db: Session,
    user_id: int,
    page: int = 1,
    limit: int = 12,
    search: Optional[str] = None,
    status: Optional[str] = None,
    travel_style: Optional[str] = None,
    sort: Optional[str] = None
) -> Dict[str, Any]:
    today = date.today()
    query = db.query(Trip).filter(Trip.user_id == user_id)

    if status and status.lower() == "archived":
        query = query.filter(Trip.is_archived == True)
    else:
        query = query.filter(Trip.is_archived == False)

    if status and status.lower() not in ["all", "archived"]:
        st_lower = status.lower()
        if st_lower == "upcoming":
            query = query.filter(Trip.start_date > today, Trip.status != "Cancelled")
        elif st_lower in ["active", "in progress"]:
            query = query.filter(Trip.start_date <= today, today <= Trip.end_date, Trip.status != "Cancelled")
        elif st_lower == "completed":
            query = query.filter(today > Trip.end_date, Trip.status != "Cancelled")
        elif st_lower == "cancelled":
            query = query.filter(Trip.status == "Cancelled")
        elif st_lower == "favorites":
            query = query.filter(Trip.is_favorite == True)

    if travel_style and travel_style.lower() != "all":
        query = query.filter(func.lower(Trip.travel_style) == travel_style.lower())

    if search and search.strip():
        pattern = f"%{search.strip().lower()}%"
        query = query.filter(
            or_(
                func.lower(Trip.destination).like(pattern),
                func.lower(Trip.title).like(pattern),
                func.lower(Trip.country).like(pattern),
                func.lower(Trip.travel_style).like(pattern),
                func.lower(Trip.interests).like(pattern)
            )
        )

    # Sorting options
    if sort == "recently_completed":
        query = query.order_by(Trip.end_date.desc(), Trip.id.desc())
    elif sort == "budget_high_low":
        query = query.order_by(Trip.budget.desc(), Trip.id.desc())
    elif sort == "budget_low_high":
        query = query.order_by(Trip.budget.asc(), Trip.id.desc())
    elif sort == "longest_trip":
        query = query.order_by((Trip.end_date - Trip.start_date).desc(), Trip.id.desc())
    elif sort == "shortest_trip":
        query = query.order_by((Trip.end_date - Trip.start_date).asc(), Trip.id.desc())
    else:
        # Default: Upcoming First -> Soonest Start Date -> Destination -> ID
        query = query.order_by(Trip.start_date.asc(), Trip.destination.asc(), Trip.id.desc())

    total_count = query.count()
    page = max(1, page)
    limit = max(1, min(100, limit))
    offset = (page - 1) * limit

    trips = query.offset(offset).limit(limit).all()
    total_pages = max(1, (total_count + limit - 1) // limit)

    return {
        "trips": [enrich_trip_response(t, db) for t in trips],
        "total": total_count,
        "page": page,
        "limit": limit,
        "total_pages": total_pages
    }


def get_or_create_place(
    db: Session,
    name: str,
    category: str = "sightseeing",
    city: Optional[str] = None,
    country: Optional[str] = None,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    address: Optional[str] = None,
    rating: Optional[float] = 4.5,
    ticket_price: Optional[float] = 0.0,
    google_maps_url: Optional[str] = None
) -> Place:
    """Cache and reuse Place entities by name + city + country to avoid duplicated location data."""
    if not name or not name.strip():
        name = "Local Attraction"

    clean_name = name.strip()
    query = db.query(Place).filter(func.lower(Place.name) == clean_name.lower())
    if city and city.strip():
        query = query.filter(func.lower(Place.city) == city.strip().lower())
    if country and country.strip():
        query = query.filter(func.lower(Place.country) == country.strip().lower())
        
    place = query.first()
    
    if not place:
        maps_url = google_maps_url or f"https://www.google.com/maps/search/?api=1&query={clean_name.replace(' ', '+')}"
        if city:
            maps_url += f"+{city.replace(' ', '+')}"
            
        place = Place(
            name=clean_name,
            category=category or "sightseeing",
            latitude=latitude,
            longitude=longitude,
            address=address or f"{clean_name}, {city or ''}".strip(", "),
            city=city,
            country=country,
            rating=rating or 4.5,
            ticket_price=float(to_decimal(ticket_price)),
            google_maps_url=maps_url
        )
        db.add(place)
        db.commit()
        db.refresh(place)
    else:
        # Update missing place metadata if provided
        updated = False
        if latitude is not None and not place.latitude:
            place.latitude = latitude
            updated = True
        if longitude is not None and not place.longitude:
            place.longitude = longitude
            updated = True
        if address and not place.address:
            place.address = address
            updated = True
        if country and not place.country:
            place.country = country
            updated = True
        if updated:
            db.commit()
            db.refresh(place)

    return place


def create_trip(db: Session, data: TripCreate) -> Trip:
    """Create a new trip record in DB."""
    share_token = secrets.token_urlsafe(12)
    title = data.title or f"Trip to {data.destination}"
    
    trip = Trip(
        user_id=data.user_id,
        title=title,
        destination=data.destination,
        country=data.country,
        origin_city=data.origin_city or "Coimbatore",
        origin_airport=data.origin_airport,
        destination_airport=data.destination_airport,
        start_date=data.start_date,
        end_date=data.end_date,
        budget=data.budget,
        currency=data.currency or "USD",
        travel_type=data.travel_type or "leisure",
        travel_style=data.travel_style or "solo",
        transportation=data.transportation or "flight",
        accommodation_preference=data.accommodation_preference or "hotel",
        interests=data.interests or "sightseeing",
        travel_companion=data.travel_companion or "solo",
        group_size=data.group_size or 1,
        visibility=data.visibility or "private",
        notes=data.notes,
        color_theme=data.color_theme or "blue",
        image_url=data.image_url,
        share_token=share_token,
        status="Upcoming"
    )
    db.add(trip)
    db.commit()
    db.refresh(trip)

    # Initialize Itinerary Days automatically based on start & end dates
    num_days = max(1, (data.end_date - data.start_date).days + 1)
    for day_idx in range(num_days):
        day_date = data.start_date + timedelta(days=day_idx)
        it_day = ItineraryDay(
            trip_id=trip.id,
            day_number=day_idx + 1,
            date=day_date,
            title=f"Day {day_idx + 1}: Explore {data.destination}"
        )
        db.add(it_day)
    db.commit()
    db.refresh(trip)
    return trip


def update_trip(db: Session, trip: Trip, data: TripUpdate) -> Trip:
    """Update trip attributes."""
    for field, value in data.model_dump(exclude_unset=True).items():
        if hasattr(trip, field) and value is not None:
            setattr(trip, field, value)
    
    # Recalculate status if dates updated
    today = date.today()
    if trip.start_date and trip.end_date:
        if trip.status not in ["Cancelled", "Archived"]:
            if today < trip.start_date:
                trip.status = "Upcoming"
            elif today > trip.end_date:
                trip.status = "Completed"
            else:
                trip.status = "In Progress"
                
    db.commit()
    db.refresh(trip)
    return trip


def duplicate_trip(db: Session, trip_id: int, user_id: int) -> Trip:
    """Duplicate an existing trip and its itinerary days & activities."""
    original = db.query(Trip).filter(Trip.id == trip_id).first()
    if not original:
        raise ValueError("Trip not found")

    new_share_token = secrets.token_urlsafe(12)
    new_trip = Trip(
        user_id=user_id,
        title=f"Copy of {original.title or original.destination}",
        destination=original.destination,
        country=original.country,
        origin_city=original.origin_city,
        origin_airport=original.origin_airport,
        destination_airport=original.destination_airport,
        start_date=original.start_date,
        end_date=original.end_date,
        budget=original.budget,
        currency=original.currency,
        travel_type=original.travel_type,
        travel_style=original.travel_style,
        transportation=original.transportation,
        accommodation_preference=original.accommodation_preference,
        interests=original.interests,
        travel_companion=original.travel_companion,
        group_size=original.group_size,
        visibility="private",
        notes=original.notes,
        color_theme=original.color_theme,
        image_url=original.image_url,
        share_token=new_share_token,
        status="Draft"
    )
    db.add(new_trip)
    db.commit()
    db.refresh(new_trip)

    # Copy itinerary days and activities
    for orig_day in original.itinerary_days:
        new_day = ItineraryDay(
            trip_id=new_trip.id,
            day_number=orig_day.day_number,
            date=orig_day.date,
            title=orig_day.title,
            theme_note=orig_day.theme_note
        )
        db.add(new_day)
        db.commit()
        db.refresh(new_day)

        for orig_act in orig_day.activities:
            new_act = ItineraryActivity(
                day_id=new_day.id,
                place_id=orig_act.place_id,
                time_slot=orig_act.time_slot,
                start_time=orig_act.start_time,
                end_time=orig_act.end_time,
                order_index=orig_act.order_index,
                title=orig_act.title,
                description=orig_act.description,
                estimated_duration=orig_act.estimated_duration,
                ticket_price=orig_act.ticket_price,
                transport_mode=orig_act.transport_mode,
                transport_duration=orig_act.transport_duration,
                weather_suitability=orig_act.weather_suitability,
                crowd_level=orig_act.crowd_level,
                ai_reason=orig_act.ai_reason,
                confidence_score=orig_act.confidence_score,
                is_locked=False
            )
            db.add(new_act)
    db.commit()
    db.refresh(new_trip)
    return new_trip


def search_trips(db: Session, user_id: int, query: str) -> List[Trip]:
    """Search trips by destination, title, country, or interests."""
    pattern = f"%{query.lower()}%"
    return db.query(Trip).filter(
        Trip.user_id == user_id,
        or_(
            func.lower(Trip.destination).like(pattern),
            func.lower(Trip.title).like(pattern),
            func.lower(Trip.country).like(pattern),
            func.lower(Trip.interests).like(pattern)
        )
    ).order_by(Trip.start_date.desc()).all()


def filter_trips(db: Session, filters: FilterTripsRequest) -> List[Trip]:
    """Filter trips with options for status, travel style, budget, favorite, archived."""
    query = db.query(Trip).filter(Trip.user_id == filters.user_id)
    
    if filters.status:
        query = query.filter(func.lower(Trip.status) == filters.status.lower())
    if filters.travel_style:
        query = query.filter(func.lower(Trip.travel_style) == filters.travel_style.lower())
    if filters.min_budget is not None:
        query = query.filter(Trip.budget >= filters.min_budget)
    if filters.max_budget is not None:
        query = query.filter(Trip.budget <= filters.max_budget)
    if filters.is_favorite is not None:
        query = query.filter(Trip.is_favorite == filters.is_favorite)
    if filters.is_archived is not None:
        query = query.filter(Trip.is_archived == filters.is_archived)

    return query.order_by(Trip.start_date.desc()).all()


def generate_smart_rule_suggestions(weather: Dict[str, Any], today_activities: List[Dict[str, Any]], active_trip: Trip) -> List[Dict[str, Any]]:
    suggestions = []
    curr_weather = weather.get("current", {}) if isinstance(weather, dict) else {}
    forecast_0 = (weather.get("forecast", [{}]) or [{}])[0] if isinstance(weather, dict) else {}

    temp = curr_weather.get("temperature", 25.0) or 25.0
    uv = curr_weather.get("uv_index", 0.0) or forecast_0.get("uv_index_max", 0.0) or 0.0
    precip_prob = forecast_0.get("precipitation_probability", 0) or forecast_0.get("precipitation_probability_max", 0) or 0
    precip_val = curr_weather.get("precipitation", 0.0) or forecast_0.get("precipitation", 0.0) or 0.0
    dest = active_trip.destination if active_trip else "your destination"

    # Rule 1: High UV Protection
    if uv >= 6.0:
        suggestions.append({
            "id": "rule_uv",
            "type": "warning",
            "icon": "☀️",
            "title": "High UV Radiation Alert",
            "message": f"UV Index is high today ({uv}). Wear sunscreen (SPF 30+), stay hydrated, and limit direct outdoor exposure between 1:00 PM – 3:00 PM."
        })

    # Rule 2: Rain Advisory
    if precip_prob > 25 or precip_val > 0.5:
        suggestions.append({
            "id": "rule_rain",
            "type": "advisory",
            "icon": "🌧️",
            "title": "Rain Expected Today",
            "message": f"Rain expected today ({precip_prob}% chance). Keep an umbrella handy. Indoor attractions are recommended later today."
        })

    # Rule 3: High Temperature Hydration
    if temp >= 32.0:
        suggestions.append({
            "id": "rule_heat",
            "type": "caution",
            "icon": "🌡️",
            "title": "High Heat Alert",
            "message": f"Warm weather today ({temp}°C) in {dest}. Carry water, take frequent breaks, and stay hydrated."
        })

    # Rule 4: Packed Schedule Tip
    if len(today_activities) >= 5:
        suggestions.append({
            "id": "rule_pace",
            "type": "info",
            "icon": "⏱️",
            "title": "Busy Schedule Tip",
            "message": f"You have {len(today_activities)} activities scheduled today! Allow extra buffer time between locations."
        })

    # Rule 5: Scenic Walking / Transit Tip
    has_walking = any(act.get("transport_mode") == "walking" for act in today_activities if isinstance(act, dict))
    if has_walking or not suggestions:
        suggestions.append({
            "id": "rule_walking",
            "type": "tip",
            "icon": "👟",
            "title": "Comfortable Walking Tip",
            "message": f"Wear comfortable footwear while exploring {dest}. Keep Google Maps offline areas saved for smooth navigation."
        })
    return suggestions



def get_dashboard_widgets(db: Session, user_id: int) -> Dict[str, Any]:
    """Build consolidated widget payload for Dashboard integration."""

    from app.services.recommendation_engine import RuleRecommendationService

    try:
        db.expire_all()
    except Exception:
        pass

    all_trips = db.query(Trip).filter(Trip.user_id == user_id, Trip.is_archived == False).all()

    today = date.today()
    now_dt = datetime.now()
    now_time_str = now_dt.strftime("%H:%M")

    active_trip = None
    upcoming_trips = []

    for t in all_trips:
        if t.start_date and t.end_date:
            if t.start_date <= today <= t.end_date:
                active_trip = t
            elif t.start_date > today:
                upcoming_trips.append(t)

    upcoming_trips.sort(key=lambda x: x.start_date)

    target_trip = active_trip or (upcoming_trips[0] if upcoming_trips else None)
    has_active_trip = bool(active_trip is not None)

    active_trip_resp = None
    days_to_next_flight = None
    today_serialized_activities = []
    completed_count = 0
    remaining_count = 0
    current_activity = None
    next_activity = None
    countdown_to_next_activity = None

    distance_travelled_today_km = 0.0
    walking_minutes_today = 0
    money_spent_today = 0.0

    trip_day_info = {
        "status": "No Trip",
        "current_trip_day": 0,
        "total_days": 0,
        "day_text": "No Active Trip"
    }

    weather_data = {}
    rule_suggestions = []
    weather_summary = {}
    smart_recommendation = {}

    if target_trip:
        active_trip_resp = enrich_trip_response(target_trip, db)

        # Dynamic Current Trip Day calculation using RuleRecommendationService
        trip_day_info = RuleRecommendationService.calculate_trip_day(target_trip.start_date, target_trip.end_date, today)

        if target_trip.start_date > today:
            days_to_next_flight = (target_trip.start_date - today).days
        else:
            days_to_next_flight = 0

        # Fetch weather for destination
        try:
            from app.routes.weather import get_weather
            weather_data = get_weather(target_trip.destination)
        except Exception:
            weather_data = {}

        # Find today's day from enriched trip response (first look for exact date match)
        itinerary_days = active_trip_resp.get("itinerary_days", []) or []
        today_str = today.isoformat()

        target_day = None
        for day in itinerary_days:
            if day.get("date") == today_str:
                target_day = day
                break

        if not target_day and itinerary_days:
            target_day = itinerary_days[0]

        if target_day:
            raw_activities = target_day.get("activities", []) or []

            # Enrich activities with dynamic status, weather & crowd badges
            for idx, act in enumerate(raw_activities):
                st = act.get("start_time") or "09:00"
                et = act.get("end_time") or "10:30"
                is_done = bool(act.get("completed"))

                target_day_date = getattr(target_day, 'date', None) if target_day else None
                status_info = RuleRecommendationService.compute_activity_status(
                    start_time=st,
                    end_time=et,
                    is_completed=is_done,
                    now_dt=now_dt,
                    activity_date=target_day_date,
                    trip_start_date=target_trip.start_date,
                    trip_end_date=target_trip.end_date
                )

                cat = act.get("place", {}).get("category", "") if act.get("place") else ""
                w_badge = RuleRecommendationService.get_weather_badge(act.get("title", ""), cat, act.get("weather_suitability", ""), weather_data, st)
                c_badge = RuleRecommendationService.get_crowd_badge(act.get("place", {}).get("rating", 4.8) if act.get("place") else 4.8, st, act.get("order_index", idx + 1))

                dist_km = round(0.6 + (idx * 0.5), 1)
                walk_mins = int(act.get("duration_minutes", 90))

                enriched_act = {
                    **act,
                    "activity_status": status_info["status"],
                    "status_badge": status_info["badge"],
                    "status_color": status_info["color"],
                    "countdown": status_info["countdown"],
                    "weather_badge": w_badge,
                    "crowd_badge": c_badge,
                    "distance_km": dist_km,
                    "walking_minutes": walk_mins
                }
                today_serialized_activities.append(enriched_act)

                if is_done:
                    completed_count += 1
                    distance_travelled_today_km += dist_km
                    walking_minutes_today += walk_mins
                    money_spent_today += float(act.get("ticket_price", 0.0) or 0.0)
                else:
                    remaining_count += 1

        # Identify Current & Next Activity
        incomplete_acts = [a for a in today_serialized_activities if not a.get("completed")]
        current_candidates = [a for a in incomplete_acts if a.get("activity_status") == "current"]
        upcoming_candidates = [a for a in incomplete_acts if a.get("activity_status") == "upcoming"]

        if current_candidates:
            current_activity = current_candidates[0]
            next_activity = upcoming_candidates[0] if upcoming_candidates else (incomplete_acts[1] if len(incomplete_acts) > 1 else None)
        elif upcoming_candidates:
            current_activity = upcoming_candidates[0]
            next_activity = upcoming_candidates[1] if len(upcoming_candidates) > 1 else None
        elif incomplete_acts:
            current_activity = incomplete_acts[0]
            next_activity = incomplete_acts[1] if len(incomplete_acts) > 1 else None
        elif today_serialized_activities:
            current_activity = today_serialized_activities[-1]
            next_activity = None


        if current_activity:
            countdown_to_next_activity = current_activity.get("countdown", "In Progress")

        # Generate weather summary & smart recommendations using RuleRecommendationService
        weather_summary = RuleRecommendationService.generate_weather_recommendations(weather_data)
        smart_recommendation = RuleRecommendationService.generate_smart_recommendations(weather_data, today_serialized_activities, target_trip)
        rule_suggestions = generate_smart_rule_suggestions(weather_data, today_serialized_activities, target_trip)

    total_count = len(today_serialized_activities)
    progress_percentage = float(round((completed_count / total_count) * 100, 1)) if total_count > 0 else 0.0

    # Calculate overall user budget & expenses
    total_budget_dec = sum((to_decimal(t.budget) for t in all_trips), Decimal("0"))
    total_expenses_dec = Decimal("0")
    try:
        exp_list = db.query(Expense).join(Trip).filter(Trip.user_id == user_id).all()
        total_expenses_dec = sum((to_decimal(e.amount) for e in exp_list), Decimal("0"))
        
        # Add expenses incurred today to money_spent_today
        today_exps = db.query(Expense).join(Trip).filter(Trip.user_id == user_id, Expense.expense_date == today).all()
        money_spent_today += sum((float(to_decimal(e.amount)) for e in today_exps), 0.0)
    except Exception:
        pass

    budget_remaining_dec = max(Decimal("0"), total_budget_dec - total_expenses_dec)

    total_budget = float(round(total_budget_dec, 2))
    total_expenses = float(round(total_expenses_dec, 2))
    budget_remaining = float(round(budget_remaining_dec, 2))

    return {
        "version": "1.0",
        "has_active_trip": has_active_trip,
        "active_trip": active_trip_resp,
        "trip_status": trip_day_info["status"],
        "current_trip_day": trip_day_info["current_trip_day"],
        "total_days": trip_day_info["total_days"],
        "day_text": trip_day_info["day_text"],
        "current_time": now_dt.strftime("%I:%M %p"),
        "current_date_str": now_dt.strftime("%d %B %Y"),
        "current_day_name": now_dt.strftime("%A"),
        "upcoming_trips_count": len(upcoming_trips),
        "days_to_next_flight": days_to_next_flight,
        "budget_remaining": budget_remaining,
        "total_budget": total_budget,
        "currency": target_trip.currency if target_trip else "USD",
        "trip_progress": active_trip_resp.get("trip_progress", 0.0) if active_trip_resp else 0.0,
        "today_plan": today_serialized_activities,
        "today_activities": today_serialized_activities,
        "completed_count": completed_count,
        "remaining_count": remaining_count,
        "total_count": total_count,
        "progress_percentage": progress_percentage,
        "current_activity": current_activity,
        "next_activity": next_activity,
        "countdown": countdown_to_next_activity,
        "countdown_to_next_activity": countdown_to_next_activity,
        "today_progress": {
            "completed_count": completed_count,
            "remaining_count": remaining_count,
            "total_count": total_count,
            "progress_percentage": progress_percentage,
            "distance_travelled_today_km": round(distance_travelled_today_km, 1),
            "walking_minutes_today": walking_minutes_today,
            "money_spent_today": round(money_spent_today, 2),
            "remaining_budget": budget_remaining
        },
        "weather": weather_data,
        "weather_summary": weather_summary,
        "smart_recommendation": smart_recommendation,
        "rule_suggestions": rule_suggestions,
        "quick_actions": [
            "Create Trip", "Add Expense", "Check Packing", "View Safety Alerts", "Convert Currency"
        ],
        "trip": active_trip_resp,
        "today": {
            "activities": today_serialized_activities,
            "completed": completed_count,
            "remaining": remaining_count,
            "total": total_count,
            "progress_percentage": progress_percentage,
            "distance_km": round(distance_travelled_today_km, 1),
            "walking_mins": walking_minutes_today,
            "money_spent": round(money_spent_today, 2)
        },
        "budget": {"total": total_budget, "remaining": budget_remaining, "expenses": total_expenses},
        "suggestions": rule_suggestions
    }


def get_today_itinerary(trip_id: int, db: Session, user_id: Optional[int] = None) -> Dict[str, Any]:
    """
    Fetch today's active execution itinerary for a specific trip with strict user isolation,
    activity status calculation (completed/current/upcoming/missed), weather smart replanning,
    and today's progress metrics.
    """
    from app.models.trip import Trip
    from app.models.itinerary import ItineraryDay, ItineraryActivity
    from app.models.expense import Expense
    from app.services.smart_replanner import SmartReplanner
    from app.services.recommendation_engine import RuleRecommendationService

    # 1. User Isolation & Trip Retrieval
    query = db.query(Trip).filter(Trip.id == trip_id)
    if user_id:
        query = query.filter(Trip.user_id == user_id)
    trip = query.first()
    if not trip:
        raise ValueError("Trip not found or unauthorized access")

    today = date.today()
    start_date = trip.start_date or today
    end_date = trip.end_date or today
    total_days = max(1, (end_date - start_date).days + 1)
    is_upcoming_trip = bool(trip.start_date and today < trip.start_date)

    # 2. Day Calculation Rules
    if today < start_date:
        current_day = 1
        status_label = "Upcoming"
    elif today > end_date:
        current_day = total_days
        status_label = "Completed"
    else:
        current_day = max(1, min(total_days, (today - start_date).days + 1))
        status_label = "Active"

    # 3. Fetch Matching Day (by day_number = current_day, or fallback to nearest available day)
    day = db.query(ItineraryDay).filter(
        ItineraryDay.trip_id == trip.id,
        ItineraryDay.day_number == current_day
    ).first()

    if not day:
        # Fallback to first available day
        day = db.query(ItineraryDay).filter(ItineraryDay.trip_id == trip.id).order_by(ItineraryDay.day_number.asc()).first()

    now_dt = datetime.now()
    now_time_str = now_dt.strftime("%H:%M")

    # Weather
    weather_summary = "Clear Sky 26°C"
    weather_info = {"temperature": 26, "condition": weather_summary}

    raw_activities = []
    if day:
        raw_activities = db.query(ItineraryActivity).filter(
            ItineraryActivity.day_id == day.id
        ).order_by(ItineraryActivity.order_index.asc(), ItineraryActivity.id.asc()).all()

    processed_activities = []
    completed_count = 0
    total_activities = len(raw_activities)

    for act in raw_activities:
        s_time = act.start_time or "09:00"
        e_time = act.end_time or "10:30"
        act_date = getattr(day, 'date', None) if day else None
        
        # Rule-based activity status calculation with trip date hierarchy
        status_info = RuleRecommendationService.compute_activity_status(
            start_time=s_time,
            end_time=e_time,
            is_completed=bool(act.is_completed),
            now_dt=now_dt,
            activity_date=act_date,
            trip_start_date=trip.start_date,
            trip_end_date=trip.end_date
        )
        status = status_info["status"]
        if act.is_completed:
            completed_count += 1

        processed_activities.append({
            "id": act.id,
            "day_id": act.day_id,
            "order": act.order_index,
            "title": act.title,
            "description": act.description,
            "time": s_time,
            "end_time": e_time,
            "duration": act.estimated_duration or "1.5 hours",
            "transport_mode": act.transport_mode or "walking",
            "transport_duration": act.transport_duration or "15 mins",
            "weather_suitability": act.weather_suitability or "all-weather",
            "crowd_level": act.crowd_level or "moderate",
            "status": status,
            "activity_status": status,
            "status_badge": status_info["badge"],
            "status_color": status_info["color"],
            "countdown": status_info["countdown"],
            "is_completed": act.is_completed or False,
            "completed": act.is_completed or False,
            "completed_at": act.completed_at.strftime("%I:%M %p") if act.completed_at else None,
            "is_locked": act.is_locked or False,
            "ticket_price": act.ticket_price or 0.0
        })

    # Weather Smart Recommendation (Rule Engine)
    smart_rec = SmartReplanner.evaluate_weather_recommendation(weather_summary, processed_activities)

    # Today's Progress Metrics
    pct = 0.0 if is_upcoming_trip else (round((completed_count / total_activities) * 100.0, 1) if total_activities > 0 else 0.0)

    # Today's Expenses
    today_expenses_dec = db.query(func.coalesce(func.sum(Expense.amount), Decimal("0"))).filter(
        Expense.trip_id == trip.id,
        Expense.expense_date == today
    ).scalar() or Decimal("0")

    formatted_start = trip.start_date.strftime("%d %b %Y") if trip.start_date else "the start date"

    return {
        "trip_id": trip.id,
        "destination": trip.destination,
        "country": trip.country,
        "trip_status": status_label,
        "is_upcoming_trip": is_upcoming_trip,
        "upcoming_notice": f"Your trip begins on {formatted_start}. Your itinerary is ready and will become active on the start date." if is_upcoming_trip else None,
        "date": today.strftime("%Y-%m-%d"),
        "date_formatted": today.strftime("%d %B %Y"),
        "current_day": current_day,
        "total_days": total_days,
        "day_title": day.title if day else f"Day {current_day} Exploration",
        "weather": {
            "temperature": weather_info.get("temperature", 26),
            "condition": weather_summary
        },
        "smart_recommendation": smart_rec,
        "activities": processed_activities,
        "progress": {
            "completed_count": completed_count,
            "total_count": total_activities,
            "percentage": pct,
            "walking_distance_km": round(completed_count * 1.2, 1) if not is_upcoming_trip else 0.0,
            "walking_time_mins": completed_count * 20 if not is_upcoming_trip else 0,
            "spent_today": float(today_expenses_dec) if not is_upcoming_trip else 0.0
        }
    }


def toggle_activity_completion(trip_id: int, activity_id: int, user_id: Optional[int], db: Session) -> Dict[str, Any]:
    """
    Toggle completion status for an itinerary activity with strict user isolation.
    """
    from app.models.trip import Trip
    from app.models.itinerary import ItineraryDay, ItineraryActivity
    from datetime import datetime, timezone

    query = db.query(Trip).filter(Trip.id == trip_id)
    if user_id:
        query = query.filter(Trip.user_id == user_id)
    trip = query.first()
    if not trip:
        raise ValueError("Trip not found or unauthorized")

    act = db.query(ItineraryActivity).join(ItineraryDay).filter(
        ItineraryActivity.id == activity_id,
        ItineraryDay.trip_id == trip.id
    ).first()

    if not act:
        raise ValueError("Activity not found")

    act.is_completed = not (act.is_completed or False)
    act.completed_at = datetime.now(timezone.utc) if act.is_completed else None

    db.commit()
    db.refresh(act)

    return {
        "id": act.id,
        "is_completed": act.is_completed,
        "completed_at": act.completed_at.strftime("%I:%M %p") if act.completed_at else None,
        "message": f"Activity marked as {'completed' if act.is_completed else 'pending'}"
    }



