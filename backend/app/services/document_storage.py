import os
import uuid
import logging
from typing import Tuple, Optional
from fastapi import UploadFile, HTTPException, status

logger = logging.getLogger(__name__)

# Uploads directory outside static/public route
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads", "documents")

# Security Constraints
ALLOWED_MIME_TYPES = {
    "application/pdf",
    "image/jpeg",
    "image/jpg",
    "image/png",
    "image/webp"
}

ALLOWED_EXTENSIONS = {
    ".pdf",
    ".jpg",
    ".jpeg",
    ".png",
    ".webp"
}

MAX_FILE_SIZE_BYTES = 15 * 1024 * 1024  # 15 MB


def ensure_upload_dir_exists() -> str:
    """Ensures the uploads directory exists and returns absolute path."""
    if not os.path.exists(UPLOAD_DIR):
        os.makedirs(UPLOAD_DIR, exist_ok=True)
    return UPLOAD_DIR


def validate_file_security(file: UploadFile) -> Tuple[str, str]:
    """
    Validates file extension and MIME type.
    Returns sanitized (original_filename, extension).
    """
    original_name = file.filename or "document.pdf"
    # Extract extension safely
    _, ext = os.path.splitext(original_name)
    ext = ext.lower()

    if not ext or ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file extension '{ext}'. Allowed extensions: PDF, JPG, JPEG, PNG, WEBP."
        )

    content_type = (file.content_type or "").lower()
    if content_type and content_type not in ALLOWED_MIME_TYPES:
        # Fallback check if browser sends generic octet-stream for valid extensions
        if content_type != "application/octet-stream" and content_type != "binary/octet-stream":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file type '{content_type}'. Allowed types: PDF, JPG, PNG, WEBP."
            )

    return original_name, ext


async def save_document_file(file: UploadFile) -> Tuple[str, str, int, str]:
    """
    Validates and securely saves an uploaded document file.
    Returns Tuple of (storage_key, original_filename, file_size, mime_type).
    """
    original_name, ext = validate_file_security(file)
    target_dir = ensure_upload_dir_exists()

    # Generate random storage key
    storage_key = f"doc_{uuid.uuid4().hex}{ext}"
    target_path = os.path.join(target_dir, storage_key)

    total_bytes = 0
    chunk_size = 1024 * 64  # 64 KB

    try:
        with open(target_path, "wb") as f:
            while True:
                chunk = await file.read(chunk_size)
                if not chunk:
                    break
                total_bytes += len(chunk)
                if total_bytes > MAX_FILE_SIZE_BYTES:
                    # Clean up partially written file
                    f.close()
                    if os.path.exists(target_path):
                        os.remove(target_path)
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail="File size exceeds the 15 MB limit."
                    )
                f.write(chunk)

        if total_bytes == 0:
            if os.path.exists(target_path):
                os.remove(target_path)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded file is empty."
            )

        # Map MIME type
        mime_type = file.content_type
        if not mime_type or mime_type in ["application/octet-stream", "binary/octet-stream"]:
            if ext == ".pdf":
                mime_type = "application/pdf"
            elif ext in [".jpg", ".jpeg"]:
                mime_type = "image/jpeg"
            elif ext == ".png":
                mime_type = "image/png"
            elif ext == ".webp":
                mime_type = "image/webp"
            else:
                mime_type = "application/pdf"

        logger.info(f"[DOC_STORAGE] Saved document '{original_name}' as key '{storage_key}' ({total_bytes} bytes)")
        return storage_key, original_name, total_bytes, mime_type

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[DOC_STORAGE] Failed to save document file: {e}")
        if os.path.exists(target_path):
            os.remove(target_path)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save document file securely."
        )


def get_document_file_path(storage_key: str) -> str:
    """
    Sanitizes storage_key against path traversal and returns absolute file path.
    Raises HTTPException 404 if file does not exist.
    """
    if not storage_key:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document file not found.")

    # Prevent path traversal attacks
    safe_key = os.path.basename(storage_key.replace("\\", "/"))
    target_dir = ensure_upload_dir_exists()
    file_path = os.path.join(target_dir, safe_key)

    if not os.path.exists(file_path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document file not found on storage.")

    return file_path


def delete_document_file(storage_key: str) -> bool:
    """Safely deletes a document file from storage if present."""
    if not storage_key:
        return False
    try:
        safe_key = os.path.basename(storage_key.replace("\\", "/"))
        target_dir = ensure_upload_dir_exists()
        file_path = os.path.join(target_dir, safe_key)
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"[DOC_STORAGE] Deleted document file: {safe_key}")
            return True
    except Exception as e:
        logger.error(f"[DOC_STORAGE] Error deleting file {storage_key}: {e}")
    return False
