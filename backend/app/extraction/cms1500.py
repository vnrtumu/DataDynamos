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
    "insured_name",
    "insured_address",
    "referring_provider_name",
    "referring_provider_npi",
    "illness_date",
    "signatures_on_file",
    "diagnosis_codes",
    "prior_auth_number",
    "rendering_provider_npi",
    "provider_tax_id",
    "patient_account_no",
    "accept_assignment",
    "total_charge",
    "amount_paid",
    "balance_due",
    "service_facility_name",
    "service_facility_address",
    "service_facility_npi",
    "billing_provider_name",
    "billing_provider_address",
    "billing_provider_npi",
    "payer_name",
    "service_line",
}

PROMPT = """\
Extract healthcare claim fields from this CMS-1500 form according to official box numbers:
insurance_type (Box 1), insured_id (Box 1a), patient_name (Box 2 - Last Name, First Name), patient_dob (Box 3),
patient_address (Box 5 - Street, City, State, Zip), insured_name (Box 4), insured_address (Box 7),
referring_provider_name (Box 17), referring_provider_npi (Box 17b), illness_date (Box 14),
signatures_on_file (Box 12/13), diagnosis_codes (Box 21 A-L), prior_auth_number (Box 23),
provider_tax_id (Box 25), patient_account_no (Box 26), accept_assignment (Box 27),
total_charge (Box 28), amount_paid (Box 29), balance_due (Box 30),
service_facility_name (Box 32), service_facility_address (Box 32), service_facility_npi (Box 32a),
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
    insured_name: FieldValue
    insured_address: FieldValue
    referring_provider_name: FieldValue
    referring_provider_npi: FieldValue
    illness_date: FieldValue
    signatures_on_file: FieldValue
    diagnosis_codes: FieldValue
    prior_auth_number: FieldValue
    provider_tax_id: FieldValue
    patient_account_no: FieldValue
    accept_assignment: FieldValue
    total_charge: FieldValue
    amount_paid: FieldValue
    balance_due: FieldValue
    service_facility_name: FieldValue
    service_facility_address: FieldValue
    service_facility_npi: FieldValue
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
        insured_name=scalar_field(grouped, "insured_name", ctx, to_text),
        insured_address=scalar_field(grouped, "insured_address", ctx, to_text),
        referring_provider_name=scalar_field(grouped, "referring_provider_name", ctx, to_text),
        referring_provider_npi=scalar_field(grouped, "referring_provider_npi", ctx, to_text),
        illness_date=scalar_field(grouped, "illness_date", ctx, to_text),
        signatures_on_file=scalar_field(grouped, "signatures_on_file", ctx, to_text),
        diagnosis_codes=scalar_field(grouped, "diagnosis_codes", ctx, to_text),
        prior_auth_number=scalar_field(grouped, "prior_auth_number", ctx, to_text),
        provider_tax_id=scalar_field(grouped, "provider_tax_id", ctx, to_text),
        patient_account_no=scalar_field(grouped, "patient_account_no", ctx, to_text),
        accept_assignment=scalar_field(grouped, "accept_assignment", ctx, to_text),
        total_charge=scalar_field(grouped, "total_charge", ctx, to_number),
        amount_paid=scalar_field(grouped, "amount_paid", ctx, to_number),
        balance_due=scalar_field(grouped, "balance_due", ctx, to_number),
        service_facility_name=scalar_field(grouped, "service_facility_name", ctx, to_text),
        service_facility_address=scalar_field(grouped, "service_facility_address", ctx, to_text),
        service_facility_npi=scalar_field(grouped, "service_facility_npi", ctx, to_text),
        billing_provider_name=scalar_field(grouped, "billing_provider_name", ctx, to_text),
        billing_provider_address=scalar_field(grouped, "billing_provider_address", ctx, to_text),
        billing_provider_npi=scalar_field(grouped, "billing_provider_npi", ctx, to_text),
        rendering_provider_npi=scalar_field(grouped, "rendering_provider_npi", ctx, to_text),
        payer_name=scalar_field(grouped, "payer_name", ctx, to_text),
        service_lines=[_service_line(f, ctx) for f in grouped.get("service_line", [])],
    )


def _examples() -> list:
    import langextract as lx

    return [
        lx.data.ExampleData(
            text=(
                "HEALTH INSURANCE CLAIM FORM\n"
                "1. MEDICARE  1a. INSURED'S I.D. NUMBER: 990086221-00\n"
                "2. PATIENT'S NAME: KARNO, YOLANA\n"
                "3. PATIENT'S BIRTH DATE: 12-02-1932  SEX: F\n"
                "5. PATIENT'S ADDRESS: 4019 IDAHO AVE, KENNER LA 70065\n"
                "12. SIGNATURE ON FILE  Date: 06-25-26\n"
                "21. DIAGNOSIS: A. G31.84  B. F02.81\n"
                "23. PRIOR AUTHORIZATION: AUTH-30757\n"
                "25. FEDERAL TAX I.D.: 721216996\n"
                "28. TOTAL CHARGE: $1675.00  29. AMOUNT PAID: $0.00  30. BALANCE DUE: $1675.00\n"
                "33. BILLING PROVIDER: Kim E VanGeffen PhD  NPI: 1396827531\n"
                "24. 07/16/25 11 96116 A B $175.00 1 NPI 1396827531"
            ),
            extractions=[
                lx.data.Extraction(extraction_class="insurance_type", extraction_text="MEDICARE"),
                lx.data.Extraction(extraction_class="insured_id", extraction_text="990086221-00"),
                lx.data.Extraction(extraction_class="patient_name", extraction_text="KARNO, YOLANA"),
                lx.data.Extraction(extraction_class="patient_dob", extraction_text="12-02-1932"),
                lx.data.Extraction(
                    extraction_class="patient_address",
                    extraction_text="4019 IDAHO AVE, KENNER LA 70065",
                ),
                lx.data.Extraction(extraction_class="signatures_on_file", extraction_text="SIGNATURE ON FILE"),
                lx.data.Extraction(extraction_class="diagnosis_codes", extraction_text="G31.84, F02.81"),
                lx.data.Extraction(extraction_class="prior_auth_number", extraction_text="AUTH-30757"),
                lx.data.Extraction(extraction_class="provider_tax_id", extraction_text="721216996"),
                lx.data.Extraction(extraction_class="total_charge", extraction_text="$1675.00"),
                lx.data.Extraction(extraction_class="amount_paid", extraction_text="$0.00"),
                lx.data.Extraction(extraction_class="balance_due", extraction_text="$1675.00"),
                lx.data.Extraction(extraction_class="billing_provider_name", extraction_text="Kim E VanGeffen PhD"),
                lx.data.Extraction(extraction_class="billing_provider_npi", extraction_text="1396827531"),
                lx.data.Extraction(
                    extraction_class="service_line",
                    extraction_text="07/16/25 11 96116 A B $175.00 1 NPI 1396827531",
                    attributes={
                        "dos": "07/16/25",
                        "pos": "11",
                        "cpt": "96116",
                        "diag_pointer": "A B",
                        "charge": "175.00",
                        "units": "1",
                        "rendering_npi": "1396827531",
                    },
                ),
            ],
        )
    ]


SPEC = DocTypeSpec(
    prompt=PROMPT,
    examples_factory=_examples,
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
