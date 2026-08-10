from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from datetime import datetime
from pydantic import BaseModel
from typing import List
import os
import shutil
import uuid

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
            "status": status,
            "url": f"/api/health-safety/documents/{d.id}/download"
        })
    return results

@router.post("/documents")
def upload_document(
    file: UploadFile = File(...),
    document_type: str = Form(...),
    expiry_date: str = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Validate file size (e.g. max 5MB)
    # Validate file type (e.g. pdf, jpg, png)
    allowed_types = ["application/pdf", "image/jpeg", "image/png"]
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Invalid file type. Only PDF, JPG, and PNG are allowed.")
    
    # Ensure directory exists
    user_dir = f"uploads/users/{current_user.id}/documents"
    os.makedirs(user_dir, exist_ok=True)
    
    # Secure filename
    ext = file.filename.split('.')[-1] if '.' in file.filename else 'bin'
    secure_filename = f"{uuid.uuid4().hex}.{ext}"
    file_path = os.path.join(user_dir, secure_filename)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    exp_dt = None
    if expiry_date:
        try:
            exp_dt = datetime.strptime(expiry_date, "%Y-%m-%d")
        except ValueError:
            pass
            
    new_doc = Document(
        user_id=current_user.id,
        document_type=document_type,
        encrypted_url=file_path,
        expiry_date=exp_dt
    )
    db.add(new_doc)
    db.commit()
    db.refresh(new_doc)
    
    return {"message": "Document uploaded successfully", "id": new_doc.id}

@router.delete("/documents/{doc_id}")
def delete_document(
    doc_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    doc = db.query(Document).filter(Document.id == doc_id, Document.user_id == current_user.id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
        
    # Delete file
    if os.path.exists(doc.encrypted_url):
        os.remove(doc.encrypted_url)
        
    db.delete(doc)
    db.commit()
    return {"message": "Document deleted successfully"}

@router.get("/documents/{doc_id}/download")
def download_document(
    doc_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    doc = db.query(Document).filter(Document.id == doc_id, Document.user_id == current_user.id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
        
    if not os.path.exists(doc.encrypted_url):
        raise HTTPException(status_code=404, detail="File not found on server")
        
    filename = f"{doc.document_type}_{doc.id}"
    ext = doc.encrypted_url.split('.')[-1]
    return FileResponse(doc.encrypted_url, filename=f"{filename}.{ext}")
