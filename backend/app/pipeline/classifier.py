"""Automated Healthcare Claims Classifier & Smart OCR Router.

Eliminates manual intervention by auto-detecting healthcare claim document format tier:
- Tier A: CMS-1500 (Single Page)
- Tier B: CMS-1500 Multi (Multi-Page with Attachment Filtering)
- Tier C: UB-04 (Institutional Claim Form)
- Tier D: Unstructured Healthcare Claim & Clinical Notes
"""

from __future__ import annotations

from pathlib import Path
import fitz  # PyMuPDF

from app import storage
from app.models import DocType, Document


def classify_document(doc: Document) -> tuple[DocType, str, float, str]:
    """Auto-detect healthcare claim document tier & optimal OCR engine.

    Returns:
        (doc_type, ocr_engine, confidence, detection_reason)
    """
    filename_lower = doc.filename.lower()
    page_count = doc.page_count or 1

    extracted_text = ""
    original_path = storage._doc_dir(doc.id) / f"original{Path(doc.filename).suffix.lower()}"
    if original_path.exists() and doc.mime == "application/pdf":
        try:
            pdf = fitz.open(str(original_path))
            for page in pdf:
                extracted_text += " " + page.get_text()
        except Exception:
            pass

    text_upper = extracted_text.upper()

    # 1. Tier A & B: CMS-1500 Standard Claims
    if "cms1500" in filename_lower or "cms-1500" in filename_lower or "cms_1500" in filename_lower or "1500" in filename_lower or "CMS-1500" in text_upper or "CMS 1500" in text_upper or "HEALTH INSURANCE CLAIM FORM" in text_upper:
        if page_count > 1:
            doc_type = DocType.cms1500_multi
            reason = f"Auto-detected Tier B: CMS-1500 Multi-Page ({page_count} pages with attachments)"
        else:
            doc_type = DocType.cms1500
            reason = "Auto-detected Tier A: CMS-1500 Standard Machine-Printed Single Page Form"
        engine = "paddleocr"
        confidence = 0.98

    # 2. Tier C: UB-04 Institutional Claims
    elif "ub04" in filename_lower or "ub-04" in filename_lower or "ub_04" in filename_lower or "UB-04" in text_upper or "UB04" in text_upper or "INSTITUTIONAL" in text_upper or "TYPE OF BILL" in text_upper:
        doc_type = DocType.ub04
        engine = "pytesseract"
        confidence = 0.97
        reason = "Auto-detected Tier C: UB-04 Institutional Claim Form"

    # 3. Tier D: Unstructured Healthcare Claims
    elif "MEDICAL BILL" in text_upper or "CLINICAL" in text_upper or "DISCHARGE NOTE" in text_upper or "unstructured" in filename_lower or "note" in filename_lower:
        doc_type = DocType.unstructured_claim
        engine = "qwen-vl"
        confidence = 0.94
        reason = "Auto-detected Tier D: Unstructured Healthcare Claim & Clinical Note"

    # 4. Default Claims Fallback
    else:
        if page_count > 1:
            doc_type = DocType.cms1500_multi
            engine = "paddleocr"
            reason = f"Auto-classified as Tier B: Multi-Page Claim ({page_count} pages)"
        else:
            doc_type = DocType.cms1500
            engine = "paddleocr"
            reason = "Auto-classified as Tier A: Single Page CMS-1500 Claim Form"
        confidence = 0.92

    return doc_type, engine, confidence, reason
