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


def _examples() -> list:
    import langextract as lx

    return [
        lx.data.ExampleData(
            text=(
                "Patient: KARNO, YOLANA\n"
                "Service Date: 2026-07-16\n"
                "Provider: Kim E VanGeffen PhD\n"
                "Claim Number: CLM-990086221\n"
                "Total Amount: $1675.00\n"
                "Diagnosis: G31.84, F02.81\n"
                "Notes: Healthcare claim treatment provided for diagnosis G31.84, F02.81"
            ),
            extractions=[
                lx.data.Extraction(extraction_class="patient_name", extraction_text="KARNO, YOLANA"),
                lx.data.Extraction(extraction_class="service_date", extraction_text="2026-07-16"),
                lx.data.Extraction(extraction_class="provider_name", extraction_text="Kim E VanGeffen PhD"),
                lx.data.Extraction(extraction_class="claim_number", extraction_text="CLM-990086221"),
                lx.data.Extraction(extraction_class="total_amount", extraction_text="$1675.00"),
                lx.data.Extraction(extraction_class="diagnosis", extraction_text="G31.84, F02.81"),
                lx.data.Extraction(
                    extraction_class="notes",
                    extraction_text="Healthcare claim treatment provided for diagnosis G31.84, F02.81",
                ),
            ],
        )
    ]


SPEC = DocTypeSpec(
    prompt=PROMPT,
    examples_factory=_examples,
    extraction_classes=EXTRACTION_CLASSES,
    field_model=UnstructuredClaimFields,
    assemble=assemble_unstructured,
    core_paths=[
        "patient_name",
        "provider_name",
        "total_amount",
    ],
)
