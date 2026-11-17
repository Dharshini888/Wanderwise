"""
test_audit_security_and_code_quality.py — Verification of IDOR Authorization,
Schema Validation, and General-Purpose Travel Companion Branding.
"""
import pytest
from datetime import date, timedelta
from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.database.connection import Base
from app.models.user import User
from app.models.trip import Trip
from app.schemas.trip_schemas import TripUpdate
from app.routes.trips import _get_user_trip, get_shared_trip_endpoint
from app.services.location.location_normalizer import resolve_destination_info
from app.services.budget_allocation_service import BudgetAllocationService, COUNTRY_VISA_RULES
from app.services.trip_execution.emergency_service import get_offline_emergency_data


@pytest.fixture(scope="module")
def db_engine():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session(db_engine):
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def test_users(db_session: Session):
    import uuid
    uid = uuid.uuid4().hex[:6]
    u1 = User(email=f"traveler1_{uid}@wanderwise.com", name="Alex Traveler", password="hash1", currency="USD")
    u2 = User(email=f"traveler2_{uid}@wanderwise.com", name="Sam Wanderer", password="hash2", currency="EUR")
    db_session.add_all([u1, u2])
    db_session.commit()
    db_session.refresh(u1)
    db_session.refresh(u2)
    return u1, u2


def test_idor_protection_on_trip_access(db_session: Session, test_users):
    """Ensure user 2 cannot modify or delete user 1's trip (enforce_owner=True raises 403)."""
    u1, u2 = test_users
    trip = Trip(
        user_id=u1.id,
        destination="Kyoto",
        country="Japan",
        start_date=date(2027, 4, 1),
        end_date=date(2027, 4, 7),
        budget=2000.0,
        currency="USD"
    )
    db_session.add(trip)
    db_session.commit()
    db_session.refresh(trip)

    # User 1 (owner) can access with enforce_owner=True
    owner_trip = _get_user_trip(trip.id, db_session, current_user=u1, enforce_owner=True)
    assert owner_trip.id == trip.id

    # User 2 cannot access with enforce_owner=True (raises 403 Forbidden)
    with pytest.raises(HTTPException) as exc_info:
        _get_user_trip(trip.id, db_session, current_user=u2, enforce_owner=True)
    assert exc_info.value.status_code == 403
    assert "Access forbidden" in exc_info.value.detail


def test_trip_update_date_validation():
    """Verify that end_date < start_date raises ValidationError in TripUpdate."""
    with pytest.raises(ValidationError) as exc_info:
        TripUpdate(
            start_date=date(2027, 5, 10),
            end_date=date(2027, 5, 5)
        )
    assert "Return date cannot be earlier than departure date" in str(exc_info.value)


def test_trip_update_negative_budget_validation():
    """Verify that negative budget raises ValidationError in TripUpdate."""
    with pytest.raises(ValidationError) as exc_info:
        TripUpdate(
            budget=-500.0
        )
    assert "Budget cannot be negative" in str(exc_info.value)


def test_no_conference_branding_in_codebase():
    """Verify that IEEE NMIC-2026 conference-specific branding is completely absent from user-facing templates."""
    import os
    dashboard_path = os.path.join(os.path.dirname(__file__), "../../frontend/src/pages/Dashboard.jsx")
    if os.path.exists(dashboard_path):
        with open(dashboard_path, "r", encoding="utf-8") as f:
            content = f.read()
        assert "IEEE NMIC-2026 Ready" not in content
        assert "IEEE NMIC-2026" not in content
        assert "deterministic constraint satisfaction" not in content


def test_global_origin_geocoding_and_flight_distance():
    """Verify that global non-Indian origins (e.g. London, UK) compute accurate flight distances to destinations."""
    info = resolve_destination_info(destination="Tokyo, Japan", origin="London, UK")
    assert info["origin_city"] == "London, UK"
    assert info["origin_country_code"] == "GB"
    # Real flight distance from London (LHR) to Tokyo (HND/NRT) is approx 9,500 - 9,600 km
    flight_km = info.get("flight_distance_km", 0)
    assert 9000 <= flight_km <= 10500, f"Expected realistic London-Tokyo distance ~9500km, got {flight_km}"
    assert info["is_long_haul"] is True


def test_ambiguous_city_resolution():
    """Verify that same-name cities across different countries are disambiguated by user country context."""
    info_es = resolve_destination_info("Santiago, Spain")
    assert info_es["country"] == "Spain"
    assert info_es["country_code"] == "ES"
    assert info_es["currency"] == "EUR"

    info_cl = resolve_destination_info("Santiago, Chile")
    assert info_cl["country"] == "Chile"
    assert info_cl["country_code"] == "CL"
    assert info_cl["currency"] == "CLP"


def test_country_visa_rules_destination_independence():
    """Verify that visa fee logic uses country codes and works for any city without city-specific hardcoding."""
    assert "TR" in COUNTRY_VISA_RULES
    assert "ID" in COUNTRY_VISA_RULES

    # Antalya in Turkey (not named 'istanbul')
    b_tr = BudgetAllocationService.calculate_plan(
        total_budget=300000.0,
        currency="INR",
        tier="mid_range",
        destination="Antalya, Turkey",
        origin_city="Coimbatore",
        travellers=2
    )
    fees_tr = b_tr["fees_breakdown"]
    assert "Turkey entry" in fees_tr["notes"]

    # Ubud in Indonesia (not named 'bali')
    b_id = BudgetAllocationService.calculate_plan(
        total_budget=200000.0,
        currency="INR",
        tier="mid_range",
        destination="Ubud, Indonesia",
        origin_city="Coimbatore",
        travellers=2
    )
    fees_id = b_id["fees_breakdown"]
    assert "Indonesia entry" in fees_id["notes"]


def test_shared_trip_public_endpoint_access(db_session: Session, test_users):
    """Verify that public shared trips can be retrieved via token without user auth, and 404 on invalid token."""
    u1, _ = test_users
    trip = Trip(
        user_id=u1.id,
        destination="Porto",
        country="Portugal",
        start_date=date(2027, 6, 1),
        end_date=date(2027, 6, 8),
        budget=2500.0,
        currency="EUR",
        share_token="porto_shared_token_xyz"
    )
    db_session.add(trip)
    db_session.commit()
    db_session.refresh(trip)

    # Valid share token retrieval
    shared_data = get_shared_trip_endpoint("porto_shared_token_xyz", db_session)
    assert shared_data["id"] == trip.id
    assert shared_data["destination"] == "Porto"
    assert shared_data["country"] == "Portugal"
    assert shared_data["share_token"] == "porto_shared_token_xyz"

    # Invalid share token raises 404
    with pytest.raises(HTTPException) as exc_info:
        get_shared_trip_endpoint("invalid_token_999", db_session)
    assert exc_info.value.status_code == 404


def test_destination_aware_offline_emergency_data():
    """Verify offline emergency contact resolver returns country-specific hotlines globally."""
    tokyo_emerg = get_offline_emergency_data("Tokyo, Japan")
    assert tokyo_emerg["country"] == "Japan"
    assert "110" in tokyo_emerg["police"]
    assert "119" in tokyo_emerg["medical"]

    london_emerg = get_offline_emergency_data("London, UK")
    assert "999" in london_emerg["police"]
    assert "999" in london_emerg["medical"]

    sg_emerg = get_offline_emergency_data("Singapore")
    assert "999" in sg_emerg["police"]
    assert "995" in sg_emerg["medical"]

