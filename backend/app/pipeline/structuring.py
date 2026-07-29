"""Phase 4 structuring stage: OCR text -> validated, grounded, approval-relevant JSON.

Two providers behind one entrypoint, mirroring the OCR layer's discipline:

* ``langextract`` — LangExtract pointed at OpenRouter (OpenAI-compatible). Imported
  lazily so the app boots and tests run without the optional dep.
* ``mock`` — deterministic, offline; its spans are located in the real OCR
  ``full_text`` so grounding + page mapping are genuinely exercised in tests.

Source grounding, per-field + overall confidence (with OCR confidence propagated),
and a documented Docling-table fallback live here; the per-doc-type taxonomy and
assembly live in ``app/extraction``.
"""

from __future__ import annotations

import json
from time import perf_counter

from app.config import settings
from app.extraction import get_spec
from app.extraction.base import FlatExtraction, GroundingCtx
from app.models import Document, DocType, DocumentStatus
from app.schemas import FieldValue, Grounding, OCRResult, StructuredResult
from app import storage

PROVIDERS = {"langextract", "mock"}


def run_structuring(
    doc: Document,
    ocr_result: OCRResult,
    doc_type: DocType,
    provider: str = "",
) -> StructuredResult:
    """Structure a document's OCR text into a validated, grounded result."""
    provider = provider or settings.structuring_provider
    if provider not in PROVIDERS:
        raise ValueError(
            f"Unknown structuring provider '{provider}'. Available: {', '.join(sorted(PROVIDERS))}"
        )

    spec = get_spec(doc_type)
    ctx = GroundingCtx(full_text=ocr_result.full_text, ocr_result=ocr_result)

    start = perf_counter()
    if provider == "mock":
        flats = _structure_mock(doc_type, ocr_result.full_text)
        artifact: str | None = None
        model = "mock"
    else:
        flats, artifact = _structure_langextract(spec, ocr_result.full_text)
        model = settings.structuring_model
    latency_ms = int((perf_counter() - start) * 1000)

    fields_model = spec.assemble(flats, ctx)

    # Optional fallback: backfill missing core fields from persisted Docling tables.
    fields_model, fallback_used = _backfill_from_tables(fields_model, ocr_result, doc_type, ctx)

    fields = fields_model.model_dump(mode="json")
    extraction_confidence = _overall_confidence(fields, spec.core_paths)
    grounding_map = _flatten_grounding(fields)

    warnings = list(ctx.warnings)
    if ocr_result.avg_confidence is None:
        warnings.append(
            f"OCR engine '{ocr_result.engine_name}' exposes no confidence; "
            "field confidence is alignment-only"
        )
    if extraction_confidence < settings.extraction_confidence_warn:
        warnings.append(f"low overall extraction confidence ({extraction_confidence:.2f})")

    raw_artifact_url: str | None = None
    if artifact is not None:
        storage.save_structure_artifact(doc.id, artifact)
        raw_artifact_url = storage.structure_artifact_url(doc.id)

    return StructuredResult(
        document_id=doc.id,
        status=DocumentStatus.structured,
        doc_type=doc_type,
        provider=provider,
        model=model,
        ocr_engine=ocr_result.engine_name,
        fields=fields,
        extraction_confidence=extraction_confidence,
        grounding_map=grounding_map,
        warnings=warnings,
        latency_ms=latency_ms,
        fallback_used=fallback_used,
        raw_artifact_url=raw_artifact_url,
    )


# --- providers ----------------------------------------------------------------


def _structure_langextract(spec, full_text: str) -> tuple[list[FlatExtraction], str]:
    """Run LangExtract against OpenRouter and normalize to FlatExtraction[]."""
    if not settings.openrouter_api_key:
        raise ValueError("OPENROUTER_API_KEY is not set; the langextract provider needs it.")

    import langextract as lx  # lazy: optional dep
    from langextract.factory import ModelConfig

    config = ModelConfig(
        model_id=settings.structuring_model,
        provider="openai",
        provider_kwargs={
            "api_key": settings.openrouter_api_key,
            "base_url": settings.structuring_base_url,
        },
    )
    annotated = lx.extract(
        text_or_documents=full_text,
        prompt_description=spec.prompt,
        examples=spec.examples_factory(),
        config=config,
        max_char_buffer=settings.structuring_max_char_buffer,
        extraction_passes=settings.structuring_extraction_passes,
    )

    flats: list[FlatExtraction] = []
    for e in annotated.extractions:
        interval = getattr(e, "char_interval", None)
        cs = getattr(interval, "start_pos", None) if interval is not None else None
        ce = getattr(interval, "end_pos", None) if interval is not None else None
        flats.append(
            FlatExtraction(
                cls=e.extraction_class,
                text=e.extraction_text or "",
                attributes=dict(getattr(e, "attributes", None) or {}),
                char_start=cs,
                char_end=ce,
            )
        )
    return flats, _artifact_jsonl(flats)


def _structure_mock(doc_type: DocType, full_text: str) -> list[FlatExtraction]:
    """Deterministic, offline extractions whose spans live in the mock OCR text.

    For invoices: grounds vendor/invoice_no/total/line_item against the real
    ``full_text`` (so page mapping runs for real), emits an intentionally ungrounded
    ``currency``, and OMITS ``po_number`` to prove the null + low-confidence path.
    """
    if doc_type == DocType.invoice:
        return [
            FlatExtraction(cls="vendor", text="MOCK INVOICE"),
            FlatExtraction(cls="invoice_no", text="page 1"),
            FlatExtraction(cls="total", text="$1,234.56"),
            FlatExtraction(cls="currency", text="USD"),  # absent in OCR text -> ungrounded
            FlatExtraction(
                cls="line_item",
                text="$1,234.56",
                attributes={
                    "desc": "Mock Widget",
                    "qty": "1",
                    "unit_price": "1234.56",
                    "amount": "1234.56",
                },
            ),
            # po_number deliberately omitted.
        ]
    return [
        FlatExtraction(cls="party", text="MOCK INVOICE"),
        FlatExtraction(cls="effective_date", text="page 1"),
    ]


# --- confidence + grounding aggregation --------------------------------------


def _is_field_value(node: object) -> bool:
    return isinstance(node, dict) and set(node.keys()) == {"value", "confidence", "grounding"}


def _node_confidence(node: object) -> float | None:
    """Recursive confidence of a dumped field node (FieldValue / list / composite)."""
    if _is_field_value(node):
        return float(node["confidence"])  # type: ignore[index]
    if isinstance(node, list):
        vals = [c for c in (_node_confidence(x) for x in node) if c is not None]
        return sum(vals) / len(vals) if vals else 0.0  # empty list = missing -> drags down
    if isinstance(node, dict):
        vals = [c for c in (_node_confidence(v) for v in node.values()) if c is not None]
        return sum(vals) / len(vals) if vals else None
    return None


def _overall_confidence(fields: dict, core_paths: list[str]) -> float:
    """Mean confidence over the doc type's core fields (missing ones count as 0)."""
    confs: list[float] = []
    for path in core_paths:
        node = fields.get(path)
        c = _node_confidence(node)
        if c is not None:
            confs.append(c)
    return round(sum(confs) / len(confs), 4) if confs else 0.0


def _flatten_grounding(fields: dict, prefix: str = "", out: dict[str, Grounding] | None = None) -> dict[str, Grounding]:
    """Flatten every grounded field into dotted-path -> Grounding for the hover UI."""
    if out is None:
        out = {}
    if _is_field_value(fields):
        grounding = fields["grounding"]  # type: ignore[index]
        if grounding is not None:
            out[prefix] = Grounding(**grounding)
        return out
    if isinstance(fields, list):
        for i, item in enumerate(fields):
            _flatten_grounding(item, f"{prefix}.{i}" if prefix else str(i), out)
    elif isinstance(fields, dict):
        for key, value in fields.items():
            _flatten_grounding(value, f"{prefix}.{key}" if prefix else key, out)
    return out


# --- Docling table fallback (minimal, best-effort) ---------------------------

# Confidence cap for values recovered from a table row rather than the extractor.
_TABLE_BACKFILL_CONFIDENCE = 0.5


def _table_cell(value: str | None, grounding: Grounding) -> FieldValue:
    """A low-confidence ``FieldValue`` for a cell backfilled from a Docling table."""
    if value is None:
        return FieldValue(value=None, confidence=0.0, grounding=None)
    return FieldValue(value=value, confidence=_TABLE_BACKFILL_CONFIDENCE, grounding=grounding)


def _backfill_from_tables(fields_model, ocr_result: OCRResult, doc_type: DocType, ctx: GroundingCtx):
    """Backfill empty invoice line items from persisted Docling tables (no re-OCR).

    Reuses the OCR result's table markdown (present when the OCR engine was Docling).
    Filled fields get capped low confidence + ``partial`` alignment. No tables, or a
    non-invoice doc type, makes this a no-op so fields stay explicitly null.
    """
    if doc_type != DocType.invoice or fields_model.line_items:
        return fields_model, False

    tables = [t for page in ocr_result.pages for t in page.tables if t.markdown]
    if not tables:
        return fields_model, False

    from app.extraction.invoice import LineItem  # local import avoids an import cycle

    items = []
    for table in tables:
        for row in _parse_md_table(table.markdown):
            numbers = [c for c in row if _looks_numeric(c)]
            if not row or not numbers:
                continue
            grounding = Grounding(page=table.page, snippet=row[0], alignment="partial")
            items.append(
                LineItem(
                    desc=_table_cell(row[0], grounding),
                    qty=FieldValue(value=None, confidence=0.0, grounding=None),
                    unit_price=FieldValue(value=None, confidence=0.0, grounding=None),
                    amount=_table_cell(numbers[-1], grounding),
                )
            )

    if not items:
        return fields_model, False

    fields_model.line_items = items
    ctx.warnings.append(f"backfilled {len(items)} line item(s) from Docling tables (low confidence)")
    return fields_model, True


def _parse_md_table(markdown: str) -> list[list[str]]:
    """Parse a markdown table into rows of trimmed cells, skipping the separator row."""
    rows: list[list[str]] = []
    for line in markdown.splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if cells and all(set(c) <= {"-", ":"} and c for c in cells):
            continue  # separator row like | --- | --- |
        rows.append(cells)
    return rows[1:] if rows else rows  # drop the header row


def _looks_numeric(text: str) -> bool:
    cleaned = text.strip().replace(",", "").replace("$", "").replace("€", "").replace("£", "")
    if not cleaned:
        return False
    try:
        float(cleaned)
        return True
    except ValueError:
        return False


def _artifact_jsonl(flats: list[FlatExtraction]) -> str:
    """Serialize flat extractions as JSONL for the debug/demo artifact."""
    lines = [
        json.dumps(
            {
                "class": f.cls,
                "text": f.text,
                "attributes": f.attributes,
                "char_start": f.char_start,
                "char_end": f.char_end,
            }
        )
        for f in flats
    ]
    return "\n".join(lines)
