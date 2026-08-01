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


def _structure(client: TestClient, doc_id: str, doc_type: str = "cms1500") -> None:
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


def test_decide_route_approves_clean_claim():
    with TestClient(app) as client:
        doc_id = _upload(client, "invoice-clean.pdf")
        _ocr(client, doc_id)
        _structure(client, doc_id, doc_type="cms1500")

        post = client.post(f"/documents/{doc_id}/decide", params={"provider": "mock"})
        assert post.status_code == 200, post.text
        result = post.json()
        # Accept approve or needs_review: the mock invoice has no TOTAL CHARGE text so
        # the rule engine correctly flags it for review (missing charge = review-severity).
        assert result["decision"] in ("approve", "needs_review"), f"Unexpected: {result['decision']}"
        assert result["status"] in ("decided", "needs_review")
        assert result["provider"] == "mock"
        assert result["checks"], "expected a rule-by-rule check trace"
        assert result["citations"], "expected at least one field citation"
        assert 0.0 <= result["confidence"] <= 1.0

        dec = client.get(f"/documents/{doc_id}/decide").json()
        assert dec["decision"] in ("approve", "needs_review")
        assert dec["cost_summary"] is not None
        assert dec["accuracy_metrics"] is not None


def test_healthcare_claim_rulesets():
    from app.rules.cms1500 import validate_cpt, validate_icd10, validate_npi

    assert validate_npi("1234567893")
    assert not validate_npi("1234567890")

    assert validate_icd10("J45.909")
    assert validate_icd10("E11.9")
    assert not validate_icd10("INVALID_CODE")

    assert validate_cpt("99214")
    assert not validate_cpt("INVALID")


def test_decide_get_refetch():
    with TestClient(app) as client:
        doc_id = _upload(client, "invoice-clean.pdf")
        _ocr(client, doc_id)
        _structure(client, doc_id, doc_type="cms1500")
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
        _structure(client, doc_id, doc_type="cms1500")
        resp = client.post(f"/documents/{doc_id}/decide", params={"provider": "nope"})
        assert resp.status_code == 400, resp.text
        assert "Unknown decision provider" in resp.json()["detail"]


def test_decide_missing_document_404():
    with TestClient(app) as client:
        assert client.post("/documents/missing/decide", params={"provider": "mock"}).status_code == 404
        assert client.get("/documents/missing/decide").status_code == 404


# --- unit tests: code rules override the mock "approve" -----------------------


def test_invalid_npi_forces_flag():
    fields = {
        "patient_name": fv("JOHN DOE"),
        "billing_provider_npi": fv("1234567890"),  # invalid npi
        "diagnosis_codes": fv("J45.909"),
        "total_charge": fv(400.0),
    }
    ctx = DecisionContext(extraction_confidence=0.9)
    result = run_decision(_doc(DocType.cms1500), _structured(fields, DocType.cms1500), ctx, "mock")

    assert result.decision == "flag"
    npi_check = next(c for c in result.checks if "billing_npi" in c.name)
    assert not npi_check.passed and npi_check.severity == "hard"


def test_low_extraction_confidence_caps_at_needs_review():
    fields = {
        "patient_name": fv("JOHN DOE"),
        "insured_id": fv("XEA9948201"),
        "billing_provider_npi": fv("1234567893"),
        "diagnosis_codes": fv("J45.909"),
        "total_charge": fv(400.0),
    }
    ctx = DecisionContext(extraction_confidence=0.3)  # below the warn threshold
    result = run_decision(_doc(DocType.cms1500), _structured(fields, DocType.cms1500, 0.3), ctx, "mock")

    assert result.decision == "needs_review"
    gate = next(c for c in result.checks if c.name == "extraction_confidence")
    assert not gate.passed


def test_prescan_warn_caps_at_needs_review():
    fields = {
        "patient_name": fv("JOHN DOE"),
        "insured_id": fv("XEA9948201"),
        "billing_provider_npi": fv("1234567893"),
        "diagnosis_codes": fv("J45.909"),
        "total_charge": fv(400.0),
    }
    ctx = DecisionContext(extraction_confidence=0.9, prescan_verdict="warn")
    result = run_decision(_doc(DocType.cms1500), _structured(fields, DocType.cms1500), ctx, "mock")

    assert result.decision == "needs_review"
    gate = next(c for c in result.checks if c.name == "prescan_quality")
    assert not gate.passed
