from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from datetime import datetime
from pydantic import BaseModel
from typing import List

from app.database.connection import get_db
from app.models.document import Document
from app.routes.auth import get_current_user
from app.models.user import User

router = APIRouter(prefix="/health-safety", tags=["Health & Safety"])

class VisaCheckResponse(BaseModel):
    destination: str
    requires_visa: bool
    notes: str

@router.get("/visa/{destination}", response_model=VisaCheckResponse)
def check_visa_requirements(
    destination: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    nationality = current_user.nationality or "Unknown"
    
    # Placeholder Logic: Call external visa API
    requires_visa = False
    notes = f"Visa-free entry for up to 90 days for {nationality} citizens."
    
    if nationality == "Unknown":
        notes = "Please update your profile with your nationality to check visa requirements."
        requires_visa = True

    return VisaCheckResponse(
        destination=destination,
        requires_visa=requires_visa,
        notes=notes
    )

@router.post("/scan-menu")
def scan_menu_for_allergies(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    # Placeholder Logic: Use OCR to extract text from the menu image and compare against current_user.allergies
    allergies = current_user.allergies if current_user.allergies else "None"
    
    return {
        "filename": file.filename,
        "allergies_profile": allergies,
        "warnings": ["Warning: Contains Peanuts", "Gluten-free options found"] if "peanuts" in allergies.lower() else ["Menu seems safe based on your profile."]
    }

@router.get("/documents", response_model=List[dict])
def list_documents(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    docs = db.query(Document).filter(Document.user_id == current_user.id).all()
    results = []
    for d in docs:
        status = "Valid"
        if d.expiry_date and d.expiry_date < datetime.utcnow():
            status = "Expired"
            
        results.append({
            "id": d.id,
            "document_type": d.document_type,
            "expiry_date": d.expiry_date,
            "status": status
        })
    return results
