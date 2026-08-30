from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean, Text, Float, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional

from app.database.connection import Base


def _to_datetime(val: Any) -> Optional[datetime]:
    if not val:
        return None
    if isinstance(val, datetime):
        if val.tzinfo is None:
            return val.replace(tzinfo=timezone.utc)
        return val
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


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    trip_id = Column(Integer, ForeignKey("trips.id"), nullable=True, index=True)
    
    name = Column(String, nullable=False, default="Travel Document")
    category = Column(String, nullable=False, default="Other", index=True)  # Passport, Visa, Identity, Flight, Train, Hotel, Insurance, Driving, Other
    document_type = Column(String, nullable=True)  # e.g., Passport, Visa, Insurance
    
    file_name = Column(String, nullable=False, default="document.pdf")  # Original uploaded file name
    storage_key = Column(String, nullable=False, default="")  # Secure key/filename on disk
    encrypted_url = Column(String, nullable=True)  # URL or path placeholder for backward compatibility
    
    mime_type = Column(String, nullable=False, default="application/pdf")
    file_size = Column(Integer, nullable=False, default=0)  # in bytes
    
    expiry_date = Column(DateTime(timezone=True), nullable=True, index=True)
    ocr_status = Column(String, nullable=True)
    ocr_confidence = Column(Float, nullable=True)
    extraction_source = Column(String, nullable=True)
    document_type_confidence = Column(Float, nullable=True)
    extracted_metadata = Column(JSON, nullable=True)
    notes = Column(Text, nullable=True)
    is_deleted = Column(Boolean, default=False, nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User")
    trip = relationship("Trip")

    @property
    def status(self) -> str:
        """
        Calculates status:
        - NO_EXPIRY: if expiry_date is None
        - EXPIRED: if expiry_date < now
        - EXPIRING_SOON: if expiry_date <= now + 30 days
        - ACTIVE: otherwise
        """
        exp = _to_datetime(self.expiry_date)
        if not exp:
            return "NO_EXPIRY"
        
        now = datetime.now(timezone.utc)
        if exp < now:
            return "EXPIRED"
        elif exp <= now + timedelta(days=30):
            return "EXPIRING_SOON"
        else:
            return "ACTIVE"

    @property
    def days_until_expiry(self) -> Optional[int]:
        exp = _to_datetime(self.expiry_date)
        if not exp:
            return None
        now = datetime.now(timezone.utc)
        delta = exp - now
        return delta.days

    def to_dict(self) -> Dict[str, Any]:
        trip_title = None
        if self.trip:
            trip_title = getattr(self.trip, 'title', None) or getattr(self.trip, 'destination', None)

        exp_dt = _to_datetime(self.expiry_date)
        created_dt = _to_datetime(self.created_at)
        updated_dt = _to_datetime(self.updated_at) or created_dt

        exp_iso = exp_dt.isoformat() if exp_dt else None
        created_iso = created_dt.isoformat() if created_dt else None
        updated_iso = updated_dt.isoformat() if updated_dt else created_iso

        return {
            "id": self.id,
            "user_id": self.user_id,
            "trip_id": self.trip_id,
            "trip_title": trip_title,
            "name": self.name or "Travel Document",
            "category": self.category or "Other",
            "document_type": self.document_type or self.category,
            "file_name": self.file_name or "document.pdf",
            "mime_type": self.mime_type or "application/pdf",
            "file_size": self.file_size or 0,
            "expiry_date": exp_iso,
            "status": self.status,
            "days_until_expiry": self.days_until_expiry,
            "ocr_status": self.ocr_status,
            "ocr_confidence": self.ocr_confidence,
            "extraction_source": self.extraction_source,
            "document_type_confidence": self.document_type_confidence,
            "extracted_metadata": self.extracted_metadata,
            "notes": self.notes or "",
            "created_at": created_iso,
            "updated_at": updated_iso,
            "download_url": f"/api/documents/{self.id}/download",
            "preview_url": f"/api/documents/{self.id}/download?disposition=inline"
        }
