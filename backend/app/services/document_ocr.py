import re
import os
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional
import tempfile

logger = logging.getLogger(__name__)

EASYOCR_AVAILABLE = False
try:
    import easyocr
    # We will initialize the reader lazily to not slow down app startup
    _reader = None
    EASYOCR_AVAILABLE = True
except ImportError:
    pass

try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False

try:
    import cv2
    import numpy as np
    from PIL import Image, ImageEnhance
    OPENCV_AVAILABLE = True
except ImportError:
    OPENCV_AVAILABLE = False

def get_easyocr_reader():
    global _reader
    if not EASYOCR_AVAILABLE:
        return None
    if _reader is None:
        logger.info("[OCR] Initializing EasyOCR reader...")
        _reader = easyocr.Reader(['en'], gpu=False)
    return _reader


def _calculate_status(exp: Optional[datetime]) -> tuple[str, str, str]:
    if not exp:
        return "NO_EXPIRY", "No Expiry Date", "GRAY"
    if exp.tzinfo is None:
        exp = exp.replace(tzinfo=timezone.utc)
    now = datetime.now(timezone.utc)
    if exp < now:
        return "EXPIRED", "Expired", "RED"
    elif exp <= now + timedelta(days=30):
        return "EXPIRING_SOON", "Expiring Soon", "YELLOW"
    else:
        return "ACTIVE", "Active", "GREEN"


def extract_document_metadata(file_path: str, mime_type: str = "") -> Dict[str, Any]:
    """
    Extracts text and metadata from a document file.
    Calculates Status: PROCESSING, SUCCESS, PARTIAL, FAILED, NO_TEXT.
    """
    if not os.path.exists(file_path):
        return _build_response("FAILED", "File not found", None)

    ext = os.path.splitext(file_path)[1].lower()
    is_pdf = ext == ".pdf" or "pdf" in mime_type

    raw_text = ""
    lines = []

    try:
        if ext in [".txt", ".text"] or "text" in mime_type:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                raw_text = f.read()
            lines = raw_text.split("\n")
        elif is_pdf and PYMUPDF_AVAILABLE:
            raw_text, lines = _process_pdf(file_path)
        else:
            raw_text, lines = _process_image(file_path)
    except Exception as e:
        logger.exception(f"[OCR] Processing error: {e}")
        return _build_response("FAILED", str(e), None)

    if not raw_text or not raw_text.strip():
        return _build_response("NO_TEXT", "No text detected", None)

    # Detect Document Type
    doc_type = _detect_document_type(raw_text, file_path)
    
    # Try MRZ Extraction First
    mrz_data = _extract_mrz(raw_text)
    
    extraction_source = "NONE"
    extracted_metadata = {}
    expiry_date_str = None
    expiry_dt_obj = None
    ocr_status = "SUCCESS"

    if doc_type == "Passport" and mrz_data:
        extraction_source = "MRZ"
        extracted_metadata = mrz_data
        expiry_date_str = mrz_data.get("expiry_date")
        if expiry_date_str:
            try:
                expiry_dt_obj = datetime.strptime(expiry_date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            except Exception:
                pass
        
        # Verify MRZ date sanity
        if expiry_date_str:
            is_sane, reason = _validate_date_sanity(expiry_date_str, is_expiry=True)
            if not is_sane:
                ocr_status = "PARTIAL"
                logger.warning(f"[OCR] MRZ expiry date {expiry_date_str} looks suspicious: {reason}")
    else:
        # Fallback to general OCR parsing
        extracted_metadata["full_name"] = _extract_full_name(raw_text)
        extracted_metadata["document_number"] = _extract_document_number(raw_text, doc_type)
        
        # Date extraction
        expiry_dt = _extract_expiry_date(raw_text)
        if expiry_dt:
            expiry_dt_obj = expiry_dt
            expiry_date_str = expiry_dt.strftime("%Y-%m-%d")
            extraction_source = "OCR"
            
            is_sane, reason = _validate_date_sanity(expiry_date_str, is_expiry=True)
            if not is_sane:
                ocr_status = "PARTIAL"

    if not expiry_date_str:
        ocr_status = "PARTIAL"

    # Remove None values
    extracted_metadata = {k: v for k, v in extracted_metadata.items() if v}
    status_code, status_label, status_color = _calculate_status(expiry_dt_obj)

    return {
        "ocr_status": ocr_status,
        "ocr_confidence": 0.9, # Fixed mock confidence for now
        "extraction_source": extraction_source,
        "document_type": doc_type,
        "document_type_confidence": 0.95,
        "expiry_date": expiry_date_str,
        "extracted_metadata": extracted_metadata,
        "extracted_fields": extracted_metadata,
        "status": status_code,
        "status_color": status_color
    }


def _build_response(status: str, msg: str, doc_type: Optional[str]) -> Dict[str, Any]:
    return {
        "ocr_status": status,
        "ocr_confidence": 0.0,
        "extraction_source": "NONE",
        "document_type": doc_type or "Other",
        "document_type_confidence": 0.0,
        "expiry_date": None,
        "extracted_metadata": {"error": msg} if msg else {}
    }


def _process_pdf(file_path: str):
    import fitz
    doc = fitz.open(file_path)
    text = ""
    for i in range(min(3, len(doc))): # Only check first 3 pages
        page = doc.load_page(i)
        page_text = page.get_text()
        if page_text:
            text += page_text + "\n"
    
    if len(text.strip()) > 50:
        return text, text.split("\n")
        
    # If not enough text, render as image and OCR
    reader = get_easyocr_reader()
    if not reader:
        return text, text.split("\n")
        
    all_text = ""
    lines = []
    for i in range(min(2, len(doc))):
        page = doc.load_page(i)
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2)) # upscale
        
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tf:
            pix.save(tf.name)
            img_path = tf.name
            
        try:
            processed_img_path = _preprocess_image(img_path)
            res = reader.readtext(processed_img_path, detail=0)
            page_text = "\n".join(res)
            all_text += page_text + "\n"
            lines.extend(res)
        finally:
            if os.path.exists(img_path):
                os.remove(img_path)
            if 'processed_img_path' in locals() and os.path.exists(processed_img_path) and processed_img_path != img_path:
                os.remove(processed_img_path)
                
    return all_text, lines

def _process_image(file_path: str):
    reader = get_easyocr_reader()
    if not reader:
        return "", []
        
    processed_img_path = file_path
    try:
        processed_img_path = _preprocess_image(file_path)
        res = reader.readtext(processed_img_path, detail=0)
        text = "\n".join(res)
        return text, res
    finally:
        if processed_img_path != file_path and os.path.exists(processed_img_path):
            try:
                os.remove(processed_img_path)
            except:
                pass

def _preprocess_image(file_path: str) -> str:
    """ Applies mild preprocessing for better OCR if OpenCV is available """
    if not OPENCV_AVAILABLE:
        return file_path
        
    try:
        img = cv2.imread(file_path)
        if img is None:
            return file_path
            
        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Mild contrast enhancement
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        gray = clahe.apply(gray)
        
        fd, temp_path = tempfile.mkstemp(suffix=".png")
        os.close(fd)
        
        cv2.imwrite(temp_path, gray)
        return temp_path
    except Exception as e:
        logger.warning(f"[OCR] Preprocessing failed: {e}")
        return file_path

def _detect_document_type(text: str, file_path: str) -> str:
    text_upper = text.upper()
    file_upper = os.path.basename(file_path).upper()

    if "PASSPORT" in text_upper or "P<" in text_upper or "PASSPORT" in file_upper:
        return "Passport"
    elif "VISA" in text_upper or "VISA" in file_upper:
        return "Visa"
    elif "LICENSE" in text_upper or "LICENCE" in text_upper or "DRIVING" in text_upper or "DRIVER" in text_upper:
        return "Driving"
    elif "FLIGHT" in text_upper or "BOARDING" in text_upper or "AIRLINE" in text_upper or "TICKET" in text_upper:
        return "Flight"
    elif "TRAIN" in text_upper or "RAILWAY" in text_upper or "IRCTC" in text_upper:
        return "Train"
    elif "HOTEL" in text_upper or "BOOKING" in text_upper or "RESERVATION" in text_upper or "CHECK-IN" in text_upper:
        return "Hotel"
    elif "INSURANCE" in text_upper or "POLICY" in text_upper or "COVERAGE" in text_upper:
        return "Insurance"
    elif "IDENTITY" in text_upper or "NATIONAL ID" in text_upper or "SSN" in text_upper or "AADHAAR" in text_upper:
        return "Identity"
    return "Passport" if "P<" in text_upper else "Other"


def _extract_mrz(text: str) -> Optional[Dict[str, str]]:
    """ 
    Robust MRZ extraction for TD3 (Passport) format.
    Expects 2 lines of 44 characters starting with P<
    """
    # Fix common OCR artifacts in MRZ
    clean_text = text.replace(" ", "").upper()
    clean_text = clean_text.replace("O", "0") # MRZ lines shouldn't have 'O' in numeric fields but let's be careful. Actually 'O' is allowed in names.
    
    # Find P< or P<... line
    lines = text.split("\n")
    mrz_lines = []
    
    for idx, line in enumerate(lines):
        cl = line.replace(" ", "").upper()
        if cl.startswith("P<"):
            # This is line 1.
            mrz_lines.append(cl)
            if idx + 1 < len(lines):
                mrz_lines.append(lines[idx+1].replace(" ", "").upper())
            break
            
    if len(mrz_lines) < 2:
        return None
        
    line1 = mrz_lines[0]
    line2 = mrz_lines[1]
    
    # MRZ lines should be 44 chars, but OCR might drop/add some. We'll do our best.
    if len(line1) < 30 or len(line2) < 30:
        return None
        
    data = {}
    try:
        # Line 1: P<USAHOLDER<<NAME<<<<<<<<<<<<<
        names = line1[5:].split("<<")
        if len(names) >= 2:
            data["surname"] = names[0].replace("<", " ").strip()
            data["given_names"] = names[1].replace("<", " ").strip()
            data["full_name"] = f"{data['given_names']} {data['surname']}".strip()
        else:
            data["surname"] = line1[5:].replace("<", " ").strip()
            data["full_name"] = data["surname"]
            
        data["issuing_country"] = line1[2:5].replace("<", "")
        
        # Line 2: 1234567890USA1234567M1234567<<<<<<<<<<<<<<0
        # doc num (9), check digit (1), nat (3), dob (6), cd (1), sex (1), exp (6)
        data["passport_number"] = line2[0:9].replace("<", "")
        data["document_number"] = data["passport_number"]
        data["nationality"] = line2[10:13].replace("<", "")
        
        dob_raw = line2[13:19]
        sex = line2[20:21]
        exp_raw = line2[21:27]
        
        if sex in ['M', 'F', 'X', '<']:
            data["sex"] = sex.replace("<", "Unknown")
            
        # Parse Dates (YYMMDD)
        if len(dob_raw) == 6 and dob_raw.isdigit():
            # DOB century heuristic: if YY > current_year_last_2, it's 1900s, else 2000s
            yy = int(dob_raw[0:2])
            curr_yy = datetime.now().year % 100
            year = 1900 + yy if yy > curr_yy else 2000 + yy
            data["date_of_birth"] = f"{year}-{dob_raw[2:4]}-{dob_raw[4:6]}"
            
        if len(exp_raw) == 6 and exp_raw.isdigit():
            # Expiry century heuristic: always 2000s for modern passports
            year = 2000 + int(exp_raw[0:2])
            data["expiry_date"] = f"{year}-{exp_raw[2:4]}-{exp_raw[4:6]}"
            
    except Exception as e:
        logger.warning(f"[OCR] MRZ parsing error: {e}")
        
    return data

def _extract_full_name(text: str) -> Optional[str]:
    patterns = [
        r"(?:NAME|FULL NAME|GIVEN NAME|HOLDER NAME)[:\s]+([A-Z\s]{3,30})",
        r"(?:NAME OF HOLDER)[:\s]+([A-Z\s]{3,30})",
    ]
    for pat in patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            clean = m.group(1).strip()
            if len(clean) > 2:
                return clean
    return None

def _extract_document_number(text: str, doc_type: str) -> Optional[str]:
    patterns = [
        r"(?:PASSPORT NO|PASSPORT NUMBER|DOCUMENT NO|DOC NO|LICENCE NO)[:\s]+([A-Z0-9]{6,12})",
        r"(?:NO|NUMBER)[:\s]+([A-Z0-9]{7,12})",
    ]
    for pat in patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            return m.group(1).strip()
    return None

def _extract_expiry_date(text: str) -> Optional[datetime]:
    expiry_keywords = ["expiry", "expires", "valid until", "exp date", "date of expiry", "expiration", "valid to", "valid through"]
    lines = text.split("\n")
    
    # Strategy 1: Find lines with expiry keywords
    for line in lines:
        for kw in expiry_keywords:
            if kw in line.lower():
                dt = _parse_date_string(line)
                if dt:
                    return dt
                    
    # Strategy 2: If no keyword found, grab the latest date in the document
    dates = []
    for line in lines:
        dt = _parse_date_string(line)
        if dt:
            dates.append(dt)
            
    if dates:
        # Sort dates and pick the one furthest in the future
        # Assuming expiry date is later than DOB and Issue date
        dates.sort(reverse=True)
        return dates[0]

    return None

def _parse_date_string(text: str) -> Optional[datetime]:
    # Support multiple formats
    patterns = [
        r"(\d{4}[-/\.]\d{2}[-/\.]\d{2})",  # YYYY-MM-DD
        r"(\d{2}[-/\.]\d{2}[-/\.]\d{4})",  # DD-MM-YYYY
        r"(\d{2}\s+(?:JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)[a-z]*\s+\d{4})",  # DD MMM YYYY
    ]

    for pat in patterns:
        matches = re.findall(pat, text, re.IGNORECASE)
        for m in matches:
            try:
                clean = m.strip().replace("O", "0") # Fix common OCR typo
                if "-" in clean or "/" in clean or "." in clean:
                    parts = re.split(r"[-/\.]", clean)
                    if len(parts[0]) == 4:
                        dt = datetime(int(parts[0]), int(parts[1]), int(parts[2]), tzinfo=timezone.utc)
                    else:
                        # DD-MM-YYYY vs MM-DD-YYYY is hard, assume DD-MM-YYYY if DD > 12
                        p1, p2, p3 = int(parts[0]), int(parts[1]), int(parts[2])
                        if p2 > 12 and p1 <= 12: # It's MM-DD-YYYY
                            dt = datetime(p3, p1, p2, tzinfo=timezone.utc)
                        else:
                            dt = datetime(p3, p2, p1, tzinfo=timezone.utc)
                    return dt
                else:
                    dt = datetime.strptime(clean, "%d %b %Y").replace(tzinfo=timezone.utc)
                    return dt
            except Exception:
                continue
    return None

def _validate_date_sanity(date_str: str, is_expiry: bool = True) -> tuple[bool, str]:
    """ Ensures the date is logical. """
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        
        # Extracted dates shouldn't be 100 years in the future or past
        if dt.year < 1900 or dt.year > 2100:
            return False, "Year out of logical bounds"
            
        if is_expiry and dt < now - timedelta(days=365*20):
            # Expiry date shouldn't be 20+ years in the past (likely DOB instead)
            return False, "Expiry date is too far in the past"
            
        return True, "Valid"
    except Exception as e:
        return False, str(e)
