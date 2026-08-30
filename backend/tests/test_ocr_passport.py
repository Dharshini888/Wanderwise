import os
import sys
from datetime import datetime, timezone, timedelta

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.document_ocr import extract_document_metadata, _calculate_status


def test_passport_mrz_ocr_extraction(tmp_path):
    # Create sample passport text with MRZ
    sample_content = """
    PASSPORT
    REPUBLIC OF INDIA
    TYPE: P  COUNTRY CODE: IND  PASSPORT NO: Z9876543
    NAME: DHARSHINI RAMESH
    NATIONALITY: INDIAN
    DATE OF BIRTH: 15/08/1998
    DATE OF ISSUE: 10/05/2020
    DATE OF EXPIRY: 10/05/2030
    P<INDRAMESH<<DHARSHINI<<<<<<<<<<<<<<<<<<<<<<
    Z9876543<0IND9808151F3005108<<<<<<<<<<<<<<<04
    """
    file_p = tmp_path / "sample_passport.txt"
    file_p.write_text(sample_content, encoding="utf-8")

    res = extract_document_metadata(str(file_p), "text/plain")

    assert res["document_type"] == "Passport"
    fields = res["extracted_fields"]
    assert fields["full_name"] is not None
    assert fields["document_number"] is not None
    assert res["status"] in ["ACTIVE", "EXPIRING_SOON", "EXPIRED"]
    assert res["status_color"] in ["GREEN", "YELLOW", "RED"]


def test_calculate_status_logic():
    now = datetime.now(timezone.utc)

    # 1. Active (> 30 days)
    active_dt = now + timedelta(days=100)
    code, label, color = _calculate_status(active_dt)
    assert code == "ACTIVE"
    assert color == "GREEN"

    # 2. Expiring Soon (<= 30 days)
    exp_soon_dt = now + timedelta(days=15)
    code, label, color = _calculate_status(exp_soon_dt)
    assert code == "EXPIRING_SOON"
    assert color == "YELLOW"

    # 3. Expired (< current date)
    expired_dt = now - timedelta(days=10)
    code, label, color = _calculate_status(expired_dt)
    assert code == "EXPIRED"
    assert color == "RED"
