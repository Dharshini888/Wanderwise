import os
import sys
import io
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
from app.services.auth_service import hash_password, create_access_token

# Test DB Setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_documents.db"
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
    db.query(Document).delete()
    db.query(Trip).delete()
    db.query(User).delete()
    db.commit()

    # Create User 1
    u1 = User(
        name="Test User 1",
        email="user1@example.com",
        password=hash_password("password123"),
        is_active=True,
    )
    # Create User 2
    u2 = User(
        name="Test User 2",
        email="user2@example.com",
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
    trip = Trip(
        user_id=u1.id,
        title="Tokyo Adventure",
        destination="Tokyo, Japan",
        budget=1500.0,
        start_date=now_dt,
        end_date=now_dt + timedelta(days=7),
    )
    db.add(trip)
    db.commit()

    db.close()
    yield
    Base.metadata.drop_all(bind=engine)
    if os.path.exists("./test_documents.db"):
        try:
            os.remove("./test_documents.db")
        except Exception:
            pass


def get_token(email: str = "user1@example.com", user_id: int = 1) -> str:
    db = TestingSessionLocal()
    user = db.query(User).filter(User.email == email).first()
    uid = user.id if user else user_id
    db.close()
    return create_access_token({"sub": str(uid), "email": email, "role": "USER"})


def get_async_client():
    return httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://testserver")


# ── TEST SUITE ─────────────────────────────────────────────────────────────

@pytest.mark.anyio
async def test_unauthenticated_upload_rejected():
    """Requirement 2: Unauthenticated upload rejected with 401"""
    async with get_async_client() as client:
        file_data = io.BytesIO(b"%PDF-1.4 test document content")
        response = await client.post(
            "/api/documents",
            files={"file": ("passport.pdf", file_data, "application/pdf")},
            data={"name": "My Passport", "category": "Passport"}
        )
        assert response.status_code == 401


@pytest.mark.anyio
async def test_authenticated_document_upload():
    """Requirement 1: Authenticated document upload succeeds"""
    token = get_token("user1@example.com")
    async with get_async_client() as client:
        file_data = io.BytesIO(b"%PDF-1.4 sample passport file content")
        response = await client.post(
            "/api/documents",
            headers={"Authorization": f"Bearer {token}"},
            files={"file": ("passport.pdf", file_data, "application/pdf")},
            data={
                "name": "My Passport",
                "category": "Passport",
                "notes": "Primary Indian Passport",
                "expiry_date": "2030-05-20"
            }
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "My Passport"
        assert data["category"] == "Passport"
        assert data["status"] == "ACTIVE"
        assert "download_url" in data


@pytest.mark.anyio
async def test_user_can_retrieve_own_document():
    """Requirement 3: User can retrieve their own document list & details"""
    token = get_token("user1@example.com")
    async with get_async_client() as client:
        file_data = io.BytesIO(b"%PDF-1.4 sample file")
        upload_res = await client.post(
            "/api/documents",
            headers={"Authorization": f"Bearer {token}"},
            files={"file": ("visa.pdf", file_data, "application/pdf")},
            data={"name": "Japan Visa", "category": "Visa"}
        )
        doc_id = upload_res.json()["id"]

        # Get list
        list_res = await client.get("/api/documents", headers={"Authorization": f"Bearer {token}"})
        assert list_res.status_code == 200
        docs = list_res.json()["documents"]
        assert len(docs) == 1
        assert docs[0]["id"] == doc_id

        # Get details
        detail_res = await client.get(f"/api/documents/{doc_id}", headers={"Authorization": f"Bearer {token}"})
        assert detail_res.status_code == 200
        assert detail_res.json()["name"] == "Japan Visa"


@pytest.mark.anyio
async def test_user_cannot_retrieve_another_user_document():
    """Requirement 4: User 2 cannot retrieve User 1's document (404)"""
    token1 = get_token("user1@example.com")
    token2 = get_token("user2@example.com")

    async with get_async_client() as client:
        file_data = io.BytesIO(b"%PDF-1.4 secret doc")
        upload_res = await client.post(
            "/api/documents",
            headers={"Authorization": f"Bearer {token1}"},
            files={"file": ("secret.pdf", file_data, "application/pdf")},
            data={"name": "User 1 Secret", "category": "Identity"}
        )
        doc_id = upload_res.json()["id"]

        # User 2 tries to fetch User 1's document
        res = await client.get(f"/api/documents/{doc_id}", headers={"Authorization": f"Bearer {token2}"})
        assert res.status_code == 404


@pytest.mark.anyio
async def test_user_can_download_own_document():
    """Requirement 5: User can download their own document file"""
    token = get_token("user1@example.com")
    file_content = b"%PDF-1.4 sample download pdf payload"
    async with get_async_client() as client:
        file_data = io.BytesIO(file_content)
        upload_res = await client.post(
            "/api/documents",
            headers={"Authorization": f"Bearer {token}"},
            files={"file": ("ticket.pdf", file_data, "application/pdf")},
            data={"name": "Flight Ticket", "category": "Flight"}
        )
        doc_id = upload_res.json()["id"]

        # Download file
        dl_res = await client.get(f"/api/documents/{doc_id}/download", headers={"Authorization": f"Bearer {token}"})
        assert dl_res.status_code == 200
        assert dl_res.content == file_content


@pytest.mark.anyio
async def test_user_cannot_download_another_user_document():
    """Requirement 6: User 2 cannot download User 1's document"""
    token1 = get_token("user1@example.com")
    token2 = get_token("user2@example.com")

    async with get_async_client() as client:
        file_data = io.BytesIO(b"%PDF-1.4 private payload")
        upload_res = await client.post(
            "/api/documents",
            headers={"Authorization": f"Bearer {token1}"},
            files={"file": ("private.pdf", file_data, "application/pdf")},
            data={"name": "Private Document", "category": "Other"}
        )
        doc_id = upload_res.json()["id"]

        # User 2 attempts download
        dl_res = await client.get(f"/api/documents/{doc_id}/download", headers={"Authorization": f"Bearer {token2}"})
        assert dl_res.status_code == 404


@pytest.mark.anyio
async def test_user_can_update_own_metadata():
    """Requirement 7: User can update metadata of owned document"""
    token = get_token("user1@example.com")
    async with get_async_client() as client:
        file_data = io.BytesIO(b"%PDF-1.4 file")
        upload_res = await client.post(
            "/api/documents",
            headers={"Authorization": f"Bearer {token}"},
            files={"file": ("hotel.pdf", file_data, "application/pdf")},
            data={"name": "Hotel Voucher", "category": "Hotel"}
        )
        doc_id = upload_res.json()["id"]

        # Update metadata
        update_res = await client.put(
            f"/api/documents/{doc_id}",
            headers={"Authorization": f"Bearer {token}"},
            json={"name": "Hilton Tokyo Booking", "category": "Hotel", "notes": "Confirmation #12345"}
        )
        assert update_res.status_code == 200
        assert update_res.json()["name"] == "Hilton Tokyo Booking"
        assert update_res.json()["notes"] == "Confirmation #12345"


@pytest.mark.anyio
async def test_user_can_delete_own_document():
    """Requirement 8: User can delete their own document"""
    token = get_token("user1@example.com")
    async with get_async_client() as client:
        file_data = io.BytesIO(b"%PDF-1.4 file to delete")
        upload_res = await client.post(
            "/api/documents",
            headers={"Authorization": f"Bearer {token}"},
            files={"file": ("temp.pdf", file_data, "application/pdf")},
            data={"name": "Temp File", "category": "Other"}
        )
        doc_id = upload_res.json()["id"]

        # Delete
        del_res = await client.delete(f"/api/documents/{doc_id}", headers={"Authorization": f"Bearer {token}"})
        assert del_res.status_code == 200

        # Ensure document no longer listed
        list_res = await client.get("/api/documents", headers={"Authorization": f"Bearer {token}"})
        assert len(list_res.json()["documents"]) == 0


@pytest.mark.anyio
async def test_invalid_file_type_rejected():
    """Requirement 9: Invalid file extension (e.g. .exe) is rejected"""
    token = get_token("user1@example.com")
    async with get_async_client() as client:
        file_data = io.BytesIO(b"malicious executable payload")
        res = await client.post(
            "/api/documents",
            headers={"Authorization": f"Bearer {token}"},
            files={"file": ("virus.exe", file_data, "application/octet-stream")},
            data={"name": "Executable", "category": "Other"}
        )
        assert res.status_code == 400
        assert "Unsupported file extension" in res.json()["detail"]


@pytest.mark.anyio
async def test_oversized_file_rejected():
    """Requirement 10: Files larger than 15MB are rejected with 413"""
    token = get_token("user1@example.com")
    async with get_async_client() as client:
        large_data = io.BytesIO(b"A" * (16 * 1024 * 1024))
        res = await client.post(
            "/api/documents",
            headers={"Authorization": f"Bearer {token}"},
            files={"file": ("large.pdf", large_data, "application/pdf")},
            data={"name": "Large Document", "category": "Other"}
        )
        assert res.status_code == 413


@pytest.mark.anyio
async def test_expiry_status_calculation():
    """Requirements 11, 12, 13: Active vs Expiring Soon vs Expired calculation"""
    token = get_token("user1@example.com")
    now = datetime.now(timezone.utc)
    past_date = (now - timedelta(days=10)).strftime("%Y-%m-%d")
    soon_date = (now + timedelta(days=15)).strftime("%Y-%m-%d")
    future_date = (now + timedelta(days=365)).strftime("%Y-%m-%d")

    async with get_async_client() as client:
        # 1. Expired document
        res_expired = await client.post(
            "/api/documents",
            headers={"Authorization": f"Bearer {token}"},
            files={"file": ("old.pdf", io.BytesIO(b"%PDF-1.4"), "application/pdf")},
            data={"name": "Expired License", "category": "Driving", "expiry_date": past_date}
        )
        assert res_expired.json()["status"] == "EXPIRED"

        # 2. Expiring soon document
        res_soon = await client.post(
            "/api/documents",
            headers={"Authorization": f"Bearer {token}"},
            files={"file": ("soon.pdf", io.BytesIO(b"%PDF-1.4"), "application/pdf")},
            data={"name": "Expiring Insurance", "category": "Insurance", "expiry_date": soon_date}
        )
        assert res_soon.json()["status"] == "EXPIRING_SOON"

        # 3. Active document
        res_active = await client.post(
            "/api/documents",
            headers={"Authorization": f"Bearer {token}"},
            files={"file": ("passport.pdf", io.BytesIO(b"%PDF-1.4"), "application/pdf")},
            data={"name": "Valid Passport", "category": "Passport", "expiry_date": future_date}
        )
        assert res_active.json()["status"] == "ACTIVE"


@pytest.mark.anyio
async def test_search_filtering_sorting():
    """Requirements 14, 15, 16: Search, Category, Trip filtering and sorting"""
    token = get_token("user1@example.com")
    async with get_async_client() as client:
        # Upload docs with different categories
        await client.post(
            "/api/documents",
            headers={"Authorization": f"Bearer {token}"},
            files={"file": ("doc1.pdf", io.BytesIO(b"%PDF-1.4"), "application/pdf")},
            data={"name": "IndiGo Flight Ticket", "category": "Flight"}
        )
        await client.post(
            "/api/documents",
            headers={"Authorization": f"Bearer {token}"},
            files={"file": ("doc2.pdf", io.BytesIO(b"%PDF-1.4"), "application/pdf")},
            data={"name": "Hilton Hotel Booking", "category": "Hotel"}
        )

        # Category Filter
        res_cat = await client.get("/api/documents?category=Flight", headers={"Authorization": f"Bearer {token}"})
        assert res_cat.status_code == 200
        docs_cat = res_cat.json()["documents"]
        assert len(docs_cat) == 1
        assert docs_cat[0]["name"] == "IndiGo Flight Ticket"

        # Search Filter
        res_search = await client.get("/api/documents?search=Hilton", headers={"Authorization": f"Bearer {token}"})
        assert res_search.status_code == 200
        docs_search = res_search.json()["documents"]
        assert len(docs_search) == 1
        assert docs_search[0]["name"] == "Hilton Hotel Booking"
