"""Deterministic business rules for Unstructured Claims (Tier D)."""

from __future__ import annotations

from app.schemas import Check
from .base import DecisionContext, as_number, cross_cutting_checks, fval, present


def unstructured_claim_rules(fields: dict, ctx: DecisionContext) -> list[Check]:
    checks = cross_cutting_checks(ctx)

    # 1. Mandatory identification fields
    checks.append(
        Check(
            name="unstructured_patient_present",
            passed=present(fields, "patient_name"),
            detail=f"patient name present: {fval(fields, 'patient_name') or 'missing'}",
            severity="hard",
        )
    )

    # 2. Total amount present & positive
    amt = as_number(fval(fields, "total_amount"))
    checks.append(
        Check(
            name="total_amount_valid",
            passed=amt is not None and amt > 0,
            detail=f"claim total amount: {amt if amt is not None else 'missing'}",
            severity="review",
        )
    )

    # 3. Provider or Service Date
    checks.append(
        Check(
            name="provider_or_date_present",
            passed=present(fields, "provider_name") or present(fields, "service_date"),
            detail="provider name or service date captured from unstructured layout",
            severity="review",
        )
    )

    return checks
