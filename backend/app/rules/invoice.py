"""Invoice business rules (TASK Phase 5).

Each rule is deterministic and grounded in the structured fields; the agent's LLM
call adds narrative on top but cannot override a failed ``hard`` rule.
"""

from __future__ import annotations

from app.config import settings
from app.schemas import Check

from .base import DecisionContext, as_number, fval, present

# Fields worth citing in the decision (those a reviewer would check first).
CITATION_PATHS = ["vendor", "invoice_no", "total", "subtotal", "tax"]


def invoice_checks(fields: dict, ctx: DecisionContext) -> list[Check]:
    """Run the invoice rule set over the structured fields."""
    checks: list[Check] = []

    # total = subtotal + tax (hard). Skipped when components are absent so we never
    # flag on missing data — that's the confidence gate's job, not a math failure.
    total = as_number(fval(fields, "total"))
    subtotal = as_number(fval(fields, "subtotal"))
    tax = as_number(fval(fields, "tax"))
    if total is not None and subtotal is not None and tax is not None:
        expected = subtotal + tax
        ok = abs(total - expected) <= settings.invoice_total_tolerance
        checks.append(
            Check(
                name="total_math",
                passed=ok,
                detail=(
                    f"total {total:.2f} {'=' if ok else '≠'} subtotal {subtotal:.2f} "
                    f"+ tax {tax:.2f} ({expected:.2f})"
                ),
                severity="hard",
            )
        )
    else:
        checks.append(
            Check(
                name="total_math",
                passed=True,
                detail="not enough line-total data to verify (subtotal/tax/total)",
                severity="advisory",
            )
        )

    # Duplicate invoice number across previously decided documents (hard).
    invoice_no = fval(fields, "invoice_no")
    if invoice_no is not None:
        dup = str(invoice_no) in ctx.prior_invoice_numbers
        checks.append(
            Check(
                name="duplicate_invoice_no",
                passed=not dup,
                detail=(
                    f"invoice_no {invoice_no!r} "
                    + ("already seen on another document" if dup else "is unique")
                ),
                severity="hard",
            )
        )

    # Auto-approve threshold (review): large totals need a human.
    if total is not None:
        under = total <= settings.invoice_auto_approve_max
        checks.append(
            Check(
                name="auto_approve_threshold",
                passed=under,
                detail=(
                    f"total {total:.2f} "
                    f"{'within' if under else 'over'} auto-approve limit "
                    f"{settings.invoice_auto_approve_max:.2f}"
                ),
                severity="review",
            )
        )

    # PO present (advisory) — surfaced, but absence alone doesn't block.
    po_present = present(fields, "po_number")
    checks.append(
        Check(
            name="po_present",
            passed=po_present,
            detail="purchase-order number " + ("present" if po_present else "absent"),
            severity="advisory",
        )
    )

    # Due date present (advisory).
    due_date_present = present(fields, "due_date")
    checks.append(
        Check(
            name="due_date_present",
            passed=due_date_present,
            detail="due date " + ("present" if due_date_present else "absent"),
            severity="advisory",
        )
    )

    # Bank/payment details (advisory by default; hard when flagged in config). True
    # change-detection needs a vendor baseline — deferred; advisory avoids false flags.
    has_bank = present(fields, "bank_details_present")
    bank_severity = "hard" if settings.invoice_flag_on_bank_details else "advisory"
    checks.append(
        Check(
            name="bank_details",
            passed=not (has_bank and settings.invoice_flag_on_bank_details),
            detail=(
                "payment/bank details "
                + ("present — verify against vendor records" if has_bank else "not present")
            ),
            severity=bank_severity,
        )
    )

    return checks
