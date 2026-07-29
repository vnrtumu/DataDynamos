"""Pipeline stage endpoints. Phase 2: pre-flight / preprocessing.

Per-document stage actions live here (OCR / structure / decide land in later
phases). Each call reuses the document's latest ``PipelineRun`` and overwrites the
relevant stage entry, so re-running live on camera doesn't pile up rows.
"""

import asyncio
from typing import Callable, TypeVar

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select

from app.config import settings
from app.db import get_session
from app.models import Document, DocType, DocumentStatus, PipelineRun, _utcnow
from app.pipeline.agent import run_decision
from app.pipeline.ocr import run_ocr
from app.pipeline.prescan import run_prescan
from app.pipeline.structuring import run_structuring
from app.rules import DecisionContext
from app.schemas import DecisionResult, OCRResult, QualityReport, StructuredResult

router = APIRouter(prefix="/documents/{doc_id}", tags=["pipeline"])

_T = TypeVar("_T")


async def _run_stage(stage: str, timeout: float, fn: Callable[..., _T], *args, **kwargs) -> _T:
    """Run a blocking pipeline stage off the event loop, with a timeout.

    The prescan/OCR/structure/decide functions are heavy + synchronous (OpenCV,
    Docling, network VLM/LLM calls). Calling them directly in an ``async`` route
    blocks the whole event loop — the server freezes for every other request until the
    stage finishes (we saw a multi-minute freeze on a cold OCR). ``asyncio.to_thread``
    moves the work to a worker thread; ``wait_for`` turns a hung stage into a clean 504
    instead of an indefinite hang. ``ValueError`` (e.g. a missing optional dep) still
    maps to 400.
    """
    try:
        return await asyncio.wait_for(
            asyncio.to_thread(fn, *args, **kwargs), timeout=timeout
        )
    except asyncio.TimeoutError:
        raise HTTPException(
            status_code=504,
            detail=f"{stage} stage timed out after {timeout:.0f}s.",
        ) from None
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


def _latest_run(session: Session, doc_id: str) -> PipelineRun | None:
    """Return the newest pipeline run for the document, or ``None`` if there are none."""
    return session.exec(
        select(PipelineRun)
        .where(PipelineRun.document_id == doc_id)
        .order_by(PipelineRun.created_at.desc())
    ).first()


def get_or_create_run(session: Session, doc_id: str) -> PipelineRun:
    """Return the newest pipeline run for the document, creating one if none exist."""
    run = _latest_run(session, doc_id)
    if run is None:
        run = PipelineRun(document_id=doc_id)
        session.add(run)
        session.commit()
        session.refresh(run)
    return run


def _save_stage(
    session: Session,
    run: PipelineRun,
    doc: Document,
    stage_key: str,
    payload: object,
    run_status: str,
    doc_status: DocumentStatus,
) -> None:
    """Persist one stage's result onto the run and advance both statuses.

    A fresh dict is assigned (rather than mutating in place) so SQLAlchemy detects the
    change on the JSON column.
    """
    run.stage_results = {**run.stage_results, stage_key: payload}
    run.status = run_status
    run.updated_at = _utcnow()
    doc.status = doc_status
    session.add(run)
    session.add(doc)
    session.commit()


@router.post("/prescan", response_model=QualityReport)
async def prescan_document(
    doc_id: str,
    deskew: bool = True,
    clean: bool = False,
    session: Session = Depends(get_session),
) -> QualityReport:
    """Run the advisory pre-flight pass and write any cleaned page variants.

    Always advances the document to ``prescanned`` — quality here is advisory; the
    authoritative ``needs_review`` verdict comes from OCR/extraction confidence later.
    """
    doc = session.get(Document, doc_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="Document not found.")
    if doc.page_count == 0:
        raise HTTPException(status_code=409, detail="Document has no rasterized pages.")

    report = await _run_stage(
        "Prescan", settings.prescan_timeout_s, run_prescan, doc, deskew=deskew, clean=clean
    )

    run = get_or_create_run(session, doc_id)
    _save_stage(
        session, run, doc, "prescan", report.model_dump(mode="json"),
        "prescanned", DocumentStatus.prescanned,
    )
    return report


@router.get("/prescan", response_model=QualityReport)
def get_prescan(doc_id: str, session: Session = Depends(get_session)) -> QualityReport:
    """Return the persisted pre-flight report without recomputing it."""
    doc = session.get(Document, doc_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="Document not found.")

    run = _latest_run(session, doc_id)
    prescan = run.stage_results.get("prescan") if run else None
    if not prescan:
        raise HTTPException(status_code=404, detail="No pre-flight result for this document.")
    return QualityReport(**prescan)


@router.post("/ocr", response_model=OCRResult)
async def ocr_document(
    doc_id: str,
    engine: str = Query(default=""),
    session: Session = Depends(get_session),
) -> OCRResult:
    """Run a swappable OCR engine over the document's pages and persist the result.

    Results are stored under ``stage_results["ocr"][<engine>]`` so multiple engines'
    output coexists for the side-by-side comparison view; re-running an engine
    overwrites just that engine's entry.
    """
    engine = engine or settings.ocr_default_engine

    doc = session.get(Document, doc_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="Document not found.")
    if doc.page_count == 0:
        raise HTTPException(status_code=409, detail="Document has no rasterized pages.")

    result = await _run_stage("OCR", settings.ocr_timeout_s, run_ocr, doc, engine)

    run = get_or_create_run(session, doc_id)
    existing_ocr = dict(run.stage_results.get("ocr") or {})
    existing_ocr[engine] = result.model_dump(mode="json")
    _save_stage(session, run, doc, "ocr", existing_ocr, "ocr_done", DocumentStatus.ocr_done)
    return result


@router.get("/ocr", response_model=OCRResult)
def get_ocr(
    doc_id: str,
    engine: str = Query(default=""),
    session: Session = Depends(get_session),
) -> OCRResult:
    """Return a persisted OCR result for the given engine without recomputing it."""
    engine = engine or settings.ocr_default_engine

    doc = session.get(Document, doc_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="Document not found.")

    run = _latest_run(session, doc_id)
    ocr = (run.stage_results.get("ocr") or {}) if run else {}
    result = ocr.get(engine)
    if not result:
        raise HTTPException(
            status_code=404, detail=f"No OCR result for engine '{engine}' on this document."
        )
    return OCRResult(**result)


@router.post("/structure", response_model=StructuredResult)
async def structure_document(
    doc_id: str,
    doc_type: DocType | None = Query(default=None),
    provider: str = Query(default=""),
    ocr_engine: str = Query(default=""),
    session: Session = Depends(get_session),
) -> StructuredResult:
    """Structure a document's OCR text into validated, grounded JSON and persist it.

    Reads the OCR result for ``ocr_engine`` (default ``OCR_DEFAULT_ENGINE``) — run OCR
    first. The result is stored under ``stage_results["structure"]`` (one object).
    """
    ocr_engine = ocr_engine or settings.ocr_default_engine

    doc = session.get(Document, doc_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="Document not found.")

    resolved_type = doc_type or doc.doc_type
    if resolved_type is None:
        raise HTTPException(
            status_code=400,
            detail="doc_type is required (not set on the document); pass ?doc_type=invoice|contract.",
        )

    run = _latest_run(session, doc_id)
    ocr = (run.stage_results.get("ocr") or {}) if run else {}
    ocr_data = ocr.get(ocr_engine)
    if not ocr_data:
        raise HTTPException(
            status_code=409,
            detail=f"Run OCR (engine '{ocr_engine}') before structuring this document.",
        )
    ocr_result = OCRResult(**ocr_data)

    result = await _run_stage(
        "Structuring", settings.llm_timeout_s, run_structuring, doc, ocr_result, resolved_type, provider
    )

    # ``run`` is non-None here: an OCR result was found above, which requires a run.
    _save_stage(
        session, run, doc, "structure", result.model_dump(mode="json"),
        "structured", DocumentStatus.structured,
    )
    return result


@router.get("/structure", response_model=StructuredResult)
def get_structure(doc_id: str, session: Session = Depends(get_session)) -> StructuredResult:
    """Return the persisted structuring result without recomputing it."""
    doc = session.get(Document, doc_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="Document not found.")

    run = _latest_run(session, doc_id)
    structure = run.stage_results.get("structure") if run else None
    if not structure:
        raise HTTPException(status_code=404, detail="No structuring result for this document.")
    return StructuredResult(**structure)


def _prior_invoice_numbers(session: Session, exclude_doc_id: str) -> set[str]:
    """Invoice numbers seen on OTHER documents that were already decided.

    Only decided runs count: an in-progress or abandoned upload shouldn't make a
    later, legitimate invoice look like a duplicate — a duplicate is a hard flag, and
    a hard flag can't be overridden downstream.
    """
    seen: set[str] = set()
    runs = session.exec(select(PipelineRun).where(PipelineRun.document_id != exclude_doc_id)).all()
    for run in runs:
        if "decide" not in run.stage_results:
            continue
        structure = run.stage_results.get("structure") or {}
        node = (structure.get("fields") or {}).get("invoice_no") or {}
        value = node.get("value")
        if value is not None:
            seen.add(str(value))
    return seen


@router.post("/decide", response_model=DecisionResult)
async def decide_document(
    doc_id: str,
    provider: str = Query(default=""),
    session: Session = Depends(get_session),
) -> DecisionResult:
    """Decide a structured document (approve | flag | needs_review) and persist it.

    Reads ``stage_results["structure"]`` (run structuring first) and the optional
    ``stage_results["prescan"]`` verdict. Deterministic rules run in code; the LLM
    only adds judgment it can't use to override a hard-failed rule.
    """
    doc = session.get(Document, doc_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="Document not found.")

    run = _latest_run(session, doc_id)
    structure = run.stage_results.get("structure") if run else None
    if not structure:
        raise HTTPException(status_code=409, detail="Run structuring before deciding this document.")
    structured = StructuredResult(**structure)

    prescan = (run.stage_results.get("prescan") or {}) if run else {}
    ctx = DecisionContext(
        extraction_confidence=structured.extraction_confidence,
        prescan_verdict=prescan.get("verdict"),
        prescan_reasons=list(prescan.get("reasons") or []),
        prior_invoice_numbers=_prior_invoice_numbers(session, doc_id),
    )

    result = await _run_stage(
        "Decision", settings.llm_timeout_s, run_decision, doc, structured, ctx, provider
    )

    # ``run`` is non-None here: a structure result was found above, which requires a run.
    _save_stage(
        session, run, doc, "decide", result.model_dump(mode="json"),
        result.status.value, result.status,
    )
    return result


@router.get("/decide", response_model=DecisionResult)
def get_decision(doc_id: str, session: Session = Depends(get_session)) -> DecisionResult:
    """Return the persisted decision without recomputing it."""
    doc = session.get(Document, doc_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="Document not found.")

    run = _latest_run(session, doc_id)
    decide = run.stage_results.get("decide") if run else None
    if not decide:
        raise HTTPException(status_code=404, detail="No decision for this document.")
    return DecisionResult(**decide)
