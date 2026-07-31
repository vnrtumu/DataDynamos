"""UB-04 extraction specification (Tier C Institutional Healthcare Claim Forms)."""

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
    "patient_name",
    "health_plan_id",
    "type_of_bill",
    "federal_tax_id",
    "statement_period_from",
    "statement_period_to",
    "attending_physician_npi",
    "revenue_code",
    "total_charges",
}

PROMPT = """\
Extract UB-04 institutional claim fields. Use extraction classes:
patient_name, health_plan_id, type_of_bill, federal_tax_id, statement_period_from, statement_period_to,
attending_physician_npi, total_charges, and revenue_code (attributes code, desc, charge).
"""


class RevenueLine(BaseModel):
    """One UB-04 revenue code line."""

    code: FieldValue
    desc: FieldValue
    charge: FieldValue


class UB04Fields(BaseModel):
    """Tier C UB-04 extracted fields."""

    patient_name: FieldValue
    health_plan_id: FieldValue
    type_of_bill: FieldValue
    federal_tax_id: FieldValue
    statement_period_from: FieldValue
    statement_period_to: FieldValue
    attending_physician_npi: FieldValue
    revenue_lines: list[RevenueLine]
    total_charges: FieldValue


def _revenue_line(flat: FlatExtraction, ctx: GroundingCtx) -> RevenueLine:
    grounding, confidence = ground_field(flat, ctx)
    return RevenueLine(
        code=attr_field(flat, "code", ctx, grounding, confidence, to_text),
        desc=attr_field(flat, "desc", ctx, grounding, confidence, to_text),
        charge=attr_field(flat, "charge", ctx, grounding, confidence, to_number),
    )


def assemble_ub04(flats: list[FlatExtraction], ctx: GroundingCtx) -> UB04Fields:
    grouped = group_by_class(flats)
    return UB04Fields(
        patient_name=scalar_field(grouped, "patient_name", ctx, to_text),
        health_plan_id=scalar_field(grouped, "health_plan_id", ctx, to_text),
        type_of_bill=scalar_field(grouped, "type_of_bill", ctx, to_text),
        federal_tax_id=scalar_field(grouped, "federal_tax_id", ctx, to_text),
        statement_period_from=scalar_field(grouped, "statement_period_from", ctx, to_text),
        statement_period_to=scalar_field(grouped, "statement_period_to", ctx, to_text),
        attending_physician_npi=scalar_field(grouped, "attending_physician_npi", ctx, to_text),
        revenue_lines=[_revenue_line(f, ctx) for f in grouped.get("revenue_code", [])],
        total_charges=scalar_field(grouped, "total_charges", ctx, to_number),
    )


def _examples() -> list:
    import langextract as lx

    return [
        lx.data.ExampleData(
            text=(
                "UB-04 INSTITUTIONAL CLAIM\n"
                "PATIENT: KARNO, YOLANA   PLAN ID: 990086221\n"
                "BILL TYPE: 0111   TAX ID: 72-1216996\n"
                "STATEMENT PERIOD: 2026-07-01 TO 2026-07-15\n"
                "ATTENDING PHYSICIAN NPI: 1396827531\n"
                "REV 0250 PHARMACY $450.00\n"
                "TOTAL CHARGES: $1675.00"
            ),
            extractions=[
                lx.data.Extraction(extraction_class="patient_name", extraction_text="KARNO, YOLANA"),
                lx.data.Extraction(extraction_class="health_plan_id", extraction_text="990086221"),
                lx.data.Extraction(extraction_class="type_of_bill", extraction_text="0111"),
                lx.data.Extraction(extraction_class="federal_tax_id", extraction_text="72-1216996"),
                lx.data.Extraction(extraction_class="statement_period_from", extraction_text="2026-07-01"),
                lx.data.Extraction(extraction_class="statement_period_to", extraction_text="2026-07-15"),
                lx.data.Extraction(extraction_class="attending_physician_npi", extraction_text="1396827531"),
                lx.data.Extraction(
                    extraction_class="revenue_code",
                    extraction_text="REV 0250 PHARMACY $450.00",
                    attributes={"code": "0250", "desc": "PHARMACY", "charge": "450.00"},
                ),
                lx.data.Extraction(extraction_class="total_charges", extraction_text="$1675.00"),
            ],
        )
    ]


SPEC = DocTypeSpec(
    prompt=PROMPT,
    examples_factory=_examples,
    extraction_classes=EXTRACTION_CLASSES,
    field_model=UB04Fields,
    assemble=assemble_ub04,
    core_paths=[
        "patient_name",
        "health_plan_id",
        "attending_physician_npi",
        "total_charges",
    ],
)
