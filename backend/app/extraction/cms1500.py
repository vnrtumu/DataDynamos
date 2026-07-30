"""CMS-1500 extraction specification (Tier A & Tier B Healthcare Claim Forms)."""

from __future__ import annotations

from pydantic import BaseModel
from app.schemas import FieldValue
from .base import (
    DocTypeSpec,
    FlatExtraction,
    GroundingCtx,
    attr_field,
    ground_field,
    group_by_class,
    scalar_field,
    to_number,
    to_text,
)

EXTRACTION_CLASSES = {
    "insurance_type",
    "insured_id",
    "patient_name",
    "patient_dob",
    "patient_address",
    "signatures_on_file",
    "diagnosis_codes",
    "prior_auth_number",
    "rendering_provider_npi",
    "provider_tax_id",
    "total_charge",
    "amount_paid",
    "balance_due",
    "billing_provider_name",
    "billing_provider_address",
    "billing_provider_npi",
    "payer_name",
    "service_line",
}

PROMPT = """\
Extract healthcare claim fields from this CMS-1500 form according to official box numbers:
insurance_type (Box 1), insured_id (Box 1a), patient_name (Box 2), patient_dob (Box 3),
signatures_on_file (Box 12/13), diagnosis_codes (Box 21 A-L), prior_auth_number (Box 23),
provider_tax_id (Box 25), total_charge (Box 28), amount_paid (Box 29), balance_due (Box 30),
billing_provider_name (Box 33), billing_provider_address (Box 33), billing_provider_npi (Box 33a),
rendering_provider_npi (Box 24J), and service_line (Box 24, with attributes: dos, pos, cpt, diag_pointer, charge, units, rendering_npi).
"""


class ServiceLine(BaseModel):
    """One service line on CMS-1500 Box 24."""

    dos: FieldValue
    pos: FieldValue
    cpt: FieldValue
    diag_pointer: FieldValue
    charge: FieldValue
    units: FieldValue
    rendering_npi: FieldValue


class CMS1500Fields(BaseModel):
    """Tier A / Tier B CMS-1500 extracted fields."""

    insurance_type: FieldValue
    insured_id: FieldValue
    patient_name: FieldValue
    patient_dob: FieldValue
    patient_address: FieldValue
    signatures_on_file: FieldValue
    diagnosis_codes: FieldValue
    prior_auth_number: FieldValue
    provider_tax_id: FieldValue
    total_charge: FieldValue
    amount_paid: FieldValue
    balance_due: FieldValue
    billing_provider_name: FieldValue
    billing_provider_address: FieldValue
    billing_provider_npi: FieldValue
    rendering_provider_npi: FieldValue
    payer_name: FieldValue
    service_lines: list[ServiceLine]


def _service_line(flat: FlatExtraction, ctx: GroundingCtx) -> ServiceLine:
    grounding, confidence = ground_field(flat, ctx)
    return ServiceLine(
        dos=attr_field(flat, "dos", ctx, grounding, confidence, to_text),
        pos=attr_field(flat, "pos", ctx, grounding, confidence, to_text),
        cpt=attr_field(flat, "cpt", ctx, grounding, confidence, to_text),
        diag_pointer=attr_field(flat, "diag_pointer", ctx, grounding, confidence, to_text),
        charge=attr_field(flat, "charge", ctx, grounding, confidence, to_number),
        units=attr_field(flat, "units", ctx, grounding, confidence, to_number),
        rendering_npi=attr_field(flat, "rendering_npi", ctx, grounding, confidence, to_text),
    )


def assemble_cms1500(flats: list[FlatExtraction], ctx: GroundingCtx) -> CMS1500Fields:
    grouped = group_by_class(flats)
    return CMS1500Fields(
        insurance_type=scalar_field(grouped, "insurance_type", ctx, to_text),
        insured_id=scalar_field(grouped, "insured_id", ctx, to_text),
        patient_name=scalar_field(grouped, "patient_name", ctx, to_text),
        patient_dob=scalar_field(grouped, "patient_dob", ctx, to_text),
        patient_address=scalar_field(grouped, "patient_address", ctx, to_text),
        signatures_on_file=scalar_field(grouped, "signatures_on_file", ctx, to_text),
        diagnosis_codes=scalar_field(grouped, "diagnosis_codes", ctx, to_text),
        prior_auth_number=scalar_field(grouped, "prior_auth_number", ctx, to_text),
        provider_tax_id=scalar_field(grouped, "provider_tax_id", ctx, to_text),
        total_charge=scalar_field(grouped, "total_charge", ctx, to_number),
        amount_paid=scalar_field(grouped, "amount_paid", ctx, to_number),
        balance_due=scalar_field(grouped, "balance_due", ctx, to_number),
        billing_provider_name=scalar_field(grouped, "billing_provider_name", ctx, to_text),
        billing_provider_address=scalar_field(grouped, "billing_provider_address", ctx, to_text),
        billing_provider_npi=scalar_field(grouped, "billing_provider_npi", ctx, to_text),
        rendering_provider_npi=scalar_field(grouped, "rendering_provider_npi", ctx, to_text),
        payer_name=scalar_field(grouped, "payer_name", ctx, to_text),
        service_lines=[_service_line(f, ctx) for f in grouped.get("service_line", [])],
    )


SPEC = DocTypeSpec(
    prompt=PROMPT,
    examples_factory=lambda: [],
    extraction_classes=EXTRACTION_CLASSES,
    field_model=CMS1500Fields,
    assemble=assemble_cms1500,
    core_paths=[
        "patient_name",
        "insured_id",
        "billing_provider_npi",
        "total_charge",
    ],
)
