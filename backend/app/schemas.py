"""API response models (decoupled from the ORM tables)."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel

from app.models import DocType, DocumentStatus


class DocumentSummary(BaseModel):
    """Compact shape for the list view."""

    id: str
    filename: str
    doc_type: DocType | None
    mime: str
    page_count: int
    status: DocumentStatus
    created_at: datetime


class PageInfo(BaseModel):
    """One rasterized page + its preview, addressed via the /files static mount."""

    page: int
    image_url: str
    thumbnail_url: str


class DocumentDetail(DocumentSummary):
    """List fields plus per-page image/thumbnail URLs."""

    pages: list[PageInfo]


# --- Phase 2: pre-flight / quality metrics -----------------------------------

# Advisory only at this stage; the pipeline never hard-fails here.
Verdict = Literal["pass", "warn"]


class MetricResult(BaseModel):
    """One pre-flight metric: its measured value, verdict, and the threshold used."""

    value: float
    verdict: Verdict
    threshold: float | None = None


class PageQuality(BaseModel):
    """Pre-flight metrics + optional cleaned-image URLs for a single page."""

    page: int
    width_px: int
    height_px: int
    resolution: MetricResult  # value = effective DPI
    sharpness: MetricResult  # value = variance of Laplacian
    contrast: MetricResult  # value = pixel std
    brightness: MetricResult  # value = pixel mean
    skew_angle_deg: float
    verdict: Verdict  # worst metric on this page
    reasons: list[str]  # human-readable notes for non-pass metrics
    deskewed: bool = False
    image_url: str  # raw rasterized page
    deskewed_url: str | None = None
    gray_url: str | None = None
    thresh_url: str | None = None


class QualityReport(BaseModel):
    """Document-level pre-flight result, persisted on the pipeline run."""

    document_id: str
    status: DocumentStatus  # always `prescanned` at this stage
    verdict: Verdict  # worst page verdict
    reasons: list[str]  # aggregated, page-prefixed, deduped
    preprocess_applied: bool
    pages: list[PageQuality]


# --- Phase 3: OCR engine layer ------------------------------------------------

# Pixel-space box on the source page, [x0, y0, x1, y1] (top-left origin).
BBox = tuple[float, float, float, float]


class OCRBlock(BaseModel):
    """One recognized region: text + its location + (optional) confidence."""

    page: int
    text: str
    bbox: BBox
    confidence: float | None = None  # 0-1; None when the engine doesn't expose it
    label: str = "text"  # text | table | title | figure | formula | seal | ...


class OCRTable(BaseModel):
    """A detected table, captured as markdown (engines that expose structure)."""

    page: int
    bbox: BBox | None = None
    n_rows: int = 0
    n_cols: int = 0
    markdown: str = ""
    confidence: float | None = None


class OCRPage(BaseModel):
    """Per-page OCR output, normalized across engines."""

    page: int
    text: str
    blocks: list[OCRBlock]
    tables: list[OCRTable]
    avg_confidence: float | None = None  # mean over blocks that report confidence
    char_count: int = 0
    markdown_url: str | None = None  # /files URL for the saved page markdown, if any


class OCRResult(BaseModel):
    """Document-level OCR result, persisted on the run keyed by engine name."""

    document_id: str
    status: DocumentStatus  # `ocr_done` at this stage
    engine_name: str
    engine_version: str
    device: str
    full_text: str
    pages: list[OCRPage]
    avg_confidence: float | None = None  # document-wide mean of per-block confidence
    table_count: int = 0
    latency_ms: int = 0
    warnings: list[str] = []  # seals noted, low confidence, no-table-support, etc.


# --- Phase 4: structuring / extraction ----------------------------------------

# Where a field came from. Char offsets index into OCRResult.full_text (the text
# handed to the extractor); `page` is the 1-based page that offset falls on.
Alignment = Literal["exact", "partial", "ungrounded"]


class Grounding(BaseModel):
    """Source location for one extracted field, for the hover-to-highlight UI."""

    page: int | None = None  # None when the span couldn't be located in the source
    char_start: int | None = None
    char_end: int | None = None
    snippet: str | None = None  # the matched source substring (the verbatim span)
    alignment: Alignment | None = None


class FieldValue(BaseModel):
    """A single extracted field: its value, confidence, and source grounding.

    A missing field is an explicit ``value=None`` with low confidence — never a
    hallucinated value (cross-cutting checklist).
    """

    value: str | float | int | bool | None = None
    confidence: float = 0.0  # 0-1; alignment quality x propagated OCR confidence
    grounding: Grounding | None = None


class StructuredResult(BaseModel):
    """Document-level structuring result, persisted under stage_results["structure"]."""

    document_id: str
    status: DocumentStatus  # `structured` at this stage
    doc_type: DocType
    provider: str  # "langextract" | "mock"
    model: str  # extractor model slug (or "mock")
    ocr_engine: str  # which OCR result this was built from
    fields: dict  # validated InvoiceFields/ContractFields, dumped to JSON
    extraction_confidence: float  # overall 0-1 (mean over the doc type's core fields)
    grounding_map: dict[str, Grounding] = {}  # flat field path -> grounding, for the UI
    warnings: list[str] = []
    latency_ms: int = 0
    fallback_used: bool = False  # True if the Docling table backfill filled a field
    raw_artifact_url: str | None = None  # /files URL to the saved extractor output


# --- Phase 5: agent decision -------------------------------------------------

# The agent verdict. `flag` = a rule definitively failed; `needs_review` = can't
# confidently auto-approve (low confidence / poor scan / over threshold).
Decision = Literal["approve", "flag", "needs_review"]
# How a failed check steers the decision (see app/rules + the reconcile step):
# hard -> forces `flag`; review -> caps at `needs_review`; advisory -> note only.
Severity = Literal["hard", "review", "advisory"]


class Check(BaseModel):
    """One deterministic business-rule outcome, surfaced as the decision trace."""

    name: str
    passed: bool
    detail: str  # human-readable, e.g. "total 135.00 = subtotal 125.00 + tax 10.00"
    severity: Severity


class Citation(BaseModel):
    """Ties a decision-relevant field back to its source location."""

    field: str  # dotted field path, e.g. "total"
    source: str  # e.g. "page 1"


class DecisionResult(BaseModel):
    """Document-level decision, persisted under stage_results["decide"]."""

    document_id: str
    status: DocumentStatus  # `decided` (approve/flag) | `needs_review`
    doc_type: DocType
    provider: str  # "llm" | "mock"
    model: str  # decision model slug (or "mock")
    decision: Decision
    confidence: float  # 0-1
    reasons: list[str]  # human-readable bullets (LLM judgment + any code-forced reason)
    checks: list[Check]  # authoritative, code-computed rule-by-rule trace
    citations: list[Citation] = []  # built from the structured grounding_map
    llm_decision: Decision | None = None  # what the LLM proposed before reconciliation
    warnings: list[str] = []
    latency_ms: int = 0
