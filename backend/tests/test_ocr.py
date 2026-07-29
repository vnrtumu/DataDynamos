"""Phase 3 OCR layer tests. Use the offline mock engine — no heavy ML deps."""

from fastapi.testclient import TestClient

from app.main import app
from app.models import Document
from app.pipeline.ocr import run_ocr
from app.pipeline.ocr.mock import MockEngine

from .conftest import SAMPLES


def _upload(client: TestClient, name: str) -> str:
    with (SAMPLES / name).open("rb") as fh:
        resp = client.post("/documents", files={"file": (name, fh)})
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


def test_ocr_route_persists_and_advances_status():
    with TestClient(app) as client:
        doc_id = _upload(client, "invoice-clean.pdf")

        post = client.post(f"/documents/{doc_id}/ocr", params={"engine": "mock"})
        assert post.status_code == 200, post.text
        result = post.json()
        assert result["engine_name"] == "mock"
        assert result["status"] == "ocr_done"
        assert len(result["pages"]) >= 1
        assert result["full_text"]
        assert isinstance(result["latency_ms"], int)
        assert result["table_count"] >= 1

        # Document status advanced.
        detail = client.get(f"/documents/{doc_id}").json()
        assert detail["status"] == "ocr_done"

        # GET returns the persisted result without recompute.
        got = client.get(f"/documents/{doc_id}/ocr", params={"engine": "mock"}).json()
        assert got["engine_name"] == "mock"
        assert got["full_text"] == result["full_text"]


def test_ocr_unknown_engine_returns_400():
    with TestClient(app) as client:
        doc_id = _upload(client, "invoice-clean.pdf")
        resp = client.post(f"/documents/{doc_id}/ocr", params={"engine": "nope"})
        assert resp.status_code == 400, resp.text
        assert "Unknown OCR engine" in resp.json()["detail"]


def test_ocr_missing_document_returns_404():
    with TestClient(app) as client:
        assert client.post("/documents/missing/ocr", params={"engine": "mock"}).status_code == 404
        assert client.get("/documents/missing/ocr", params={"engine": "mock"}).status_code == 404


def test_get_ocr_before_run_returns_404():
    with TestClient(app) as client:
        doc_id = _upload(client, "invoice-clean.pdf")
        assert client.get(f"/documents/{doc_id}/ocr", params={"engine": "mock"}).status_code == 404


def test_base_aggregates_pages_offline():
    """MockEngine.run reads no files, so aggregation is testable in isolation."""
    doc = Document(id="agg-test", filename="x.pdf", mime="application/pdf", page_count=2)
    result = run_ocr(doc, "mock")

    assert result.engine_name == "mock"
    assert len(result.pages) == 2
    # Two blocks/page at 0.97 and 0.92 -> mean 0.945; well above the warn floor.
    assert result.avg_confidence == 0.945
    assert all(p.avg_confidence == 0.945 for p in result.pages)
    assert result.table_count == 2
    assert "page 1" in result.full_text and "page 2" in result.full_text
    assert not any("low average" in w for w in result.warnings)
    assert isinstance(MockEngine().version, str)
