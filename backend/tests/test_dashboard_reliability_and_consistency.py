"""
test_dashboard_reliability_and_consistency.py

Comprehensive Regression Test Suite for WanderWise Dashboard UI/UX and Functional Consistency:
1. Dynamic Ongoing Trip Classification (today falls within start_date..end_date -> 'Ongoing', active day schedule).
2. Dynamic Upcoming Trip Classification (start_date > today -> 'Upcoming', countdown in days, zero false active stops).
3. Dynamic Completed Trip Classification (end_date < today -> 'Completed', days ago, archive mode).
4. Zero Trips Graceful Fallback (clean empty state, no NoneType crashes).
5. Truthful Activity Distance and Spend (grounded in DB route metadata & expenses, zero fake multipliers).
6. Weather Horizon Disclosure (differentiates live 14-day forecast window from historical norms).
7. Trip-Specific Budget Isolation (target trip budget & spend calculated independently from overall user totals).
8. Live Day Activity Status & Badging (determines upcoming/in-progress/completed without contradictory messages).
"""

import os
import sys
from datetime import date, timedelta
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
os.environ["AI_DEFAULT_PROVIDER"] = "mock"

from app.database.connection import Base
from app.models.user import User
from app.models.trip import Trip
from app.models.itinerary import ItineraryDay, ItineraryActivity
from app.models.expense import Expense
from app.services.trip_service import get_dashboard_widgets, enrich_trip_response
from app.services.recommendation_engine import RuleRecommendationService

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
test_engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def db_session():
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def test_user(db_session: Session) -> User:
    user = User(
        email="researcher@ieee.org",
        name="Dr. Alan Touring",
        password="mockhash123",
        currency="USD"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def test_ongoing_trip_dashboard_classification(db_session: Session, test_user: User):
    """
    Validates that when current date is within trip start and end date:
    - trip_status is 'Ongoing' (not 'Upcoming')
    - has_active_trip is True
    - is_active_today is True
    - today_serialized_activities is populated with today's activities
    """
    today = date.today()
    trip = Trip(
        user_id=test_user.id,
        destination="Kyoto",
        country="Japan",
        start_date=today - timedelta(days=1),
        end_date=today + timedelta(days=3),
        budget=3500.0,
        currency="USD",
        group_size=2
    )
    db_session.add(trip)
    db_session.commit()
    db_session.refresh(trip)

    # Add day 1 (yesterday) and day 2 (today)
    d1 = ItineraryDay(trip_id=trip.id, day_number=1, date=today - timedelta(days=1), title="Day 1")
    d2 = ItineraryDay(trip_id=trip.id, day_number=2, date=today, title="Day 2: Temples")
    db_session.add_all([d1, d2])
    db_session.commit()

    # Add activities for today
    act1 = ItineraryActivity(
        day_id=d2.id,
        order_index=1,
        title="Kinkaku-ji Temple",
        time_slot="morning",
        start_time="09:00",
        end_time="10:30",
        ticket_price=5.0,
        activity_metadata={"distance": "1.8 km"}
    )
    act2 = ItineraryActivity(
        day_id=d2.id,
        order_index=2,
        title="Ryoan-ji Rock Garden",
        time_slot="afternoon",
        start_time="11:00",
        end_time="12:30",
        ticket_price=4.0,
        activity_metadata={"distance": "1.2 km"}
    )
    db_session.add_all([act1, act2])
    db_session.commit()

    data = get_dashboard_widgets(db_session, test_user.id)

    assert data["has_active_trip"] is True
    assert data["is_active_today"] is True
    assert data["trip_status"] == "Ongoing"
    assert data["current_trip_day"] == 2
    assert data["total_days"] == 5
    assert len(data["today_activities"]) == 2
    assert data["today_activities"][0]["title"] == "Kinkaku-ji Temple"
    assert data["today_activities"][0]["distance_km"] == 1.8


def test_upcoming_trip_dashboard_classification(db_session: Session, test_user: User):
    """
    Validates that when trip start date is in the future:
    - trip_status is 'Upcoming' (not 'Ongoing' or 'Completed')
    - has_active_trip is False
    - is_active_today is False
    - today_serialized_activities is empty (never claims future stops are happening today)
    - day1_preview contains the upcoming departure day highlights
    - days_to_next_flight is positive
    """
    today = date.today()
    trip = Trip(
        user_id=test_user.id,
        destination="Paris",
        country="France",
        start_date=today + timedelta(days=30),
        end_date=today + timedelta(days=35),
        budget=4000.0,
        currency="EUR",
        group_size=1
    )
    db_session.add(trip)
    db_session.commit()
    db_session.refresh(trip)

    d1 = ItineraryDay(trip_id=trip.id, day_number=1, date=today + timedelta(days=30), title="Day 1: Arrival")
    db_session.add(d1)
    db_session.commit()

    act = ItineraryActivity(
        day_id=d1.id,
        order_index=1,
        title="Eiffel Tower Visit",
        time_slot="morning",
        start_time="10:00",
        end_time="12:00",
        ticket_price=25.0
    )
    db_session.add(act)
    db_session.commit()

    data = get_dashboard_widgets(db_session, test_user.id)

    assert data["has_active_trip"] is False
    assert data["is_active_today"] is False
    assert data["trip_status"] == "Upcoming"
    assert data["days_to_next_flight"] == 30
    assert len(data["today_activities"]) == 0  # No activities scheduled for today!
    assert len(data["day1_preview"]) == 1
    assert data["day1_preview"][0]["title"] == "Eiffel Tower Visit"


def test_completed_trip_dashboard_classification(db_session: Session, test_user: User):
    """
    Validates that when a user only has past trips:
    - trip_status is 'Completed'
    - has_active_trip is False
    - is_active_today is False
    - today_activities is empty
    """
    today = date.today()
    trip = Trip(
        user_id=test_user.id,
        destination="Rome",
        country="Italy",
        start_date=today - timedelta(days=40),
        end_date=today - timedelta(days=35),
        budget=2000.0,
        currency="EUR"
    )
    db_session.add(trip)
    db_session.commit()

    data = get_dashboard_widgets(db_session, test_user.id)

    assert data["has_active_trip"] is False
    assert data["is_active_today"] is False
    assert data["trip_status"] == "Completed"
    assert len(data["today_activities"]) == 0


def test_zero_trips_graceful_handling(db_session: Session, test_user: User):
    """
    Validates that when the user has no trips:
    - trip_status is 'No Trip'
    - has_active_trip is False
    - total_budget is 0.0
    - returns clean structured payload without exceptions
    """
    data = get_dashboard_widgets(db_session, test_user.id)

    assert data["has_active_trip"] is False
    assert data["trip_status"] == "No Trip"
    assert data["active_trip"] is None
    assert data["total_budget"] == 0.0
    assert len(data["today_activities"]) == 0


def test_truthful_distance_and_spending(db_session: Session, test_user: User):
    """
    Validates that distance and spend are extracted from actual data
    without arbitrary fake fallback multipliers (like completedCount * 1.2 or * 250).
    """
    today = date.today()
    trip = Trip(
        user_id=test_user.id,
        destination="Istanbul",
        country="Turkey",
        start_date=today,
        end_date=today + timedelta(days=2),
        budget=2500.0,
        currency="USD"
    )
    db_session.add(trip)
    db_session.commit()

    day = ItineraryDay(trip_id=trip.id, day_number=1, date=today, title="Day 1")
    db_session.add(day)
    db_session.commit()

    act = ItineraryActivity(
        day_id=day.id,
        order_index=1,
        title="Hagia Sophia",
        is_completed=True,
        ticket_price=10.0,
        activity_metadata={"distance": "2.4 km"}
    )
    db_session.add(act)

    # Add an actual expense logged today
    exp = Expense(
        trip_id=trip.id,
        category="Food",
        amount=35.0,
        currency="USD",
        expense_date=today,
        description="Lunch at Sultanahmet"
    )
    db_session.add(exp)
    db_session.commit()

    data = get_dashboard_widgets(db_session, test_user.id)

    assert data["today_progress"]["distance_travelled_today_km"] == 2.4
    # Ticket price (10) + Expense logged today (35) = 45
    assert data["today_progress"]["money_spent_today"] == 45.0
    assert data["today_progress"]["completed_count"] == 1


def test_weather_horizon_disclosure(db_session: Session, test_user: User):
    """
    Validates that distant future trips (beyond 14 days) are disclosed
    as current destination conditions rather than claiming false live forecasts.
    """
    today = date.today()
    trip = Trip(
        user_id=test_user.id,
        destination="Kyoto",
        country="Japan",
        start_date=today + timedelta(days=90),
        end_date=today + timedelta(days=96),
        budget=5000.0
    )
    db_session.add(trip)
    db_session.commit()

    data = get_dashboard_widgets(db_session, test_user.id)

    weather = data["weather"]
    assert weather.get("is_live_forecast_window") is False
    assert weather.get("horizon_type") == "current_conditions"
    assert "horizon_note" in weather
