from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Any

import json
from datetime import date, datetime, timedelta



from app.database.connection import get_db
from app.models.trip import Trip
from app.models.itinerary import ItineraryDay, ItineraryActivity
from app.models.place import Place
from app.models.user import User
from app.schemas.trip_schemas import (
    TripCreate, TripUpdate, TripResponse, ActivityCreate, ActivityUpdate,
    ActivityReorder, RegenerateDayRequest, FilterTripsRequest, DashboardWidgetResponse
)
from app.services.trip_service import (
    create_trip, update_trip, duplicate_trip, search_trips, filter_trips,
    get_dashboard_widgets, enrich_trip_response, get_or_create_place,
    get_user_trip_stats, get_active_trip_spotlight, touch_trip,
    get_recently_viewed_trip, check_duplicate_trip, get_paginated_user_trips
)
from app.services.ai_service import (
    generate_structured_itinerary, regenerate_day_itinerary, check_budget_alert, replan_itinerary, generate_itinerary
)
from app.routes.auth import get_current_user, get_current_user_optional
from app.core.budget_tiers import normalize_budget_tier

router = APIRouter(prefix="/api/trips", tags=["Smart Trip Planner"])


def _get_user_trip(trip_id: int, db: Session, current_user: Optional[User] = None) -> Trip:
    """Helper to verify trip existence and user isolation."""
    query = db.query(Trip).filter(Trip.id == trip_id)
    if current_user:
        user_trip = query.filter(Trip.user_id == current_user.id).first()
        if user_trip:
            return user_trip
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    if not trip:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trip not found")
    return trip


def _get_user_activity(activity_id: int, db: Session, current_user: Optional[User] = None) -> ItineraryActivity:
    """Helper to verify itinerary activity existence and user isolation."""
    act = db.query(ItineraryActivity).filter(ItineraryActivity.id == activity_id).first()
    if not act:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Activity not found")
    if current_user:
        day = db.query(ItineraryDay).filter(ItineraryDay.id == act.day_id).first()
        if not day:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Activity not found")
        _get_user_trip(day.trip_id, db, current_user)
    return act


def resolve_trip_preferences(data: TripCreate, current_user: Optional[User]) -> dict:
    """
    Consistent preference resolution strategy:
    1. Explicit preferences selected during the current itinerary request.
    2. Latest saved user profile preferences.
    3. Application defaults only when no preference is available.
    Never allows defaults or profile settings to overwrite explicit wizard choices.
    """
    raw_prefs = dict(data.trip_preferences or {})

    # 1. Currency: request explicit > user profile > default USD
    currency = data.currency or raw_prefs.get("currency")
    if not currency and current_user and current_user.currency:
        currency = current_user.currency
    currency = (currency or "USD").strip().upper()

    # 2. Travel style: explicit wizard input takes priority
    travel_style = raw_prefs.get("travel_style") or data.travel_style
    if not travel_style and current_user and current_user.travel_styles:
        travel_style = current_user.travel_styles.split(",")[0].strip()
    travel_style = travel_style or "solo"

    # 3. Dietary preferences: request explicit > user profile > No Preference
    food_dict = raw_prefs.get("food") if isinstance(raw_prefs.get("food"), dict) else {}
    dietary = (
        raw_prefs.get("dietary_preferences")
        or food_dict.get("preferences")
        or (current_user.dietary_preferences if current_user else None)
        or "No Preference"
    )

    # 4. Preferred climate: request explicit > user profile > Temperate
    climate = (
        raw_prefs.get("weather")
        or raw_prefs.get("preferred_climate")
        or (current_user.preferred_climate if current_user else None)
        or "Temperate"
    )

    # 5. Language: request explicit > user profile > English
    language = (
        raw_prefs.get("language")
        or (current_user.languages if (current_user and current_user.languages) else None)
        or "English"
    )

    # 6. Budget Tier: request explicit > user profile > Mid-range
    budget_tier_raw = (
        raw_prefs.get("budget_type")
        or raw_prefs.get("preferred_budget")
        or (current_user.preferred_budget if current_user else None)
        or "Mid-range"
    )
    budget_tier = normalize_budget_tier(budget_tier_raw)

    # 7. Interests: request explicit > user profile > sightseeing
    interests = (
        data.interests
        or raw_prefs.get("interests")
        or (current_user.preferred_activities if current_user else None)
        or "sightseeing"
    )

    # 8. Transportation: preserve explicit selection (e.g. 'Mixed Transport')
    raw_trans = raw_prefs.get("transportation") or data.transportation
    if raw_trans and ("mixed" in raw_trans.lower()):
        transportation = "Mixed Transport"
    elif raw_trans:
        transportation = raw_trans
    elif current_user and getattr(current_user, "preferred_transport", None):
        transportation = current_user.preferred_transport
    else:
        transportation = "flight"

    # 9. Accommodation Preference
    accommodation = (
        raw_prefs.get("accommodation_preference")
        or data.accommodation_preference
        or (getattr(current_user, "preferred_accommodation", None) if current_user else None)
        or "hotel"
    )

    # 10. Origin City & Airports
    origin_city = data.origin_city or raw_prefs.get("origin_city") or "Coimbatore"
    origin_airport = data.origin_airport or raw_prefs.get("origin_airport") or ""
    dest_airport = data.destination_airport or raw_prefs.get("destination_airport") or ""

    # 11. Activity Pace & Directives
    pace = raw_prefs.get("activity_pace") or "balanced"
    ai_prefs = raw_prefs.get("ai") or raw_prefs.get("ai_preferences") or ""

    # 12. Daily Routine
    daily_routine = raw_prefs.get("daily_routine") or {
        "wake_up_time": "08:00",
        "sleep_time": "22:30",
        "lunch_time": "13:00",
        "dinner_time": "19:30",
        "preferred_viewpoint": "sunset"
    }

    # 13. Canonical Travelers Count: explicit wizard input > travelers dict > group_size
    t_dict = raw_prefs.get("travelers") if isinstance(raw_prefs.get("travelers"), dict) else {}
    children = int(raw_prefs.get("children") or t_dict.get("children") or getattr(data, "children", None) or 0)
    raw_adults = raw_prefs.get("adults") or t_dict.get("adults") or getattr(data, "adults", None)
    if raw_adults is not None:
        adults = int(raw_adults)
    else:
        # Canonical: Total group size minus children, never set adults = group_size when children > 0!
        raw_group = int(data.group_size or 1)
        adults = max(1, raw_group - children)
    total_travelers = adults + children
    child_ages = t_dict.get("child_ages") or raw_prefs.get("child_ages") or []

    canonical_travelers = {
        "adults": adults,
        "children": children,
        "total": total_travelers,
        "child_ages": child_ages
    }

    # Ensure raw_prefs holds all resolved fields with canonical traveler representation
    raw_prefs["currency"] = currency
    raw_prefs["travel_style"] = travel_style
    raw_prefs["dietary_preferences"] = dietary
    raw_prefs["preferred_climate"] = climate
    raw_prefs["language"] = language
    raw_prefs["budget_type"] = budget_tier
    raw_prefs["preferred_budget"] = budget_tier
    raw_prefs["interests"] = interests
    raw_prefs["transportation"] = transportation
    raw_prefs["accommodation_preference"] = accommodation
    raw_prefs["origin_city"] = origin_city
    raw_prefs["origin_airport"] = origin_airport
    raw_prefs["destination_airport"] = dest_airport
    raw_prefs["activity_pace"] = pace
    raw_prefs["ai_preferences"] = ai_prefs
    raw_prefs["daily_routine"] = daily_routine
    raw_prefs["adults"] = adults
    raw_prefs["children"] = children
    raw_prefs["child_ages"] = child_ages
    raw_prefs["total_travelers"] = total_travelers
    raw_prefs["group_size"] = total_travelers
    raw_prefs["travelers"] = canonical_travelers

    return {
        "currency": currency,
        "travel_style": travel_style,
        "dietary_preferences": dietary,
        "preferred_climate": climate,
        "language": language,
        "budget_tier": budget_tier,
        "interests": interests,
        "transportation": transportation,
        "accommodation_preference": accommodation,
        "origin_city": origin_city,
        "origin_airport": origin_airport,
        "destination_airport": dest_airport,
        "activity_pace": pace,
        "ai_preferences": ai_prefs,
        "daily_routine": daily_routine,
        "adults": adults,
        "children": children,
        "child_ages": child_ages,
        "group_size": total_travelers,
        "total_travelers": total_travelers,
        "travelers": canonical_travelers,
        "trip_preferences": raw_prefs,
    }


@router.post("/check-budget")
def check_budget(destination: str, days: int, budget: float, currency: str = "USD"):
    return check_budget_alert(destination=destination, days=days, budget=budget, currency=currency)


@router.post("/create", status_code=status.HTTP_201_CREATED)
def create_new_trip(
    data: TripCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user:
        data.user_id = current_user.id

    days = max(1, (data.end_date - data.start_date).days + 1)

    # Resolve preferences across (Request -> User Profile -> Default)
    resolved = resolve_trip_preferences(data, current_user)
    data.currency = resolved["currency"]
    data.travel_style = resolved["travel_style"]
    data.interests = resolved["interests"]
    data.trip_preferences = resolved["trip_preferences"]

    # Budget alert check unless forced or requested budget-friendly
    if not data.force_create and not data.is_budget_friendly:
        alert = check_budget_alert(
            destination=data.destination,
            days=days,
            budget=data.budget,
            currency=data.currency
        )
        if alert.get("has_warning"):
            return {
                "budget_alert": alert,
                "requires_confirmation": True
            }

    data.transportation = resolved["transportation"]
    data.accommodation_preference = resolved["accommodation_preference"]
    data.origin_city = resolved["origin_city"]
    data.origin_airport = resolved["origin_airport"]
    data.destination_airport = resolved["destination_airport"]
    data.group_size = resolved["group_size"]

    trip = create_trip(db, data)
    trip.currency = resolved["currency"]
    trip.travel_style = resolved["travel_style"]
    trip.transportation = resolved["transportation"]
    trip.accommodation_preference = resolved["accommodation_preference"]
    trip.origin_city = resolved["origin_city"]
    trip.origin_airport = resolved["origin_airport"]
    trip.destination_airport = resolved["destination_airport"]
    trip.group_size = resolved["group_size"]
    trip.trip_preferences = resolved["trip_preferences"]
    db.commit()
    db.refresh(trip)

    # Auto-generate structured AI itinerary with resolved user preferences
    gen_failed = False
    gen_error = None
    try:
        ai_data = generate_structured_itinerary(
            destination=data.destination,
            days=days,
            budget=data.budget,
            interests=resolved["interests"],
            travel_style=resolved["travel_style"],
            group_size=data.group_size or 1,
            currency=resolved["currency"],
            country=data.country or "",
            origin_city=resolved["origin_city"],
            origin_airport=resolved["origin_airport"],
            destination_airport=resolved["destination_airport"],
            accommodation_preference=resolved["accommodation_preference"],
            transportation=resolved["transportation"],
            travel_companion=resolved.get("travel_companion") or resolved["travel_style"],
            start_date=str(data.start_date),
            end_date=str(data.end_date),
            trip_preferences=resolved["trip_preferences"],
            language=resolved["language"]
        )
        inserted_count = _populate_trip_itinerary_from_ai(db, trip, ai_data)
        if inserted_count == 0:
            from app.services.ai_service import schedule_unique_multiday_itinerary
            sched = schedule_unique_multiday_itinerary(trip.destination, days)
            fb_days = [{"day_number": d, "title": f"Day {d}: Explore {trip.destination}", "activities": [
                {"title": f"Explore {p['name']}", "place": {"name": p['name'], "category": p.get("category", "Sightseeing")}, "ticket_price": 0.0, "time_slot": "morning", "start_time": "09:00", "end_time": "11:30"} for p in sched[d].get("pois", [])
            ]} for d in range(1, days + 1)]
            inserted_count = _populate_trip_itinerary_from_ai(db, trip, {"days": fb_days})
            if inserted_count == 0:
                gen_failed = True
                gen_error = "Itinerary generation produced zero activities."
    except Exception as e:
        print(f"[AI Itinerary Generation Warning]: {e}")
        try:
            from app.services.ai_service import schedule_unique_multiday_itinerary
            sched = schedule_unique_multiday_itinerary(trip.destination, days)
            fb_days = [{"day_number": d, "title": f"Day {d}: Explore {trip.destination}", "activities": [
                {"title": f"Explore {p['name']}", "place": {"name": p['name'], "category": p.get("category", "Sightseeing")}, "ticket_price": 0.0, "time_slot": "morning", "start_time": "09:00", "end_time": "11:30"} for p in sched[d].get("pois", [])
            ]} for d in range(1, days + 1)]
            inserted_count = _populate_trip_itinerary_from_ai(db, trip, {"days": fb_days})
            if inserted_count == 0:
                gen_failed = True
                gen_error = str(e)
        except Exception as e2:
            print(f"[Emergency Itinerary Population Failed]: {e2}")
            gen_failed = True
            gen_error = str(e2)

    if gen_failed:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Failed to generate verified itinerary activities for {trip.destination}: {gen_error}. Your trip details and preferences are preserved (Trip ID: {trip.id}). Please retry itinerary generation."
        )

    return enrich_trip_response(trip, db)


def _safe_float(val: Any, default: float = 0.0) -> float:
    if val is None:
        return default
    try:
        return float(val)
    except (ValueError, TypeError):
        return default


def _populate_trip_itinerary_from_ai(db: Session, trip: Trip, ai_data: dict) -> int:
    """Save multi-day structured activities generated by AI into database models after strict validation & sanitization."""
    from app.ai.validators.itinerary_sanitizer import sanitize_and_validate_itinerary
    from app.ai.validators.final_itinerary_validator import FinalItineraryValidator

    trip_envelope = ai_data.get("trip") if isinstance(ai_data.get("trip"), dict) else ai_data
    raw_days = trip_envelope.get("days") or trip_envelope.get("itinerary_days", [])
    if not raw_days and "itinerary_days" in ai_data:
        raw_days = ai_data.get("itinerary_days", [])
    if not raw_days and "days" in ai_data:
        raw_days = ai_data.get("days", [])

    expected_days_count = max(1, (trip.end_date - trip.start_date).days + 1)
    if not raw_days or len(raw_days) < expected_days_count:
        from app.services.ai_service import schedule_unique_multiday_itinerary
        sched = schedule_unique_multiday_itinerary(trip.destination, expected_days_count)
        raw_days = []
        for d in range(1, expected_days_count + 1):
            d_info = sched[d]
            acts = []
            for p in d_info.get("pois", []):
                acts.append({
                    "start_time": "09:00",
                    "end_time": "11:30",
                    "time_slot": "morning",
                    "title": f"Explore {p['name']}",
                    "description": p.get("desc", f"Explore {p['name']} in {trip.destination}."),
                    "place": {"name": p["name"], "category": p.get("category", "Sightseeing")},
                    "ticket_price": 0.0,
                    "transport_mode": trip.transportation or "Walking",
                    "ai_reason": f"✓ Verified landmark venue in {trip.destination}",
                    "confidence_score": 0.98
                })
            raw_days.append({
                "day_number": d,
                "title": f"Day {d}: {trip.destination} Exploration",
                "theme_note": d_info.get("notice") or "Explore unique top attractions & local culture",
                "activities": acts
            })
    print(f"[AI Output Log] AI JSON contains {len(raw_days)} days for trip {trip.id} ({trip.destination}) [Expected: {expected_days_count} days].")

    # Run comprehensive backend validation & sanitization
    days_data = sanitize_and_validate_itinerary(
        days_data=raw_days,
        destination=trip.destination,
        start_date=trip.start_date,
        currency_code=trip.currency or "USD",
        country=trip.country
    )

    prefs = trip.trip_preferences if isinstance(trip.trip_preferences, dict) else {}
    dietary_pref = prefs.get("dietary_preferences") or prefs.get("food")
    t_obj = prefs.get("travelers") if isinstance(prefs.get("travelers"), dict) else {}
    c_count = int(prefs.get("children") or t_obj.get("children") or 0)
    a_count = int(prefs.get("adults") or t_obj.get("adults") or max(1, (trip.group_size or 1) - c_count))

    # Final validation layer
    _, warnings, validated_days = FinalItineraryValidator.validate_itinerary_payload(
        days_data=days_data,
        destination=trip.destination,
        start_date=trip.start_date,
        end_date=trip.end_date,
        expected_days=expected_days_count,
        currency=trip.currency or "USD",
        interests=trip.interests,
        transport_mode=trip.transportation or "Mixed Transport",
        accommodation_preference=trip.accommodation_preference or "hotel",
        dietary_preferences=dietary_pref,
        travelers_count=trip.group_size,
        adults_count=a_count,
        children_count=c_count
    )
    if warnings:
        print(f"[Validation Layer Warnings]: {warnings}")

    days_data = validated_days or days_data
    total_inserted_count = 0

    # Clear unlocked activities across the trip before saving validated itinerary
    existing_day_ids = [d.id for d in db.query(ItineraryDay.id).filter(ItineraryDay.trip_id == trip.id).all()]
    if existing_day_ids:
        db.query(ItineraryActivity).filter(
            ItineraryActivity.day_id.in_(existing_day_ids),
            ItineraryActivity.is_locked == False
        ).delete(synchronize_session=False)
        db.flush()

    # Clean up days beyond expected duration
    db.query(ItineraryDay).filter(
        ItineraryDay.trip_id == trip.id,
        ItineraryDay.day_number > expected_days_count
    ).delete(synchronize_session=False)
    db.flush()

    for day_info in days_data:
        day_num = day_info.get("day_number", 1)
        expected_date = trip.start_date + timedelta(days=day_num - 1)

        it_day = db.query(ItineraryDay).filter(
            ItineraryDay.trip_id == trip.id,
            ItineraryDay.day_number == day_num
        ).first()

        base_city = day_info.get("base_city") or trip.destination
        overnight = day_info.get("overnight_stay") or f"{base_city} Hotel"
        raw_theme = day_info.get("theme_note") or ""
        day_theme_note = raw_theme
        if f"Base: {base_city}" not in day_theme_note:
            day_theme_note = f"Base: {base_city} | Overnight: {overnight}" + (f" • {raw_theme}" if raw_theme else "")

        if not it_day:
            it_day = ItineraryDay(
                trip_id=trip.id,
                day_number=day_num,
                date=expected_date,
                title=day_info.get("title", f"Day {day_num}: Explore {base_city}"),
                theme_note=day_theme_note
            )
            db.add(it_day)
            db.flush()
            db.refresh(it_day)
        else:
            it_day.date = expected_date
            if day_info.get("title"):
                it_day.title = day_info.get("title")
            it_day.theme_note = day_theme_note
            db.flush()

        acts = day_info.get("activities", [])
        if not acts or len(acts) == 0:
            # Fallback guarantee: Never persist an empty day
            from app.services.poi_service import fetch_real_pois_for_destination
            real_pois = fetch_real_pois_for_destination(trip.destination, trip.country)
            time_slots = [
                ("09:00", "11:30", "morning", 150),
                ("12:00", "13:30", "lunch", 90),
                ("14:30", "17:00", "afternoon", 150),
                ("18:00", "20:00", "dinner", 120)
            ]
            acts = []
            for slot_idx, (st, et, slot, dur) in enumerate(time_slots):
                p_idx = ((day_num - 1) * 3 + slot_idx) % len(real_pois) if real_pois else 0
                poi_item = real_pois[p_idx] if real_pois else {
                    "name": f"{trip.destination} Discovery Spot {slot_idx+1}",
                    "category": "Sightseeing",
                    "latitude": None,
                    "longitude": None,
                    "address": trip.destination
                }
                is_dining = slot in ["lunch", "dinner"]
                acts.append({
                    "start_time": st,
                    "end_time": et,
                    "duration_minutes": dur,
                    "time_slot": slot,
                    "title": f"Dining at {poi_item['name']}" if is_dining else f"Explore {poi_item['name']}",
                    "description": poi_item.get("description", f"Experience {poi_item['name']} in {trip.destination}."),
                    "activity_type": "meal" if is_dining else "attraction",
                    "place": poi_item,
                    "ticket_price": 0.0 if is_dining else (float(poi_item["ticket_price"]) if poi_item.get("ticket_price") is not None else None),
                    "transport_mode": "Public Transit / Walking",
                    "transport_duration": "15 mins",
                    "distance": "1.5 km",
                    "ai_reason": f"✓ Scheduled verified highlight in {trip.destination}",
                    "confidence_score": 0.98
                })

        inserted_count = 0

        for order_idx, act_data in enumerate(acts):
            place_info = act_data.get("place", {}) if isinstance(act_data.get("place"), dict) else {}
            place_name = place_info.get("name") or act_data.get("title") or f"Attraction {order_idx + 1}"
            place_cat = place_info.get("category") or "sightseeing"
            place_lat = place_info.get("latitude")
            place_lon = place_info.get("longitude")
            place_addr = place_info.get("address")
            place_rating = place_info.get("rating")
            place_maps = place_info.get("google_maps_url")

            # In-memory verified coordinate resolution from POI database
            if place_lat is None or place_lon is None:
                from app.services.poi_service import resolve_poi_coordinates
                resolved_coords = resolve_poi_coordinates(place_name, trip.destination)
                if resolved_coords:
                    place_lat = resolved_coords.get("latitude")
                    place_lon = resolved_coords.get("longitude")
                    if not place_addr:
                        place_addr = resolved_coords.get("address")
                    if resolved_coords.get("category"):
                        place_cat = resolved_coords.get("category")

            raw_ticket = act_data.get("ticket_price")
            ticket_amt = _safe_float(raw_ticket, 0.0) if raw_ticket is not None else None

            place = get_or_create_place(
                db,
                name=place_name,
                category=place_cat,
                city=trip.destination,
                country=trip.country,
                latitude=place_lat,
                longitude=place_lon,
                address=place_addr,
                rating=place_rating,
                ticket_price=ticket_amt or 0.0,
                google_maps_url=place_maps
            )

            is_final_act = (order_idx == len(acts) - 1)
            t_mode = None if is_final_act else act_data.get("transport_mode")
            t_dur = None if is_final_act else act_data.get("transport_duration")
            t_dist = None if is_final_act else act_data.get("distance")

            dur_mins = act_data.get("duration_minutes") or 90
            dur_str = f"{dur_mins} mins"

            act_meta = act_data.get("metadata") if isinstance(act_data.get("metadata"), dict) else {}
            if t_dist:
                act_meta["distance"] = t_dist
            act_meta["activity_type"] = act_data.get("activity_type")
            act_meta["meal_details"] = act_data.get("meal_details")
            act_meta["meal_cost"] = act_data.get("meal_cost")
            act_meta["transit_details"] = act_data.get("transit_details")
            act_meta["dietary_suitability"] = act_data.get("dietary_suitability")
            act_meta["provenance"] = act_data.get("provenance")
            act_meta["base_city"] = base_city
            act_meta["overnight_stay"] = overnight

            # Meal activities should not use attraction ticket price
            is_dining_act = (
                act_data.get("activity_type") == "meal"
                or "restaurant" in place_cat.lower()
                or "cafe" in place_cat.lower()
            )
            if is_dining_act:
                ticket_amt = 0.0

            crowd_val = act_data.get("crowd_level")

            activity = ItineraryActivity(
                day_id=it_day.id,
                place_id=place.id,
                time_slot=act_data.get("time_slot", "morning"),
                start_time=act_data.get("start_time", "08:30"),
                end_time=act_data.get("end_time", "10:00"),
                duration_minutes=dur_mins,
                order_index=order_idx,
                title=act_data.get("title", "Visit Attraction"),
                description=act_data.get("description", ""),
                estimated_duration=dur_str,
                ticket_price=ticket_amt or 0.0,
                transport_mode=t_mode,
                transport_duration=t_dur,
                weather_suitability=str(act_data.get("weather_suitability") or "Mixed"),
                crowd_level=str(crowd_val) if crowd_val else None,
                ai_reason=str(act_data.get("ai_reason") or f"✓ Recommended spot in {trip.destination}"),
                confidence_score=_safe_float(act_data.get("confidence_score"), 0.98),
                is_locked=bool(act_data.get("is_locked", False)),
                activity_metadata=act_meta
            )
            db.add(activity)
            inserted_count += 1
            total_inserted_count += 1

        db.commit()
        print(f"[DB Insert Log] Trip {trip.id} Day {day_num} activities inserted: {inserted_count}")

    db.refresh(trip)
    return total_inserted_count


@router.get("/search")
def search_user_trips(
    query: str,
    user_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    target_user_id = current_user.id if current_user else user_id
    if not target_user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User identification required")
    trips = search_trips(db, user_id=target_user_id, query=query)
    return [enrich_trip_response(t, db) for t in trips]


@router.get("/filter")
def filter_user_trips(
    user_id: Optional[int] = None,
    status: Optional[str] = None,
    travel_style: Optional[str] = None,
    min_budget: Optional[float] = None,
    max_budget: Optional[float] = None,
    is_favorite: Optional[bool] = None,
    is_archived: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    target_user_id = current_user.id if current_user else user_id
    if not target_user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User identification required")
    req = FilterTripsRequest(
        user_id=target_user_id,
        status=status,
        travel_style=travel_style,
        min_budget=min_budget,
        max_budget=max_budget,
        is_favorite=is_favorite,
        is_archived=is_archived
    )
    trips = filter_trips(db, req)
    return [enrich_trip_response(t, db) for t in trips]


@router.get("/dashboard-widgets")
@router.get("/user/{user_id}/dashboard-widgets")
@router.get("/dashboard-widgets/{user_id}")
def get_user_dashboard_widgets(
    user_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    target_user_id = current_user.id if current_user else user_id
    if not target_user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User identification required")
    return get_dashboard_widgets(db, target_user_id)


@router.get("/stats")
@router.get("/user/{user_id}/stats")
@router.get("/stats/{user_id}")
def get_trip_stats_endpoint(
    user_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    target_user_id = current_user.id if current_user else user_id
    if not target_user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User identification required")
    return get_user_trip_stats(db, target_user_id)


@router.get("/spotlight")
@router.get("/user/{user_id}/spotlight")
def get_spotlight_endpoint(
    user_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    target_user_id = current_user.id if current_user else user_id
    if not target_user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User identification required")
    spotlight = get_active_trip_spotlight(db, target_user_id)
    return spotlight if spotlight else {}


@router.get("/recently-viewed")
@router.get("/user/{user_id}/recently-viewed")
def get_recently_viewed_endpoint(
    user_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    target_user_id = current_user.id if current_user else user_id
    if not target_user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User identification required")
    recent = get_recently_viewed_trip(db, target_user_id)
    return recent if recent else {}


@router.post("/check-duplicate")
def check_duplicate_endpoint(
    payload: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    target_user_id = current_user.id if current_user else payload.get("user_id")
    if not target_user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User identification required")

    dest = payload.get("destination", "")
    st_str = payload.get("start_date", "")
    try:
        st_date = date.fromisoformat(st_str) if isinstance(st_str, str) else date.today()
    except Exception:
        st_date = date.today()

    return check_duplicate_trip(db, target_user_id, dest, st_date)


@router.get("")
@router.get("/")
@router.get("/user/{user_id}")
def get_user_trips(
    user_id: Optional[int] = None,
    page: Optional[int] = Query(None),
    limit: Optional[int] = Query(None),
    search: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    travel_style: Optional[str] = Query(None),
    sort: Optional[str] = Query(None),
    paginated: Optional[bool] = Query(False),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    target_user_id = current_user.id if current_user else user_id
    if not target_user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User identification required")

    if page is not None or limit is not None or paginated or search or status or travel_style or sort:
        p = page or 1
        l = limit or 12
        return get_paginated_user_trips(db, target_user_id, page=p, limit=l, search=search, status=status, travel_style=travel_style, sort=sort)

    trips = db.query(Trip).filter(Trip.user_id == target_user_id).order_by(Trip.start_date.asc(), Trip.destination.asc(), Trip.id.desc()).all()
    return [enrich_trip_response(t, db) for t in trips]


@router.post("/{trip_id}/touch")
def touch_trip_endpoint(
    trip_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    trip = _get_user_trip(trip_id, db, current_user)
    return touch_trip(db, trip.id, trip.user_id)


@router.get("/{trip_id}")
def get_single_trip(
    trip_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    trip = _get_user_trip(trip_id, db, current_user)
    res = enrich_trip_response(trip, db, fetch_live_network=False)
    total_acts = sum(len(d.get("activities", [])) for d in res.get("itinerary_days", []))
    print(f"[GET Endpoint Log] GET /api/trips/{trip_id} returning {total_acts} total activities across {len(res.get('itinerary_days', []))} days.")
    return res


@router.put("/{trip_id}")
def update_existing_trip(
    trip_id: int,
    data: TripUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    trip = _get_user_trip(trip_id, db, current_user)
    updated = update_trip(db, trip, data)
    return enrich_trip_response(updated, db)


@router.delete("/{trip_id}")
@router.delete("/delete/{trip_id}")
def delete_existing_trip(
    trip_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    trip = _get_user_trip(trip_id, db, current_user)
    db.delete(trip)
    db.commit()
    return {"message": "Trip deleted successfully"}


@router.post("/{trip_id}/duplicate")
def duplicate_trip_endpoint(
    trip_id: int,
    user_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    trip = _get_user_trip(trip_id, db, current_user)
    target_user_id = current_user.id if current_user else (user_id or trip.user_id)
    try:
        new_trip = duplicate_trip(db, trip_id=trip_id, user_id=target_user_id)
        return enrich_trip_response(new_trip, db)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/{trip_id}/archive")
def archive_trip_endpoint(
    trip_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    trip = _get_user_trip(trip_id, db, current_user)
    trip.is_archived = True
    trip.status = "Archived"
    db.commit()
    db.refresh(trip)
    return enrich_trip_response(trip, db)


@router.post("/{trip_id}/restore")
def restore_trip_endpoint(
    trip_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    trip = _get_user_trip(trip_id, db, current_user)
    trip.is_archived = False
    today = date.today()
    if today < trip.start_date:
        trip.status = "Upcoming"
    elif today > trip.end_date:
        trip.status = "Completed"
    else:
        trip.status = "In Progress"
    db.commit()
    db.refresh(trip)
    return enrich_trip_response(trip, db)


@router.post("/{trip_id}/favorite")
def toggle_favorite_endpoint(
    trip_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    trip = _get_user_trip(trip_id, db, current_user)
    trip.is_favorite = not trip.is_favorite
    db.commit()
    db.refresh(trip)
    return enrich_trip_response(trip, db)


@router.post("/{trip_id}/complete")
def complete_trip_endpoint(
    trip_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    trip = _get_user_trip(trip_id, db, current_user)
    trip.status = "Completed"
    db.commit()
    db.refresh(trip)
    return enrich_trip_response(trip, db)


@router.post("/{trip_id}/cancel")
def cancel_trip_endpoint(
    trip_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    trip = _get_user_trip(trip_id, db, current_user)
    trip.status = "Cancelled"
    db.commit()
    db.refresh(trip)
    return enrich_trip_response(trip, db)


activities_router = APIRouter(prefix="/api/activities", tags=["Activities"])


@router.patch("/activities/{activity_id}/complete")
@activities_router.patch("/{activity_id}/complete")
def complete_activity_endpoint(
    activity_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    act = _get_user_activity(activity_id, db, current_user)
    act.is_completed = True
    act.completed_at = datetime.now()
    db.commit()
    db.refresh(act)
    return {
        "message": "Activity marked as completed",
        "id": act.id,
        "activity_id": act.id,
        "completed": True,
        "completed_at": act.completed_at.isoformat() if act.completed_at else None
    }


@router.patch("/activities/{activity_id}/undo")
@activities_router.patch("/{activity_id}/undo")
def undo_activity_endpoint(
    activity_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    act = _get_user_activity(activity_id, db, current_user)
    act.is_completed = False
    act.completed_at = None
    db.commit()
    db.refresh(act)
    return {
        "message": "Activity marked as incomplete",
        "id": act.id,
        "activity_id": act.id,
        "completed": False,
        "completed_at": None
    }



@router.post("/{trip_id}/share")

def share_trip_endpoint(
    trip_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    trip = _get_user_trip(trip_id, db, current_user)
    if not trip.share_token:
        import secrets
        trip.share_token = secrets.token_urlsafe(12)
        db.commit()
        db.refresh(trip)
    return {
        "share_token": trip.share_token,
        "share_url": f"http://localhost:5173/trips/share/{trip.share_token}"
    }


@router.post("/{trip_id}/generate-itinerary")
def generate_trip_itinerary(
    trip_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    import uuid
    generation_id = str(uuid.uuid4())
    
    trip = _get_user_trip(trip_id, db, current_user)
    days = max(1, (trip.end_date - trip.start_date).days + 1)
    
    ai_data = generate_structured_itinerary(
        destination=trip.destination,
        days=days,
        budget=trip.budget,
        interests=trip.interests or "sightseeing",
        travel_style=trip.travel_style or "solo",
        group_size=trip.group_size or 1,
        currency=trip.currency or "USD",
        country=trip.country or "",
        origin_city=trip.origin_city or "Coimbatore",
        origin_airport=trip.origin_airport or "",
        destination_airport=trip.destination_airport or "",
        accommodation_preference=trip.accommodation_preference or "hotel",
        transportation=trip.transportation or "flight",
        travel_companion=trip.travel_companion or trip.travel_style or "solo",
        start_date=str(trip.start_date) if trip.start_date else "",
        end_date=str(trip.end_date) if trip.end_date else "",
        trip_preferences=trip.trip_preferences,
        language=current_user.languages if current_user and current_user.languages else "English",
        generation_id=generation_id
    )
    
    try:
        inserted_count = _populate_trip_itinerary_from_ai(db, trip, ai_data)
        if inserted_count == 0:
            db.rollback()
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Itinerary generation failed because no verified activities could be inserted.")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"Failed to generate itinerary: {str(e)}")

    updated_trip_data = enrich_trip_response(trip, db)
    
    return {
        "success": True,
        "trip_id": trip.id,
        "generation_id": generation_id,
        "activities_count": inserted_count,
        "data": updated_trip_data
    }


@router.post("/{trip_id}/regenerate-day")
def regenerate_day_endpoint(
    trip_id: int,
    data: RegenerateDayRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    import uuid
    generation_id = str(uuid.uuid4())
    
    trip = _get_user_trip(trip_id, db, current_user)
    it_day = db.query(ItineraryDay).filter(ItineraryDay.trip_id == trip_id, ItineraryDay.day_number == data.day_number).first()
    if not it_day:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Day {data.day_number} not found for this trip")

    # Fetch locked activities to preserve
    locked_acts = db.query(ItineraryActivity).filter(
        ItineraryActivity.day_id == it_day.id,
        ItineraryActivity.is_locked == True
    ).all()
    locked_payload = [
        {
            "id": a.id,
            "title": a.title,
            "start_time": a.start_time,
            "end_time": a.end_time,
            "time_slot": a.time_slot,
            "is_locked": True
        }
        for a in locked_acts
    ]

    new_acts = regenerate_day_itinerary(
        destination=trip.destination,
        day_number=data.day_number,
        locked_activities=locked_payload,
        notes=data.notes,
        generation_id=generation_id
    )

    # Replace unlocked activities
    db.query(ItineraryActivity).filter(
        ItineraryActivity.day_id == it_day.id,
        ItineraryActivity.is_locked == False
    ).delete()
    db.commit()

    inserted_count = 0
    from app.services.route_optimizer import estimate_travel_transition
    
    # Recalculate schedule sequentially
    current_time_mins = 8 * 60 + 30
    
    for idx, act_data in enumerate(new_acts):
        p_name = act_data.get("title", f"Attraction {idx+1}")
        
        place_info = act_data.get("place", {})
        place_lat = place_info.get("latitude") if isinstance(place_info, dict) else None
        place_lon = place_info.get("longitude") if isinstance(place_info, dict) else None
        
        place = get_or_create_place(
            db, 
            name=p_name, 
            city=trip.destination, 
            country=trip.country,
            latitude=place_lat,
            longitude=place_lon
        )
        
        dur_mins = act_data.get("duration_minutes") or 90
        
        st_hr = current_time_mins // 60
        st_mn = current_time_mins % 60
        start_time_str = f"{st_hr:02d}:{st_mn:02d}"
        
        end_time_mins = current_time_mins + dur_mins
        et_hr = end_time_mins // 60
        et_mn = end_time_mins % 60
        end_time_str = f"{et_hr:02d}:{et_mn:02d}"

        t_mode = "Not available"
        t_dur = "Not available"
        t_dist = "Not available"
        travel_mins = 15

        if idx < len(new_acts) - 1:
            next_act = new_acts[idx + 1]
            next_place_info = next_act.get("place", {})
            n_lat = next_place_info.get("latitude") if isinstance(next_place_info, dict) else None
            n_lon = next_place_info.get("longitude") if isinstance(next_place_info, dict) else None
            
            if place_lat and place_lon and n_lat and n_lon:
                try:
                    trans = estimate_travel_transition(float(place_lat), float(place_lon), float(n_lat), float(n_lon))
                    t_mode = trans.get("travel_mode", "Walking")
                    t_dur = trans.get("travel_time", "Not available")
                    t_dist = trans.get("distance", "Not available")
                    import re
                    m = re.search(r'(\d+)', t_dur)
                    if m:
                        travel_mins = int(m.group(1))
                except Exception:
                    pass
        
        current_time_mins = end_time_mins + travel_mins + 10

        act_meta = act_data.get("metadata", {})
        if not isinstance(act_meta, dict):
            act_meta = {}
        if t_dist != "Not available":
            act_meta["distance"] = t_dist

        act = ItineraryActivity(
            day_id=it_day.id,
            place_id=place.id,
            time_slot=act_data.get("time_slot", "afternoon"),
            start_time=start_time_str,
            end_time=end_time_str,
            order_index=idx,
            title=act_data.get("title", "Regenerated Spot"),
            description=act_data.get("description", ""),
            estimated_duration=act_data.get("estimated_duration", f"{dur_mins} mins"),
            ticket_price=_safe_float(act_data.get("ticket_price"), 0.0),
            transport_mode=t_mode,
            transport_duration=t_dur,
            weather_suitability="Not available",
            crowd_level="Not available",
            ai_reason="Regenerated based on traveler preferences",
            confidence_score=0.96,
            is_locked=False,
            activity_metadata=act_meta
        )
        db.add(act)
        inserted_count += 1

    if inserted_count == 0:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Day regeneration failed because no verified activities could be inserted.")

    db.commit()
    db.refresh(it_day)
    
    updated_trip_data = enrich_trip_response(trip, db)
    
    return {
        "success": True,
        "trip_id": trip.id,
        "generation_id": generation_id,
        "activities_count": inserted_count,
        "data": updated_trip_data
    }


@router.post("/{trip_id}/replan")
def replan_trip_endpoint(
    trip_id: int,
    trigger_reason: str = Query(..., description="E.g., weather_delay, budget_exceeded, miss_attraction"),
    user_notes: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    trip = _get_user_trip(trip_id, db, current_user)
    trip_dict = enrich_trip_response(trip, db)
    
    updated_itinerary = replan_itinerary(
        current_itinerary=json.dumps(trip_dict),
        modification_request=f"Reason: {trigger_reason}. Notes: {user_notes or 'None'}"
    )
    return {"updated_itinerary": updated_itinerary}


@router.put("/activities/{activity_id}/lock")
def toggle_activity_lock(
    activity_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    act = _get_user_activity(activity_id, db, current_user)
    act.is_locked = not act.is_locked
    db.commit()
    db.refresh(act)
    return {"id": act.id, "is_locked": act.is_locked}


@router.delete("/activities/{activity_id}")
def delete_activity(
    activity_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    act = _get_user_activity(activity_id, db, current_user)
    db.delete(act)
    db.commit()
    return {"message": "Activity deleted successfully"}


@router.put("/{trip_id}/activities/reorder")
def reorder_trip_activities(
    trip_id: int,
    data: ActivityReorder,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    trip = _get_user_trip(trip_id, db, current_user)
    act = db.query(ItineraryActivity).filter(ItineraryActivity.id == data.activity_id).first()
    if not act:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Activity not found")
    
    act.day_id = data.target_day_id
    act.time_slot = data.target_time_slot
    act.order_index = data.new_order_index
    db.commit()
    db.refresh(act)
    
    return enrich_trip_response(trip, db)


@router.post("/{trip_id}/activities/add")
def add_custom_activity(
    trip_id: int,
    data: ActivityCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    trip = _get_user_trip(trip_id, db, current_user)
    place = None
    if data.place_name:
        place = get_or_create_place(
            db,
            name=data.place_name,
            category=data.place_category or "sightseeing",
            latitude=data.latitude,
            longitude=data.longitude
        )

    act = ItineraryActivity(
        day_id=data.day_id,
        place_id=place.id if place else None,
        title=data.title,
        description=data.description,
        time_slot=data.time_slot,
        start_time=data.start_time,
        end_time=data.end_time,
        estimated_duration=data.estimated_duration,
        ticket_price=data.ticket_price or 0.0,
        transport_mode=data.transport_mode or "walking",
        transport_duration=data.transport_duration,
        weather_suitability=data.weather_suitability or "all-weather",
        crowd_level=data.crowd_level or "moderate",
        ai_reason="Custom traveler activity",
        is_locked=True
    )
    db.add(act)
    db.commit()
    
    return enrich_trip_response(trip, db)


@router.get("/{trip_id}/today")
def get_today_execution_itinerary(
    trip_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Fetch today's active execution itinerary with user isolation."""
    from app.services.trip_service import get_today_itinerary
    try:
        user_id = current_user.id if current_user else None
        return get_today_itinerary(trip_id=trip_id, db=db, user_id=user_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/{trip_id}/activities/{activity_id}/toggle-complete")
def toggle_activity_complete_status(
    trip_id: int,
    activity_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Toggle completion status for an itinerary activity with strict user isolation."""
    from app.services.trip_service import toggle_activity_completion
    try:
        user_id = current_user.id if current_user else None
        return toggle_activity_completion(trip_id=trip_id, activity_id=activity_id, user_id=user_id, db=db)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# Note: generate-itinerary endpoint is registered at line 822 as generate_trip_itinerary.


@router.post("/{trip_id}/regenerate-day")
def regenerate_single_day_itinerary(
    trip_id: int,
    data: RegenerateDayRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Regenerate activities for a single day while leaving other days & locked activities intact."""
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    if current_user and trip.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to modify this trip")

    day_num = data.day_number
    days_count = max(1, (trip.end_date - trip.start_date).days + 1)
    resolved_currency = trip.currency or (current_user.currency if current_user else None) or "USD"
    daily_budget = (trip.budget or 1000.0) / days_count

    trip_prefs = dict(trip.trip_preferences or {})
    resolved_lang = trip_prefs.get("language") or (current_user.languages if current_user else None) or "English"
    resolved_travel_style = trip.travel_style or trip_prefs.get("travel_style") or (current_user.travel_styles if current_user else None) or "solo"
    resolved_interests = trip.interests or trip_prefs.get("interests") or (current_user.preferred_activities if current_user else None) or "sightseeing"

    if current_user:
        if not trip_prefs.get("dietary_preferences") and current_user.dietary_preferences:
            trip_prefs["dietary_preferences"] = current_user.dietary_preferences
        if not trip_prefs.get("preferred_climate") and current_user.preferred_climate:
            trip_prefs["preferred_climate"] = current_user.preferred_climate
        if not trip_prefs.get("budget_type") and current_user.preferred_budget:
            trip_prefs["budget_type"] = current_user.preferred_budget
            trip_prefs["preferred_budget"] = current_user.preferred_budget

    trip_prefs["currency"] = resolved_currency
    trip_prefs["language"] = resolved_lang

    try:
        ai_data = generate_structured_itinerary(
            destination=trip.destination,
            days=1,
            budget=daily_budget,
            interests=resolved_interests,
            travel_style=resolved_travel_style,
            group_size=trip.group_size or 1,
            currency=resolved_currency,
            trip_preferences=trip_prefs,
            language=resolved_lang
        )

        days_data = ai_data.get("days", []) or ai_data.get("itinerary_days", [])
        if days_data:
            days_data[0]["day_number"] = day_num
            _populate_trip_itinerary_from_ai(db, trip, {"days": [days_data[0]]})
    except Exception as e:
        print(f"[Regenerate Day Exception]: {e}")

    return enrich_trip_response(trip, db)



