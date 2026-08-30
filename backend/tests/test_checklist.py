import os
import sys
import pytest
from datetime import datetime, timezone, timedelta

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import httpx
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database.connection import Base, get_db
from app.models.user import User
from app.models.trip import Trip
from app.models.document import Document
from app.models.packing import PackingList
from app.models.budget import Budget
from app.models.trip_booking import TripBooking
from app.models.itinerary import ItineraryDay
from app.models.checklist import ChecklistItem
from app.services.auth_service import hash_password, create_access_token

# Test DB Setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_checklist.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture
def anyio_backend():
    return 'asyncio'


@pytest.fixture(autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    # Clean up tables
    db.query(ChecklistItem).delete()
    db.query(Document).delete()
    db.query(PackingList).delete()
    db.query(Budget).delete()
    db.query(TripBooking).delete()
    db.query(ItineraryDay).delete()
    db.query(Trip).delete()
    db.query(User).delete()
    db.commit()

    # Create User 1
    u1 = User(
        name="Checklist User 1",
        email="check1@example.com",
        password=hash_password("password123"),
        is_active=True,
    )
    # Create User 2
    u2 = User(
        name="Checklist User 2",
        email="check2@example.com",
        password=hash_password("password123"),
        is_active=True,
    )
    db.add(u1)
    db.add(u2)
    db.commit()
    db.refresh(u1)
    db.refresh(u2)

    # Create Trip for User 1
    now_dt = datetime.now(timezone.utc)
    trip1 = Trip(
        user_id=u1.id,
        title="Paris Getaway",
        destination="Paris, France",
        budget=2000.0,
        start_date=(now_dt + timedelta(days=15)).date(),
        end_date=(now_dt + timedelta(days=22)).date(),
    )
    # Create Trip for User 2
    trip2 = Trip(
        user_id=u2.id,
        title="London Calling",
        destination="London, UK",
        budget=1500.0,
        start_date=(now_dt + timedelta(days=30)).date(),
        end_date=(now_dt + timedelta(days=35)).date(),
    )
    db.add(trip1)
    db.add(trip2)
    db.commit()

    db.close()
    yield
    Base.metadata.drop_all(bind=engine)
    if os.path.exists("./test_checklist.db"):
        try:
            os.remove("./test_checklist.db")
        except Exception:
            pass


def get_token(email: str = "check1@example.com") -> str:
    db = TestingSessionLocal()
    user = db.query(User).filter(User.email == email).first()
    uid = user.id if user else 1
    db.close()
    return create_access_token({"sub": str(uid), "email": email, "role": "USER"})


def get_async_client():
    return httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://testserver")


# ── TEST SUITE ─────────────────────────────────────────────────────────────

@pytest.mark.anyio
async def test_get_checklist_auto_generates():
    """Requirement 1 & 5: GET checklist for a trip auto-generates items and returns summary"""
    token = get_token("check1@example.com")
    async with get_async_client() as client:
        res = await client.get("/api/checklist/1", headers={"Authorization": f"Bearer {token}"})
        assert res.status_code == 200
        data = res.json()
        assert data["trip_id"] == 1
        assert "summary" in data
        assert "items" in data
        assert len(data["items"]) > 0


@pytest.mark.anyio
async def test_create_custom_item():
    """Requirement 2: Create custom checklist item"""
    token = get_token("check1@example.com")
    async with get_async_client() as client:
        res = await client.post(
            "/api/checklist/1",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "title": "Buy adapter plug",
                "description": "European type C plug",
                "priority": "HIGH",
                "category": "CUSTOM"
            }
        )
        assert res.status_code == 201
        data = res.json()
        assert data["title"] == "Buy adapter plug"
        assert data["source"] == "USER"
        assert data["is_auto_generated"] is False


@pytest.mark.anyio
async def test_update_item():
    """Requirement 3: Update item title and complete status"""
    token = get_token("check1@example.com")
    async with get_async_client() as client:
        # Get items
        get_res = await client.get("/api/checklist/1", headers={"Authorization": f"Bearer {token}"})
        item_id = get_res.json()["items"][0]["id"]

        # Update status to COMPLETED
        update_res = await client.patch(
            f"/api/checklist/{item_id}",
            headers={"Authorization": f"Bearer {token}"},
            json={"status": "COMPLETED"}
        )
        assert update_res.status_code == 200
        assert update_res.json()["status"] == "COMPLETED"
        assert update_res.json()["completed_at"] is not None


@pytest.mark.anyio
async def test_delete_item():
    """Requirement 4: Delete checklist item"""
    token = get_token("check1@example.com")
    async with get_async_client() as client:
        # Pre-populate initial items
        await client.get("/api/checklist/1", headers={"Authorization": f"Bearer {token}"})

        # Create custom item
        create_res = await client.post(
            "/api/checklist/1",
            headers={"Authorization": f"Bearer {token}"},
            json={"title": "Temporary Task"}
        )
        item_id = create_res.json()["id"]

        # Delete item
        del_res = await client.delete(f"/api/checklist/{item_id}", headers={"Authorization": f"Bearer {token}"})
        assert del_res.status_code == 200

        # Verify gone
        list_res = await client.get("/api/checklist/1", headers={"Authorization": f"Bearer {token}"})
        item_ids = [i["id"] for i in list_res.json()["items"]]
        assert item_id not in item_ids


@pytest.mark.anyio
async def test_duplicate_generation_prevention():
    """Requirement 6: Repeated POST generate does not duplicate items"""
    token = get_token("check1@example.com")
    async with get_async_client() as client:
        res1 = await client.post("/api/checklist/1/generate", headers={"Authorization": f"Bearer {token}"})
        count1 = len(res1.json()["items"])

        res2 = await client.post("/api/checklist/1/generate", headers={"Authorization": f"Bearer {token}"})
        count2 = len(res2.json()["items"])

        assert count1 == count2


@pytest.mark.anyio
async def test_user_ownership_protection():
    """Requirement 7: User 2 cannot access or modify User 1's checklist"""
    token2 = get_token("check2@example.com")
    async with get_async_client() as client:
        # User 2 attempts to get User 1's trip checklist (trip_id=1)
        res = await client.get("/api/checklist/1", headers={"Authorization": f"Bearer {token2}"})
        assert res.status_code == 404


@pytest.mark.anyio
async def test_passport_rules():
    """Requirements 8-11: Passport missing, expired, expiring soon, valid"""
    token = get_token("check1@example.com")
    db = TestingSessionLocal()
    u1 = db.query(User).filter(User.email == "check1@example.com").first()
    uid = u1.id
    now = datetime.now(timezone.utc)

    # 1. Passport missing
    async with get_async_client() as client:
        gen1 = await client.post("/api/checklist/1/generate", headers={"Authorization": f"Bearer {token}"})
        titles = [i["title"] for i in gen1.json()["items"]]
        assert "Upload your passport" in titles

    # 2. Passport expired
    doc_expired = Document(
        user_id=uid,
        name="Old Passport",
        category="Passport",
        document_type="Passport",
        expiry_date=now - timedelta(days=10)
    )
    db.add(doc_expired)
    db.commit()

    async with get_async_client() as client:
        gen2 = await client.post("/api/checklist/1/generate", headers={"Authorization": f"Bearer {token}"})
        titles = [i["title"] for i in gen2.json()["items"]]
        assert "Passport has expired — renew before travel" in titles

    # 3. Passport expiring soon
    doc_expired.expiry_date = now + timedelta(days=10)
    db.commit()

    async with get_async_client() as client:
        gen3 = await client.post("/api/checklist/1/generate", headers={"Authorization": f"Bearer {token}"})
        titles = [i["title"] for i in gen3.json()["items"]]
        assert "Renew your passport" in titles

    # 4. Passport valid
    doc_expired.expiry_date = now + timedelta(days=365)
    db.commit()

    async with get_async_client() as client:
        gen4 = await client.post("/api/checklist/1/generate", headers={"Authorization": f"Bearer {token}"})
        titles = [i["title"] for i in gen4.json()["items"]]
        assert "Passport is ready" in titles

    db.close()


@pytest.mark.anyio
async def test_packing_and_budget_rules():
    """Requirements 12-13: Packing incomplete & budget exceeded rules"""
    token = get_token("check1@example.com")
    db = TestingSessionLocal()

    # Create incomplete packing list
    pkg = PackingList(
        trip_id=1,
        user_id=1,
        destination="Paris, France",
        categories=[{"name": "Clothes", "items": [{"name": "Shirt", "packed": False}]}],
        packing_score=50.0
    )
    db.add(pkg)

    # Create exceeded budget
    bgt = Budget(
        trip_id=1,
        total_budget=1000.0,
        spent=1200.0
    )
    db.add(bgt)
    db.commit()

    async with get_async_client() as client:
        gen = await client.post("/api/checklist/1/generate", headers={"Authorization": f"Bearer {token}"})
        titles = [i["title"] for i in gen.json()["items"]]
        assert "Complete your packing list" in titles
        assert "Trip budget exceeded — review expenses" in titles

    db.close()


@pytest.mark.anyio
async def test_itinerary_and_transit_rules():
    """Requirements 14-16: Itinerary & transit rules"""
    token = get_token("check1@example.com")
    db = TestingSessionLocal()

    # Add confirmed booking
    bk = TripBooking(
        trip_id=1,
        type="flight",
        provider="Air France",
        status="confirmed"
    )
    db.add(bk)
    db.commit()

    async with get_async_client() as client:
        gen = await client.post("/api/checklist/1/generate", headers={"Authorization": f"Bearer {token}"})
        titles = [i["title"] for i in gen.json()["items"]]
        assert "Review your transportation booking" in titles
        assert "Create your trip itinerary" in titles

    db.close()
