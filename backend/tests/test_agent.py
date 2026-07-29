"""Phase 5 decision tests. Use the offline mock provider — no openai dep.

The mock provider always "approves", so the route/unit tests below prove the
deterministic code rules reconcile with — and override — the LLM judgment.
"""

from fastapi.testclient import TestClient

from app.models import Document, DocType, DocumentStatus
from app.pipeline.agent import _reconcile, run_decision
from app.rules import DecisionContext
from app.schemas import Check, StructuredResult

from .conftest import SAMPLES
from app.main import app


# --- reconcile precedence -----------------------------------------------------


def _review_check(passed: bool) -> Check:
    return Check(name="extraction_confidence", passed=passed, detail="", severity="review")


def test_review_gate_caps_llm_flag_at_needs_review():
    """A failed review gate (e.g. low confidence) must cap an LLM 'flag' at needs_review —
    untrustworthy data can't produce a confident flag without a hard rule."""
    decision, _conf, _reasons = _reconcile(
        [_review_check(passed=False)], "flag", 0.8, [], extraction_confidence=0.0
    )
    assert decision == "needs_review"


def test_llm_flag_stands_when_no_gate_fails():
    decision, _conf, _reasons = _reconcile(
        [_review_check(passed=True)], "flag", 0.8, [], extraction_confidence=0.9
    )
    assert decision == "flag"


def test_hard_failure_forces_flag_over_everything():
    hard = Check(name="total_math", passed=False, detail="", severity="hard")
    decision, conf, _ = _reconcile([hard], "approve", 0.9, [], extraction_confidence=0.2)
    assert decision == "flag"
    assert conf >= 0.9  # a certain hard failure floors confidence high


# --- helpers ------------------------------------------------------------------


def _upload(client: TestClient, name: str, doc_type: str | None = None) -> str:
    data = {"doc_type": doc_type} if doc_type else None
    with (SAMPLES / name).open("rb") as fh:
        resp = client.post("/documents", files={"file": (name, fh)}, data=data)
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


def _ocr(client: TestClient, doc_id: str) -> None:
    assert client.post(f"/documents/{doc_id}/ocr", params={"engine": "mock"}).status_code == 200


def _structure(client: TestClient, doc_id: str, doc_type: str = "invoice") -> None:
    resp = client.post(
        f"/documents/{doc_id}/structure",
        params={"doc_type": doc_type, "provider": "mock", "ocr_engine": "mock"},
    )
    assert resp.status_code == 200, resp.text


def fv(value, conf=0.9, page: int | None = 1) -> dict:
    """A FieldValue node as it appears in a dumped StructuredResult.fields."""
    grounding = (
        {"page": page, "char_start": 0, "char_end": 1, "snippet": str(value), "alignment": "exact"}
        if page is not None
        else None
    )
    return {"value": value, "confidence": conf, "grounding": grounding}


def _structured(fields: dict, doc_type: DocType, conf: float = 0.9) -> StructuredResult:
    return StructuredResult(
        document_id="t",
        status=DocumentStatus.structured,
        doc_type=doc_type,
        provider="mock",
        model="mock",
        ocr_engine="mock",
        fields=fields,
        extraction_confidence=conf,
    )


def _doc(doc_type: DocType) -> Document:
    return Document(filename="t.pdf", mime="application/pdf", doc_type=doc_type)


# --- route tests --------------------------------------------------------------


def test_decide_route_approves_clean_invoice():
    with TestClient(app) as client:
        doc_id = _upload(client, "invoice-clean.pdf")
        _ocr(client, doc_id)
        _structure(client, doc_id)

        post = client.post(f"/documents/{doc_id}/decide", params={"provider": "mock"})
        assert post.status_code == 200, post.text
        result = post.json()
        assert result["decision"] == "approve"
        assert result["status"] == "decided"
        assert result["provider"] == "mock"
        assert result["checks"], "expected a rule-by-rule check trace"
        assert result["citations"], "expected at least one field citation"
        assert 0.0 <= result["confidence"] <= 1.0

        detail = client.get(f"/documents/{doc_id}").json()
        assert detail["status"] == "decided"


def test_decide_get_refetch():
    with TestClient(app) as client:
        doc_id = _upload(client, "invoice-clean.pdf")
        _ocr(client, doc_id)
        _structure(client, doc_id)
        post = client.post(f"/documents/{doc_id}/decide", params={"provider": "mock"}).json()

        got = client.get(f"/documents/{doc_id}/decide")
        assert got.status_code == 200, got.text
        assert got.json()["decision"] == post["decision"]
        assert got.json()["checks"] == post["checks"]


def test_decide_requires_structure_409():
    with TestClient(app) as client:
        doc_id = _upload(client, "invoice-clean.pdf")
        _ocr(client, doc_id)  # structure deliberately skipped
        resp = client.post(f"/documents/{doc_id}/decide", params={"provider": "mock"})
        assert resp.status_code == 409, resp.text


def test_decide_unknown_provider_400():
    with TestClient(app) as client:
        doc_id = _upload(client, "invoice-clean.pdf")
        _ocr(client, doc_id)
        _structure(client, doc_id)
        resp = client.post(f"/documents/{doc_id}/decide", params={"provider": "nope"})
        assert resp.status_code == 400, resp.text
        assert "Unknown decision provider" in resp.json()["detail"]


def test_decide_missing_document_404():
    with TestClient(app) as client:
        assert client.post("/documents/missing/decide", params={"provider": "mock"}).status_code == 404
        assert client.get("/documents/missing/decide").status_code == 404


# --- unit tests: code rules override the mock "approve" -----------------------


def test_total_mismatch_forces_flag():
    fields = {"total": fv(200.0), "subtotal": fv(100.0), "tax": fv(10.0), "invoice_no": fv("INV-9")}
    ctx = DecisionContext(extraction_confidence=0.9)
    result = run_decision(_doc(DocType.invoice), _structured(fields, DocType.invoice), ctx, "mock")

    assert result.decision == "flag"
    math = next(c for c in result.checks if c.name == "total_math")
    assert not math.passed and math.severity == "hard"
    assert result.confidence >= 0.9
    assert result.llm_decision == "approve"  # mock approved; code overrode it


def test_low_extraction_confidence_caps_at_needs_review():
    fields = {"total": fv(100.0), "subtotal": fv(90.0), "tax": fv(10.0), "invoice_no": fv("INV-1")}
    ctx = DecisionContext(extraction_confidence=0.3)  # below the warn threshold
    result = run_decision(_doc(DocType.invoice), _structured(fields, DocType.invoice, 0.3), ctx, "mock")

    assert result.decision == "needs_review"
    gate = next(c for c in result.checks if c.name == "extraction_confidence")
    assert not gate.passed


def test_prescan_warn_caps_at_needs_review():
    fields = {"total": fv(100.0), "subtotal": fv(90.0), "tax": fv(10.0), "invoice_no": fv("INV-2")}
    ctx = DecisionContext(extraction_confidence=0.9, prescan_verdict="warn")
    result = run_decision(_doc(DocType.invoice), _structured(fields, DocType.invoice), ctx, "mock")

    assert result.decision == "needs_review"
    gate = next(c for c in result.checks if c.name == "prescan_quality")
    assert not gate.passed


def test_duplicate_invoice_no_forces_flag():
    fields = {"invoice_no": fv("INV-1"), "total": fv(50.0)}
    ctx = DecisionContext(extraction_confidence=0.9, prior_invoice_numbers={"INV-1"})
    result = run_decision(_doc(DocType.invoice), _structured(fields, DocType.invoice), ctx, "mock")

    assert result.decision == "flag"
    dup = next(c for c in result.checks if c.name == "duplicate_invoice_no")
    assert not dup.passed and dup.severity == "hard"


def test_contract_missing_signatures_forces_flag():
    fields = {
        "signatures_present": fv(False, conf=0.0, page=None),
        "governing_law": fv("Delaware"),
    }
    ctx = DecisionContext(extraction_confidence=0.9)
    result = run_decision(_doc(DocType.contract), _structured(fields, DocType.contract), ctx, "mock")

    assert result.decision == "flag"
    sig = next(c for c in result.checks if c.name == "signatures_present")
    assert not sig.passed and sig.severity == "hard"
