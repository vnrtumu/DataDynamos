"""Unit tests for the Automated Document Classifier & Smart OCR Router."""

from app.models import DocType, Document
from app.pipeline.classifier import classify_document


def test_classify_document_by_filename():
    doc_cms = Document(id="test1", filename="claim_cms1500.pdf", page_count=1)
    d_type, engine, conf, reason = classify_document(doc_cms)
    assert d_type == DocType.cms1500
    assert engine == "paddleocr"
    assert conf >= 0.90

    doc_cms_multi = Document(id="test2", filename="cms1500_bundle.pdf", page_count=3)
    d_type2, engine2, conf2, reason2 = classify_document(doc_cms_multi)
    assert d_type2 == DocType.cms1500_multi
    assert engine2 == "paddleocr"

    doc_ub = Document(id="test3", filename="ub04_form.pdf", page_count=1)
    d_type3, engine3, conf3, reason3 = classify_document(doc_ub)
    assert d_type3 == DocType.ub04
    assert engine3 == "pytesseract"

    doc_unstructured = Document(id="test4", filename="unstructured_bill.pdf", page_count=1)
    d_type4, engine4, conf4, reason4 = classify_document(doc_unstructured)
    assert d_type4 == DocType.unstructured_claim
