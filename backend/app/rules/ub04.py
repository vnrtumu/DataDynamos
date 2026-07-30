"""Deterministic business rules for UB-04 Institutional Claim Forms (Tier C)."""

from __future__ import annotations

import re
from app.schemas import Check
from .base import DecisionContext, as_number, cross_cutting_checks, fval, present
from .cms1500 import validate_npi


def validate_tax_id(tax_id_str: str | None) -> bool:
    """Validate 9-digit Federal Tax ID / EIN format."""
    if not tax_id_str:
        return False
    digits = re.sub(r"\D", "", tax_id_str)
    return len(digits) == 9


def ub04_rules(fields: dict, ctx: DecisionContext) -> list[Check]:
    checks = cross_cutting_checks(ctx)

    # 1. Attending Physician NPI
    npi = fval(fields, "attending_physician_npi")
    npi_valid = validate_npi(str(npi) if npi else None)
    checks.append(
        Check(
            name="attending_npi_checksum",
            passed=npi_valid,
            detail=f"attending physician NPI '{npi or 'missing'}' checksum: {'valid' if npi_valid else 'invalid/missing'}",
            severity="hard" if not npi else "review",
        )
    )

    # 2. Federal Tax ID validation
    tax_id = fval(fields, "federal_tax_id")
    tax_ok = validate_tax_id(str(tax_id) if tax_id else None)
    checks.append(
        Check(
            name="federal_tax_id_format",
            passed=tax_ok,
            detail=f"federal tax ID '{tax_id or 'missing'}' 9-digit format check",
            severity="review",
        )
    )

    # 3. Revenue lines total check
    rev_lines = fields.get("revenue_lines") or []
    rev_sum = 0.0
    for r in rev_lines:
        if isinstance(r, dict):
            chg = as_number((r.get("charge") or {}).get("value"))
            if chg is not None:
                rev_sum += chg

    tot_chg = as_number(fval(fields, "total_charges"))
    if tot_chg is not None and rev_sum > 0:
        balance_ok = abs(tot_chg - rev_sum) <= 0.05
        checks.append(
            Check(
                name="revenue_charges_balance",
                passed=balance_ok,
                detail=f"total charges {tot_chg:.2f} matches revenue lines sum {rev_sum:.2f}",
                severity="hard",
            )
        )

    # 4. Patient name & Health plan ID
    checks.append(
        Check(
            name="institutional_patient_id",
            passed=present(fields, "patient_name") and present(fields, "health_plan_id"),
            detail="patient name and health plan ID present on institutional claim",
            severity="hard",
        )
    )

    return checks
