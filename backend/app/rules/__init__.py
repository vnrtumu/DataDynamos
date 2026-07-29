"""Deterministic per-doc-type business rules for the agent decision layer.

Mirrors ``app/extraction``: each doc type contributes a rule set and the citation
paths worth surfacing; this module is the registry the agent stage consults.
"""

from __future__ import annotations

from app.models import DocType

from . import contract, invoice
from .base import (
    DecisionContext,
    Ruleset,
    citations_from_grounding,
    cross_cutting_checks,
)

RULESETS: dict[DocType, Ruleset] = {
    DocType.invoice: invoice.invoice_checks,
    DocType.contract: contract.contract_checks,
}

CITATION_PATHS: dict[DocType, list[str]] = {
    DocType.invoice: invoice.CITATION_PATHS,
    DocType.contract: contract.CITATION_PATHS,
}


def get_ruleset(doc_type: DocType) -> Ruleset:
    """Return the rule set for a document type, or raise for an unknown type."""
    ruleset = RULESETS.get(doc_type)
    if ruleset is None:
        raise ValueError(f"No rule set for doc_type {doc_type!r}.")
    return ruleset


def get_citation_paths(doc_type: DocType) -> list[str]:
    """Field paths to cite for a document type (empty for unknown types)."""
    return CITATION_PATHS.get(doc_type, [])


__all__ = [
    "DecisionContext",
    "Ruleset",
    "citations_from_grounding",
    "cross_cutting_checks",
    "get_citation_paths",
    "get_ruleset",
]
