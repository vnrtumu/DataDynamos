"""Shared building blocks for the Phase 5 deterministic rule engine.

Rules read ``StructuredResult.fields`` — a plain dict of ``{value, confidence,
grounding}`` nodes (scalars), lists of such nodes (``parties``, ``key_dates``),
line-item rows (``line_items``), and the nested ``termination_clause``. Each rule
returns a :class:`Check`; the agent reconciles them with the LLM judgment, where a
failed ``hard`` check forces ``flag`` and a failed ``review`` check caps the decision
at ``needs_review`` (the LLM can never override these — only explain them).
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

from app.config import settings
from app.schemas import Check, Citation, Grounding


@dataclass
class DecisionContext:
    """Per-run inputs the rule engine reasons over, beyond the structured fields."""

    extraction_confidence: float
    prescan_verdict: str | None = None  # "pass" | "warn" | None (no prescan run)
    prescan_reasons: list[str] = field(default_factory=list)  # page-prefixed warn reasons
    prior_invoice_numbers: set[str] = field(default_factory=set)


# --- field accessors (fields is a JSON-dumped dict, not a Pydantic model) -----


def _node(fields: dict, path: str) -> dict | None:
    """Navigate a dotted path to a FieldValue node (dict with a ``value`` key)."""
    node: object = fields
    for part in path.split("."):
        if not isinstance(node, dict):
            return None
        node = node.get(part)
    return node if isinstance(node, dict) and "value" in node else None


def fval(fields: dict, path: str) -> object | None:
    """The raw value at ``path`` (``None`` when absent or unparsed)."""
    node = _node(fields, path)
    return node["value"] if node else None


def present(fields: dict, path: str) -> bool:
    """True when the field carries a real value (not null/empty/False)."""
    return fval(fields, path) not in (None, "", False)


def as_number(value: object | None) -> float | None:
    """Best-effort float (values are already coerced upstream, but stay defensive)."""
    if isinstance(value, (int, float)):
        return float(value)
    return None


def citations_from_grounding(
    grounding_map: dict[str, Grounding], paths: list[str]
) -> list[Citation]:
    """Build citations for the decision-relevant fields that have a grounded page."""
    out: list[Citation] = []
    for path in paths:
        g = grounding_map.get(path)
        if g is not None and g.page is not None:
            out.append(Citation(field=path, source=f"page {g.page}"))
    return out


# --- cross-cutting gates (shared by every doc type) ---------------------------


def cross_cutting_checks(ctx: DecisionContext) -> list[Check]:
    """The two confidence/quality gates that cap any decision at needs_review."""
    conf_ok = ctx.extraction_confidence >= settings.extraction_confidence_warn
    checks = [
        Check(
            name="extraction_confidence",
            passed=conf_ok,
            detail=(
                f"overall extraction confidence {ctx.extraction_confidence:.2f} "
                f"(warn below {settings.extraction_confidence_warn:.2f})"
            ),
            severity="review",
        )
    ]
    # Prescan is advisory (pass | warn); a warn caps the decision at needs_review.
    prescan_ok = ctx.prescan_verdict != "warn"
    # Name the specific worst-page reason(s) so the decision explains the cap rather
    # than a generic "low input quality" (the reasons are already page-prefixed).
    why = "" if prescan_ok else (": " + "; ".join(ctx.prescan_reasons[:2]) if ctx.prescan_reasons else " — low input quality")
    checks.append(
        Check(
            name="prescan_quality",
            passed=prescan_ok,
            detail=f"pre-flight verdict: {ctx.prescan_verdict or 'not run'}{why}",
            severity="review",
        )
    )
    return checks


# A doc-type rule set: structured fields + context -> a list of checks.
Ruleset = Callable[[dict, DecisionContext], list[Check]]
