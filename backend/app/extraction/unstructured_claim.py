"""Unstructured Claim extraction specification (Tier D Unstructured Layouts)."""

from __future__ import annotations

from pydantic import BaseModel
from app.schemas import FieldValue
from .base import (
    DocTypeSpec,
    FlatExtraction,
    GroundingCtx,
    group_by_class,
    scalar_field,
    to_number,
    to_text,
)

EXTRACTION_CLASSES = {
    "patient_name",
    "service_date",
    "provider_name",
    "claim_number",
    "total_amount",
    "diagnosis",
    "notes",
}

PROMPT = """\
Extract fields from unstructured healthcare documents or clinical billing notes.
Use extraction classes: patient_name, service_date, provider_name, claim_number,
total_amount, diagnosis, notes.
"""


class UnstructuredClaimFields(BaseModel):
    """Tier D Unstructured Claim extracted fields."""

    patient_name: FieldValue
    service_date: FieldValue
    provider_name: FieldValue
    claim_number: FieldValue
    total_amount: FieldValue
    diagnosis: FieldValue
    notes: FieldValue


def assemble_unstructured(flats: list[FlatExtraction], ctx: GroundingCtx) -> UnstructuredClaimFields:
    grouped = group_by_class(flats)
    return UnstructuredClaimFields(
        patient_name=scalar_field(grouped, "patient_name", ctx, to_text),
        service_date=scalar_field(grouped, "service_date", ctx, to_text),
        provider_name=scalar_field(grouped, "provider_name", ctx, to_text),
        claim_number=scalar_field(grouped, "claim_number", ctx, to_text),
        total_amount=scalar_field(grouped, "total_amount", ctx, to_number),
        diagnosis=scalar_field(grouped, "diagnosis", ctx, to_text),
        notes=scalar_field(grouped, "notes", ctx, to_text),
    )


SPEC = DocTypeSpec(
    prompt=PROMPT,
    examples_factory=lambda: [],
    extraction_classes=EXTRACTION_CLASSES,
    field_model=UnstructuredClaimFields,
    assemble=assemble_unstructured,
    core_paths=[
        "patient_name",
        "provider_name",
        "total_amount",
    ],
)
