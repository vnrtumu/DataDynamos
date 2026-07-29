"""Contract extraction: prompt, few-shot examples, field model, and assembly."""

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
    missing_field,
    presence_field,
    scalar_field,
    to_number,
    to_text,
)

EXTRACTION_CLASSES = {
    "party",
    "effective_date",
    "term",
    "renewal_clause",
    "termination_clause",
    "governing_law",
    "total_value",
    "liability_cap",
    "signature",
    "key_date",
}

PROMPT = """\
Extract approval-relevant fields from this contract. Use these extraction classes:
party (one per signatory/organization), effective_date, term, renewal_clause,
termination_clause (with attribute notice_period), governing_law, total_value,
liability_cap, signature (one per executed signature), and key_date (with attribute
label, e.g. "renewal" or "expiry").

Rules:
- Use the exact verbatim text from the source for each extraction_text (do not
  paraphrase) so each field can be traced back to its location.
- Only extract a field if it actually appears in the text. Do NOT infer, guess, or
  fabricate. If a field is absent, simply emit no extraction for it.\
"""


class TerminationClause(BaseModel):
    """Termination clause text plus its notice period."""

    text: FieldValue
    notice_period: FieldValue


class ContractFields(BaseModel):
    """Approval-relevant contract fields (TASK Phase 4)."""

    parties: list[FieldValue]
    effective_date: FieldValue
    term: FieldValue
    renewal_clause: FieldValue
    termination_clause: TerminationClause
    governing_law: FieldValue
    total_value: FieldValue
    liability_cap: FieldValue
    signatures_present: FieldValue
    key_dates: list[FieldValue]


def _list_field(
    grouped: dict[str, list[FlatExtraction]], cls: str, ctx: GroundingCtx
) -> list[FieldValue]:
    """One grounded FieldValue per extraction of ``cls`` (value = the span text)."""
    out: list[FieldValue] = []
    for flat in grouped.get(cls, []):
        grounding, confidence = ground_field(flat, ctx)
        out.append(FieldValue(value=to_text(flat.text), confidence=confidence, grounding=grounding))
    return out


def _termination_clause(
    grouped: dict[str, list[FlatExtraction]], ctx: GroundingCtx
) -> TerminationClause:
    flats = grouped.get("termination_clause")
    if not flats:
        return TerminationClause(text=missing_field(), notice_period=missing_field())
    flat = flats[0]
    grounding, confidence = ground_field(flat, ctx)
    text = FieldValue(value=to_text(flat.text), confidence=confidence, grounding=grounding)
    notice = attr_field(flat, "notice_period", ctx, grounding, confidence, to_text)
    return TerminationClause(text=text, notice_period=notice)


def assemble_contract(flats: list[FlatExtraction], ctx: GroundingCtx) -> ContractFields:
    """Turn flat extractions into a validated ContractFields model."""
    grouped = group_by_class(flats)
    return ContractFields(
        parties=_list_field(grouped, "party", ctx),
        effective_date=scalar_field(grouped, "effective_date", ctx, to_text),
        term=scalar_field(grouped, "term", ctx, to_text),
        renewal_clause=scalar_field(grouped, "renewal_clause", ctx, to_text),
        termination_clause=_termination_clause(grouped, ctx),
        governing_law=scalar_field(grouped, "governing_law", ctx, to_text),
        total_value=scalar_field(grouped, "total_value", ctx, to_number),
        liability_cap=scalar_field(grouped, "liability_cap", ctx, to_number),
        signatures_present=presence_field(grouped, "signature", ctx),
        key_dates=_list_field(grouped, "key_date", ctx),
    )


def _examples() -> list:
    """Few-shot examples (lazy: imports langextract only when the engine runs)."""
    import langextract as lx

    return [
        lx.data.ExampleData(
            text=(
                "MASTER SERVICES AGREEMENT between Acme Corp and Beta LLC.\n"
                "Effective Date: 2024-01-01. Term: 24 months.\n"
                "This Agreement renews automatically for successive 12-month terms.\n"
                "Either party may terminate on 60 days written notice.\n"
                "Governing law: State of Delaware. Total contract value: $250,000.\n"
                "Liability cap: $50,000.\n"
                "Signed: Jane Roe (Acme Corp), John Doe (Beta LLC)."
            ),
            extractions=[
                lx.data.Extraction(extraction_class="party", extraction_text="Acme Corp"),
                lx.data.Extraction(extraction_class="party", extraction_text="Beta LLC"),
                lx.data.Extraction(extraction_class="effective_date", extraction_text="2024-01-01"),
                lx.data.Extraction(extraction_class="term", extraction_text="24 months"),
                lx.data.Extraction(
                    extraction_class="renewal_clause",
                    extraction_text="renews automatically for successive 12-month terms",
                ),
                lx.data.Extraction(
                    extraction_class="termination_clause",
                    extraction_text="Either party may terminate on 60 days written notice",
                    attributes={"notice_period": "60 days"},
                ),
                lx.data.Extraction(
                    extraction_class="governing_law", extraction_text="State of Delaware"
                ),
                lx.data.Extraction(extraction_class="total_value", extraction_text="$250,000"),
                lx.data.Extraction(extraction_class="liability_cap", extraction_text="$50,000"),
                lx.data.Extraction(extraction_class="signature", extraction_text="Jane Roe"),
                lx.data.Extraction(extraction_class="signature", extraction_text="John Doe"),
            ],
        ),
        lx.data.ExampleData(
            # Omits liability cap + signatures -> teaches the model to leave them out.
            text=(
                "Consulting Agreement dated 2023-09-15 by and between Globex and Initech.\n"
                "Initial term of one year, governed by the laws of England and Wales.\n"
                "Renewal date: 2024-09-15."
            ),
            extractions=[
                lx.data.Extraction(extraction_class="party", extraction_text="Globex"),
                lx.data.Extraction(extraction_class="party", extraction_text="Initech"),
                lx.data.Extraction(extraction_class="effective_date", extraction_text="2023-09-15"),
                lx.data.Extraction(extraction_class="term", extraction_text="one year"),
                lx.data.Extraction(
                    extraction_class="governing_law", extraction_text="England and Wales"
                ),
                lx.data.Extraction(
                    extraction_class="key_date",
                    extraction_text="2024-09-15",
                    attributes={"label": "renewal"},
                ),
            ],
        ),
    ]


SPEC = DocTypeSpec(
    prompt=PROMPT,
    examples_factory=_examples,
    extraction_classes=EXTRACTION_CLASSES,
    field_model=ContractFields,
    assemble=assemble_contract,
    core_paths=["parties", "effective_date", "term", "governing_law"],
)
