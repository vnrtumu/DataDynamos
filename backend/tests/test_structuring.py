"""Phase 4 structuring tests. Use the offline mock provider — no langextract dep."""

from fastapi.testclient import TestClient

import pytest

from app.config import settings
from app.extraction.base import build_page_offsets, char_to_page, to_number
from app.main import app
from app.models import DocumentStatus
from app.schemas import OCRPage, OCRResult

from .conftest import SAMPLES


@pytest.mark.parametrize(
    "text, expected",
    [
        ("$1,234.56", 1234.56),
        ("$50,000", 50000.0),
        ("250000", 250000.0),
        # amount embedded in prose (real OCR'd fields look like this)
        ("US $96,000 (ninety-six thousand US dollars)", 96000.0),
        # currency-anchored: skip the incidental "twelve (12)" in a liability clause
        ("aggregate liability over the twelve (12) months shall not exceed US $96,000.", 96000.0),
        # tolerate the OCR 0->o misread
        ("US $96,0o0", 96000.0),
    ],
)
def test_to_number_extracts_amount_from_prose(text, expected):
    assert to_number(text) == expected


def test_to_number_raises_when_no_number():
    with pytest.raises(ValueError):
        to_number("no digits here")


def _upload(client: TestClient, name: str, doc_type: str | None = None) -> str:
    data = {"doc_type": doc_type} if doc_type else None
    with (SAMPLES / name).open("rb") as fh:
        resp = client.post("/documents", files={"file": (name, fh)}, data=data)
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


def _ocr(client: TestClient, doc_id: str) -> None:
    resp = client.post(f"/documents/{doc_id}/ocr", params={"engine": "mock"})
    assert resp.status_code == 200, resp.text


def test_structure_requires_ocr_returns_409():
    with TestClient(app) as client:
        doc_id = _upload(client, "invoice-clean.pdf")
        resp = client.post(
            f"/documents/{doc_id}/structure", params={"doc_type": "invoice", "provider": "mock", "ocr_engine": "mock"}
        )
        assert resp.status_code == 409, resp.text


def test_structure_route_persists_and_advances_status():
    with TestClient(app) as client:
        doc_id = _upload(client, "invoice-clean.pdf")
        _ocr(client, doc_id)

        post = client.post(
            f"/documents/{doc_id}/structure", params={"doc_type": "invoice", "provider": "mock", "ocr_engine": "mock"}
        )
        assert post.status_code == 200, post.text
        result = post.json()
        assert result["status"] == "structured"
        assert result["doc_type"] == "invoice"
        assert result["provider"] == "mock"
        assert 0.0 <= result["extraction_confidence"] <= 1.0
        assert result["fields"]["total"]["value"] == 1234.56
        assert result["fields"]["line_items"], "expected at least one line item"

        # Document status advanced.
        detail = client.get(f"/documents/{doc_id}").json()
        assert detail["status"] == "structured"


def test_structure_get_refetch():
    with TestClient(app) as client:
        doc_id = _upload(client, "invoice-clean.pdf")
        _ocr(client, doc_id)
        post = client.post(
            f"/documents/{doc_id}/structure", params={"doc_type": "invoice", "provider": "mock", "ocr_engine": "mock"}
        ).json()

        got = client.get(f"/documents/{doc_id}/structure")
        assert got.status_code == 200, got.text
        got = got.json()
        assert got["extraction_confidence"] == post["extraction_confidence"]
        assert got["fields"] == post["fields"]


def test_missing_field_is_null_not_hallucinated():
    """po_number is intentionally absent -> explicit null + low confidence."""
    with TestClient(app) as client:
        doc_id = _upload(client, "invoice-clean.pdf")
        _ocr(client, doc_id)
        result = client.post(
            f"/documents/{doc_id}/structure", params={"doc_type": "invoice", "provider": "mock", "ocr_engine": "mock"}
        ).json()

        po = result["fields"]["po_number"]
        assert po["value"] is None
        assert po["confidence"] < settings.extraction_confidence_warn
        assert po["grounding"] is None


def test_grounding_maps_to_page():
    with TestClient(app) as client:
        doc_id = _upload(client, "invoice-clean.pdf")
        _ocr(client, doc_id)
        full_text = client.get(f"/documents/{doc_id}/ocr", params={"engine": "mock"}).json()[
            "full_text"
        ]
        result = client.post(
            f"/documents/{doc_id}/structure", params={"doc_type": "invoice", "provider": "mock", "ocr_engine": "mock"}
        ).json()

        total = result["grounding_map"]["total"]
        assert total["page"] == 1
        assert total["char_start"] is not None and total["char_end"] is not None
        assert full_text[total["char_start"] : total["char_end"]] == total["snippet"]


def test_doc_type_resolution_from_document_and_400_when_unset():
    with TestClient(app) as client:
        # doc_type set at upload -> the ?doc_type param can be omitted.
        typed = _upload(client, "invoice-clean.pdf", doc_type="invoice")
        _ocr(client, typed)
        resp = client.post(f"/documents/{typed}/structure", params={"provider": "mock", "ocr_engine": "mock"})
        assert resp.status_code == 200, resp.text
        assert resp.json()["doc_type"] == "invoice"

        # No doc_type anywhere -> 400.
        untyped = _upload(client, "invoice-clean.pdf")
        _ocr(client, untyped)
        resp = client.post(f"/documents/{untyped}/structure", params={"provider": "mock", "ocr_engine": "mock"})
        assert resp.status_code == 400, resp.text


def test_unknown_provider_returns_400():
    with TestClient(app) as client:
        doc_id = _upload(client, "invoice-clean.pdf")
        _ocr(client, doc_id)
        resp = client.post(
            f"/documents/{doc_id}/structure", params={"doc_type": "invoice", "provider": "nope", "ocr_engine": "mock"}
        )
        assert resp.status_code == 400, resp.text
        assert "Unknown structuring provider" in resp.json()["detail"]


def test_structure_missing_document_404():
    with TestClient(app) as client:
        assert (
            client.post(
                "/documents/missing/structure", params={"doc_type": "invoice", "provider": "mock", "ocr_engine": "mock"}
            ).status_code
            == 404
        )
        assert client.get("/documents/missing/structure").status_code == 404


def test_char_to_page_helper():
    """Joiner-aware page mapping over a synthetic two-page OCR result."""
    ocr = OCRResult(
        document_id="x",
        status=DocumentStatus.ocr_done,
        engine_name="mock",
        engine_version="1",
        device="cpu",
        full_text="AAAA\n\nBBB",
        pages=[
            OCRPage(page=1, text="AAAA", blocks=[], tables=[]),
            OCRPage(page=2, text="BBB", blocks=[], tables=[]),
        ],
    )
    offsets = build_page_offsets(ocr)
    assert offsets == [(1, 0), (2, 6)]
    assert char_to_page(offsets, 0) == 1
    assert char_to_page(offsets, 3) == 1
    assert char_to_page(offsets, 4) == 1  # inside the "\n\n" gap -> preceding page
    assert char_to_page(offsets, 6) == 2
    assert char_to_page(offsets, 8) == 2
    assert char_to_page(offsets, None) is None
