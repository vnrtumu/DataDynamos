"""Deterministic per-doc-type business rules for the agent decision layer.

Mirrors ``app/extraction``: each doc type contributes a rule set and the citation
paths worth surfacing; this module is the registry the agent stage consults.
"""

from __future__ import annotations

from app.models import DocType

from . import cms1500, ub04, unstructured_claim
from .base import (
    DecisionContext,
    Ruleset,
    citations_from_grounding,
    cross_cutting_checks,
)

RULESETS: dict[DocType, Ruleset] = {
    DocType.cms1500: cms1500.cms1500_rules,
    DocType.cms1500_multi: cms1500.cms1500_rules,
    DocType.ub04: ub04.ub04_rules,
    DocType.unstructured_claim: unstructured_claim.unstructured_claim_rules,
}

CITATION_PATHS: dict[DocType, list[str]] = {
    DocType.cms1500: ["patient_name", "insured_id", "billing_provider_npi", "total_charge"],
    DocType.cms1500_multi: ["patient_name", "insured_id", "billing_provider_npi", "total_charge"],
    DocType.ub04: ["patient_name", "health_plan_id", "attending_physician_npi", "total_charges"],
    DocType.unstructured_claim: ["patient_name", "provider_name", "total_amount"],
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
