"""Contract business rules (TASK Phase 5)."""

from __future__ import annotations

from app.config import settings
from app.schemas import Check

from .base import DecisionContext, as_number, fval, present

CITATION_PATHS = [
    "parties.0",
    "effective_date",
    "governing_law",
    "total_value",
    "termination_clause.text",
]


def contract_checks(fields: dict, ctx: DecisionContext) -> list[Check]:
    """Run the contract rule set over the structured fields."""
    checks: list[Check] = []

    # Missing signatures (hard).
    signed = present(fields, "signatures_present")
    checks.append(
        Check(
            name="signatures_present",
            passed=signed,
            detail="executed signatures " + ("present" if signed else "missing"),
            severity="hard",
        )
    )

    # Auto-renew without a notice period (hard).
    renews = present(fields, "renewal_clause")
    has_notice = present(fields, "termination_clause.notice_period")
    auto_renew_risk = renews and not has_notice
    checks.append(
        Check(
            name="auto_renew_without_notice",
            passed=not auto_renew_risk,
            detail=(
                "auto-renews with no termination notice period"
                if auto_renew_risk
                else "renewal/notice terms acceptable"
            ),
            severity="hard",
        )
    )

    # Standard termination clause present (review).
    has_termination = present(fields, "termination_clause.text")
    checks.append(
        Check(
            name="termination_clause_present",
            passed=has_termination,
            detail="termination clause " + ("present" if has_termination else "absent"),
            severity="review",
        )
    )

    # Liability cap present (review).
    has_cap = present(fields, "liability_cap")
    checks.append(
        Check(
            name="liability_cap_present",
            passed=has_cap,
            detail="liability cap " + ("present" if has_cap else "absent"),
            severity="review",
        )
    )

    # Governing law in the allowed list (review). Absent allowlist disables the check.
    law = fval(fields, "governing_law")
    allowed = settings.contract_allowed_governing_law
    if law is None:
        checks.append(
            Check(
                name="governing_law_allowed",
                passed=True,
                detail="governing law absent",
                severity="advisory",
            )
        )
    elif allowed:
        law_l = str(law).lower()
        ok = any(item.lower() in law_l for item in allowed)
        checks.append(
            Check(
                name="governing_law_allowed",
                passed=ok,
                detail=(
                    f"governing law {law!r} "
                    + ("is allowed" if ok else f"not in {allowed}")
                ),
                severity="review",
            )
        )

    # Total value over the review threshold (review).
    value = as_number(fval(fields, "total_value"))
    if value is not None:
        under = value <= settings.contract_value_review_threshold
        checks.append(
            Check(
                name="value_over_threshold",
                passed=under,
                detail=(
                    f"contract value {value:.2f} "
                    f"{'within' if under else 'over'} review threshold "
                    f"{settings.contract_value_review_threshold:.2f}"
                ),
                severity="review",
            )
        )

    return checks
