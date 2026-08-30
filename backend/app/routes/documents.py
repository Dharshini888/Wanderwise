from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Query, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone, timedelta
import logging

from app.database.connection import get_db
from app.models.document import Document, _to_datetime
from app.models.trip import Trip
from app.models.user import User
from app.routes.auth import get_current_user
from app.services.document_storage import (
    save_document_file,
    get_document_file_path,
    delete_document_file,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/documents", tags=["Documents"])


class DocumentUpdateRequest(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    document_type: Optional[str] = None
    trip_id: Optional[int] = None
    expiry_date: Optional[str] = None
    notes: Optional[str] = None


def _parse_expiry(expiry_str: Optional[str]) -> Optional[datetime]:
    if not expiry_str or expiry_str.strip().lower() in ["", "none", "null"]:
        return None
    try:
        clean_str = expiry_str.strip()
        if "T" in clean_str:
            dt = datetime.fromisoformat(clean_str.replace("Z", "+00:00"))
        else:
            dt = datetime.strptime(clean_str, "%Y-%m-%d")
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception as e:
        logger.warning(f"[DOCUMENTS] Could not parse expiry_date '{expiry_str}': {e}")
        return None

def _run_ocr_background(doc_id: int):
    from app.database.connection import SessionLocal
    from app.services.document_ocr import extract_document_metadata
    
    db = SessionLocal()
    try:
        doc = db.query(Document).filter(Document.id == doc_id).first()
        if not doc:
            return
            
        file_path = get_document_file_path(doc.storage_key)
        
        try:
            ocr_result = extract_document_metadata(file_path, doc.mime_type)
            
            doc.ocr_status = ocr_result.get("ocr_status", "FAILED")
            doc.ocr_confidence = ocr_result.get("ocr_confidence", 0.0)
            doc.extraction_source = ocr_result.get("extraction_source", "NONE")
            doc.document_type_confidence = ocr_result.get("document_type_confidence", 0.0)
            doc.extracted_metadata = ocr_result.get("extracted_metadata", {})
            
            if ocr_result.get("document_type") and doc.category in ["Other", None, ""]:
                doc.category = ocr_result["document_type"]
                doc.document_type = ocr_result["document_type"]
                
            if ocr_result.get("expiry_date"):
                exp_dt = _parse_expiry(ocr_result["expiry_date"])
                if exp_dt:
                    doc.expiry_date = exp_dt
                    
            db.commit()
            logger.info(f"[DOCUMENTS] OCR completed for doc #{doc_id} with status {doc.ocr_status}")
            
        except Exception as e:
            logger.warning(f"[OCR] Background extraction failed for doc #{doc_id}: {e}")
            doc.ocr_status = "FAILED"
            db.commit()
            
    finally:
        db.close()

@router.get("")
@router.get("/")
def get_documents(
    category: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    trip_id: Optional[int] = Query(None),
    search: Optional[str] = Query(None),
    sort_by: Optional[str] = Query("recently_added"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieves all non-deleted travel documents for current user with optional filtering, search, and sorting.
    """
    query = db.query(Document).filter(
        Document.user_id == current_user.id,
        Document.is_deleted == False
    )

    # Category Filter
    if category and category.lower() != "all":
        query = query.filter(Document.category.ilike(category))

    # Trip Filter
    if trip_id is not None:
        if trip_id == 0:
            query = query.filter(Document.trip_id == None)
        else:
            query = query.filter(Document.trip_id == trip_id)

    # Text Search Filter
    if search and search.strip():
        term = f"%{search.strip()}%"
        # Search in name, category, notes, or associated trip title
        query = query.outerjoin(Trip).filter(
            (Document.name.ilike(term)) |
            (Document.category.ilike(term)) |
            (Document.notes.ilike(term)) |
            (Trip.title.ilike(term)) |
            (Trip.destination.ilike(term))
        )

    all_user_docs = query.all()

    # Calculate overall stats before applying status filter
    total_docs = db.query(Document).filter(
        Document.user_id == current_user.id,
        Document.is_deleted == False
    ).all()

    active_cnt = sum(1 for d in total_docs if d.status == "ACTIVE")
    expiring_soon_cnt = sum(1 for d in total_docs if d.status == "EXPIRING_SOON")
    expired_cnt = sum(1 for d in total_docs if d.status == "EXPIRED")
    trip_linked_cnt = sum(1 for d in total_docs if d.trip_id is not None)

    # Status Filter
    filtered_docs = []
    if status_filter and status_filter.lower() != "all":
        target = status_filter.upper().replace(" ", "_")
        for d in all_user_docs:
            if d.status == target:
                filtered_docs.append(d)
    else:
        filtered_docs = all_user_docs

    # Sorting
    if sort_by == "oldest":
        filtered_docs.sort(key=lambda d: _to_datetime(d.created_at) or datetime.min.replace(tzinfo=timezone.utc))
    elif sort_by == "name_asc":
        filtered_docs.sort(key=lambda d: (d.name or "").lower())
    elif sort_by == "expiry_asc":
        # Put documents with expiry dates first, sorted by earliest expiry
        filtered_docs.sort(key=lambda d: (0 if _to_datetime(d.expiry_date) else 1, _to_datetime(d.expiry_date) or datetime.max.replace(tzinfo=timezone.utc)))
    else:  # recently_added (default)
        filtered_docs.sort(key=lambda d: _to_datetime(d.created_at) or datetime.min.replace(tzinfo=timezone.utc), reverse=True)

    return {
        "documents": [d.to_dict() for d in filtered_docs],
        "stats": {
            "total": len(total_docs),
            "active": active_cnt,
            "expiring_soon": expiring_soon_cnt,
            "expired": expired_cnt,
            "trip_linked": trip_linked_cnt,
        }
    }


@router.get("/stats")
def get_documents_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Returns high-level stats summary for Dashboard / Widgets.
    """
    all_user_docs = db.query(Document).filter(
        Document.user_id == current_user.id,
        Document.is_deleted == False
    ).all()

    active_cnt = sum(1 for d in all_user_docs if d.status == "ACTIVE")
    expiring_soon_cnt = sum(1 for d in all_user_docs if d.status == "EXPIRING_SOON")
    expired_cnt = sum(1 for d in all_user_docs if d.status == "EXPIRED")
    trip_linked_cnt = sum(1 for d in all_user_docs if d.trip_id is not None)

    return {
        "total": len(all_user_docs),
        "active": active_cnt,
        "expiring_soon": expiring_soon_cnt,
        "expired": expired_cnt,
        "trip_linked": trip_linked_cnt,
    }


@router.get("/{doc_id}")
def get_document_details(
    doc_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Returns single document details owned by current user.
    """
    doc = db.query(Document).filter(
        Document.id == doc_id,
        Document.user_id == current_user.id,
        Document.is_deleted == False
    ).first()

    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found or access denied."
        )

    return doc.to_dict()


@router.post("", status_code=status.HTTP_201_CREATED)
@router.post("/", status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    name: str = Form(...),
    category: str = Form("Other"),
    trip_id: Optional[int] = Form(None),
    expiry_date: Optional[str] = Form(None),
    notes: Optional[str] = Form(None),
    document_type: Optional[str] = Form(None),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Securely uploads a new travel document file and triggers OCR in background.
    """
    if not name or not name.strip():
        name = file.filename or "Travel Document"

    # Validate associated trip if provided
    valid_trip_id = None
    if trip_id and trip_id > 0:
        trip = db.query(Trip).filter(Trip.id == trip_id, Trip.user_id == current_user.id).first()
        if not trip:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Associated trip not found or does not belong to you."
            )
        valid_trip_id = trip.id

    # Save file securely to storage
    storage_key, original_filename, file_size, mime_type = await save_document_file(file)
    abs_file_path = get_document_file_path(storage_key)

    # OCR is now backgrounded, we don't block
    exp_dt = _parse_expiry(expiry_date)
    final_category = category.strip() if (category and category.strip() != "Other") else "Other"

    doc = Document(
        user_id=current_user.id,
        trip_id=valid_trip_id,
        name=name.strip(),
        category=final_category,
        document_type=document_type.strip() if document_type else final_category,
        file_name=original_filename,
        storage_key=storage_key,
        encrypted_url=f"/api/documents/storage/{storage_key}",
        mime_type=mime_type,
        file_size=file_size,
        expiry_date=exp_dt,
        notes=notes.strip() if notes else None,
        is_deleted=False,
        ocr_status="PROCESSING"
    )

    db.add(doc)
    db.commit()
    db.refresh(doc)

    logger.info(f"[DOCUMENTS] User {current_user.id} uploaded document #{doc.id} ('{doc.name}'), OCR started")
    
    # Dispatch Background Task
    background_tasks.add_task(_run_ocr_background, doc.id)
    
    return doc.to_dict()


@router.put("/{doc_id}")
@router.patch("/{doc_id}")
def update_document_metadata(
    doc_id: int,
    data: DocumentUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Updates metadata for a document owned by current user.
    """
    doc = db.query(Document).filter(
        Document.id == doc_id,
        Document.user_id == current_user.id,
        Document.is_deleted == False
    ).first()

    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found or access denied."
        )

    if data.name is not None:
        doc.name = data.name.strip()
    if data.category is not None:
        doc.category = data.category.strip()
    if data.document_type is not None:
        doc.document_type = data.document_type.strip()
    if data.notes is not None:
        doc.notes = data.notes.strip()

    if data.trip_id is not None:
        if data.trip_id == 0 or data.trip_id < 0:
            doc.trip_id = None
        else:
            trip = db.query(Trip).filter(Trip.id == data.trip_id, Trip.user_id == current_user.id).first()
            if not trip:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Associated trip not found or does not belong to you."
                )
            doc.trip_id = trip.id

    if data.expiry_date is not None:
        doc.expiry_date = _parse_expiry(data.expiry_date)

    db.commit()
    db.refresh(doc)

    logger.info(f"[DOCUMENTS] User {current_user.id} updated document #{doc.id}")
    return doc.to_dict()


@router.delete("/{doc_id}")
def delete_document(
    doc_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Deletes a document owned by current user.
    """
    doc = db.query(Document).filter(
        Document.id == doc_id,
        Document.user_id == current_user.id,
        Document.is_deleted == False
    ).first()

    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found or access denied."
        )

    # Delete storage file
    if doc.storage_key:
        delete_document_file(doc.storage_key)

    doc.is_deleted = True
    db.commit()

    logger.info(f"[DOCUMENTS] User {current_user.id} deleted document #{doc.id}")
    return {"message": "Document deleted successfully", "id": doc_id}


@router.get("/{doc_id}/download")
def download_document_file(
    doc_id: int,
    disposition: str = Query("inline"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Streams or downloads a document file securely after verifying user ownership.
    Never exposes internal filesystem paths.
    """
    doc = db.query(Document).filter(
        Document.id == doc_id,
        Document.user_id == current_user.id,
        Document.is_deleted == False
    ).first()

    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found or access denied."
        )

    file_path = get_document_file_path(doc.storage_key)

    disp_header = "inline" if disposition.lower() == "inline" else "attachment"
    filename_header = doc.file_name.replace('"', '\\"')

    return FileResponse(
        path=file_path,
        media_type=doc.mime_type or "application/pdf",
        headers={
            "Content-Disposition": f'{disp_header}; filename="{filename_header}"'
        }
    )

@router.post("/{doc_id}/analyze")
def analyze_document(
    doc_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Manually triggers OCR analysis for an existing document.
    """
    doc = db.query(Document).filter(
        Document.id == doc_id,
        Document.user_id == current_user.id,
        Document.is_deleted == False
    ).first()

    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found or access denied."
        )
        
    doc.ocr_status = "PROCESSING"
    db.commit()
    db.refresh(doc)
    
    background_tasks.add_task(_run_ocr_background, doc.id)
    
    return doc.to_dict()
