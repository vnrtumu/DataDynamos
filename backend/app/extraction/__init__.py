"""Per-document-type extraction specs (prompt + few-shot + field model + assembly).

These definitions live here rather than in ``app/schemas.py`` (which is a module, not
a package) so each doc type stays self-contained and adding a third is a one-file add.
"""

from __future__ import annotations

from app.models import DocType

from . import cms1500, ub04, unstructured_claim
from .base import DocTypeSpec

SPECS: dict[DocType, DocTypeSpec] = {
    DocType.cms1500: cms1500.SPEC,
    DocType.cms1500_multi: cms1500.SPEC,
    DocType.ub04: ub04.SPEC,
    DocType.unstructured_claim: unstructured_claim.SPEC,
}


def get_spec(doc_type: DocType) -> DocTypeSpec:
    """Return the extraction spec for a document type."""
    spec = SPECS.get(doc_type)
    if spec is None:  # pragma: no cover - DocType is a closed enum
        raise ValueError(f"No extraction spec for doc_type {doc_type!r}.")
    return spec


__all__ = ["SPECS", "get_spec", "DocTypeSpec"]
