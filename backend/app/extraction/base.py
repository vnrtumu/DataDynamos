"""Shared building blocks for the structuring stage.

A :class:`DocTypeSpec` ties together, for one document type, the LangExtract prompt,
its few-shot examples, the target Pydantic field model, and the assembly function
that turns flat extractions into that validated model. The grounding/confidence
helpers here are provider-agnostic: both the LangExtract and the offline mock
provider normalize into :class:`FlatExtraction`, then assembly grounds each span
against ``OCRResult.full_text`` and propagates OCR confidence.
"""

from __future__ import annotations

import re
from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from app.schemas import Alignment, FieldValue, Grounding

if TYPE_CHECKING:
    from app.schemas import OCRResult


@dataclass
class FlatExtraction:
    """One provider-agnostic extraction: a class label + its verbatim span.

    ``char_start``/``char_end`` are offsets into the text handed to the extractor
    (``None`` when the provider doesn't supply them — the mock relies on the
    grounding step's ``str.find`` re-anchoring). ``attributes`` carries sub-fields
    such as a line item's columns or a clause's notice period.
    """

    cls: str
    text: str
    attributes: dict = field(default_factory=dict)
    char_start: int | None = None
    char_end: int | None = None
    alignment: Alignment | None = None  # provider hint, re-verified during grounding


@dataclass
class DocTypeSpec:
    """Everything needed to extract and assemble one document type."""

    prompt: str
    examples_factory: Callable[[], list]  # lazy: builds lx.data.ExampleData[]
    extraction_classes: set[str]
    field_model: type
    assemble: Callable[[list[FlatExtraction], GroundingCtx], object]
    core_paths: list[str]  # dotted field paths used for the overall confidence mean


@dataclass
class GroundingCtx:
    """Per-run context threaded through assembly: source text + OCR confidence."""

    full_text: str
    ocr_result: OCRResult
    page_offsets: list[tuple[int, int]] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.page_offsets:
            self.page_offsets = build_page_offsets(self.ocr_result)


# Alignment quality -> base confidence before OCR propagation.
_ALIGN_BASE: dict[str, float] = {"exact": 1.0, "partial": 0.7, "ungrounded": 0.4}


def build_page_offsets(ocr_result: OCRResult) -> list[tuple[int, int]]:
    """``(page_number, start_offset)`` for each page within ``full_text``.

    ``full_text`` is ``"\\n\\n".join(page.text)``; we add 2 for the joiner after every
    page so a char offset maps back to the page it came from.
    """
    offsets: list[tuple[int, int]] = []
    cursor = 0
    for page in ocr_result.pages:
        offsets.append((page.page, cursor))
        cursor += len(page.text) + 2  # +2 for the "\n\n" page joiner
    return offsets


def char_to_page(offsets: list[tuple[int, int]], pos: int | None) -> int | None:
    """Map a char offset to its 1-based page (gap between pages -> preceding page)."""
    if pos is None:
        return None
    page: int | None = None
    for page_no, start in offsets:
        if start <= pos:
            page = page_no
        else:
            break
    return page


def _page_confidence(ocr_result: OCRResult, page: int | None) -> float:
    """OCR confidence multiplier for a page (falls back to the doc mean, then 1.0).

    Engines that don't expose confidence (e.g. Docling) leave it ``None``; we treat
    that as a neutral 1.0 so confidence becomes alignment-only (a warning is added
    once in ``run_structuring``).
    """
    if page is not None:
        for p in ocr_result.pages:
            if p.page == page and p.avg_confidence is not None:
                return p.avg_confidence
    if ocr_result.avg_confidence is not None:
        return ocr_result.avg_confidence
    return 1.0


def _ground(
    text: str, full_text: str, char_start: int | None, char_end: int | None
) -> tuple[int | None, int | None, Alignment]:
    """Resolve a span's offsets in ``full_text``, re-anchoring with ``find`` if needed.

    Trusts provider offsets only when they actually quote ``text`` (guards against
    chunk-local offsets); otherwise falls back to the first verbatim match. A match
    found only by re-anchoring is reported as ``partial``.
    """
    if (
        char_start is not None
        and char_end is not None
        and 0 <= char_start < char_end <= len(full_text)
        and full_text[char_start:char_end] == text
    ):
        return char_start, char_end, "exact"
    idx = full_text.find(text) if text else -1
    if idx >= 0:
        # No trustworthy provider offset, but the span is present verbatim.
        alignment: Alignment = "exact" if char_start is None else "partial"
        return idx, idx + len(text), alignment
    return None, None, "ungrounded"


def ground_field(flat: FlatExtraction, ctx: GroundingCtx) -> tuple[Grounding, float]:
    """Build the :class:`Grounding` + confidence for one extraction span."""
    cs, ce, alignment = _ground(
        flat.text, ctx.full_text, flat.char_start, flat.char_end
    )
    page = char_to_page(ctx.page_offsets, cs)
    grounding = Grounding(
        page=page, char_start=cs, char_end=ce, snippet=flat.text, alignment=alignment
    )
    base = _ALIGN_BASE.get(alignment, 0.4)
    confidence = round(min(1.0, base * _page_confidence(ctx.ocr_result, page)), 4)
    return grounding, confidence


def group_by_class(flats: list[FlatExtraction]) -> dict[str, list[FlatExtraction]]:
    """Bucket flat extractions by their class label, preserving order."""
    grouped: dict[str, list[FlatExtraction]] = defaultdict(list)
    for flat in flats:
        grouped[flat.cls].append(flat)
    return grouped


def missing_field() -> FieldValue:
    """A field absent from the source: explicit null, zero confidence, no grounding."""
    return FieldValue(value=None, confidence=0.0, grounding=None)


def scalar_field(
    grouped: dict[str, list[FlatExtraction]],
    cls: str,
    ctx: GroundingCtx,
    coerce: Callable[[str], object] = str,
) -> FieldValue:
    """Build one scalar :class:`FieldValue` from the first extraction of ``cls``.

    Absent class -> ``missing_field()``. A coercion failure degrades to ``value=None``
    with halved confidence + a warning rather than raising — never a 500.
    """
    flats = grouped.get(cls)
    if not flats:
        return missing_field()
    flat = flats[0]
    grounding, confidence = ground_field(flat, ctx)
    try:
        value = coerce(flat.text)
    except (ValueError, TypeError):
        ctx.warnings.append(f"could not parse {cls!r} value {flat.text!r}")
        return FieldValue(
            value=None, confidence=round(confidence * 0.5, 4), grounding=grounding
        )
    return FieldValue(value=value, confidence=confidence, grounding=grounding)


def attr_field(
    flat: FlatExtraction,
    key: str,
    ctx: GroundingCtx,
    grounding: Grounding,
    confidence: float,
    coerce: Callable[[str], object] = str,
) -> FieldValue:
    """Build a :class:`FieldValue` for one attribute of a composite extraction.

    Used by composite assemblers (a line item's columns, a clause's notice period)
    where every attribute shares the parent span's ``grounding``/``confidence`` —
    so those are passed in once rather than recomputed per attribute. Mirrors
    :func:`scalar_field`: absent attribute -> ``missing_field()``; a coercion failure
    degrades to ``value=None`` with halved confidence + a warning rather than raising.
    """
    raw = flat.attributes.get(key)
    if raw is None:
        return missing_field()
    try:
        value = coerce(str(raw))
    except (ValueError, TypeError):
        ctx.warnings.append(f"could not parse {flat.cls}.{key} value {raw!r}")
        return FieldValue(
            value=None, confidence=round(confidence * 0.5, 4), grounding=grounding
        )
    return FieldValue(value=value, confidence=confidence, grounding=grounding)


def presence_field(
    grouped: dict[str, list[FlatExtraction]], cls: str, ctx: GroundingCtx
) -> FieldValue:
    """A boolean field that is True iff an extraction of ``cls`` exists (grounded)."""
    flats = grouped.get(cls)
    if not flats:
        return FieldValue(value=False, confidence=0.0, grounding=None)
    grounding, confidence = ground_field(flats[0], ctx)
    return FieldValue(value=True, confidence=confidence, grounding=grounding)


# --- value coercion helpers ---------------------------------------------------


_CURRENCY_NUM = re.compile(r"[$€£]\s?([\d][\d.,oO]*)")
_BARE_NUM = re.compile(r"(?<![\w.])([\d][\d.,oO]*)")


def to_number(text: str) -> float:
    """Parse an amount out of a currency string, tolerant of surrounding prose.

    Real OCR'd fields rarely arrive as a bare ``"1234.56"`` — the amount is embedded
    in text (``"shall not exceed US $96,000"``) and OCR sometimes misreads a ``0`` as
    ``o``. So we extract the numeric token attached to a currency symbol (preferred —
    it skips incidental numbers like "twelve (12) months"), else the first bare number,
    and map the ``o/O`` OCR confusion back to ``0``.
    """
    m = _CURRENCY_NUM.search(text) or _BARE_NUM.search(text)
    if not m:
        raise ValueError(f"no number in {text!r}")
    token = m.group(1).replace(",", "").replace("o", "0").replace("O", "0").rstrip(".")
    if not token or token == ".":
        raise ValueError(f"no number in {text!r}")
    return float(token)


def to_text(text: str) -> str:
    """Trim a free-text span."""
    return text.strip()
