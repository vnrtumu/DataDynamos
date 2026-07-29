"""Invoice extraction: prompt, few-shot examples, field model, and assembly."""

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
    presence_field,
    scalar_field,
    to_number,
    to_text,
)

# Extraction classes the model may emit. line_item rows carry their columns in
# attributes; bank_details_present is derived from a bank_details span's presence.
EXTRACTION_CLASSES = {
    "vendor",
    "invoice_no",
    "po_number",
    "invoice_date",
    "due_date",
    "subtotal",
    "tax",
    "total",
    "currency",
    "payment_terms",
    "bank_details",
    "line_item",
}

PROMPT = """\
Extract approval-relevant fields from this invoice. Use these extraction classes:
vendor, invoice_no, po_number, invoice_date, due_date, subtotal, tax, total,
currency, payment_terms, bank_details, and line_item (one per row, with attributes
desc, qty, unit_price, amount).

Rules:
- Use the exact verbatim text from the source for each extraction_text (do not
  paraphrase or reformat) so each field can be traced back to its location.
- Only extract a field if it actually appears in the text. Do NOT infer, guess, or
  fabricate. If a field is absent, simply emit no extraction for it.
- Emit dates and amounts as they appear in the document.\
"""


class LineItem(BaseModel):
    """One invoice line; each column carries its own value/confidence/grounding."""

    desc: FieldValue
    qty: FieldValue
    unit_price: FieldValue
    amount: FieldValue


class InvoiceFields(BaseModel):
    """Approval-relevant invoice fields (TASK Phase 4)."""

    vendor: FieldValue
    invoice_no: FieldValue
    po_number: FieldValue
    invoice_date: FieldValue
    due_date: FieldValue
    line_items: list[LineItem]
    subtotal: FieldValue
    tax: FieldValue
    total: FieldValue
    currency: FieldValue
    payment_terms: FieldValue
    bank_details_present: FieldValue


def _line_item(flat: FlatExtraction, ctx: GroundingCtx) -> LineItem:
    """Build a LineItem from a row extraction's attributes, grounded to the row span."""
    grounding, confidence = ground_field(flat, ctx)
    return LineItem(
        desc=attr_field(flat, "desc", ctx, grounding, confidence, to_text),
        qty=attr_field(flat, "qty", ctx, grounding, confidence, to_number),
        unit_price=attr_field(flat, "unit_price", ctx, grounding, confidence, to_number),
        amount=attr_field(flat, "amount", ctx, grounding, confidence, to_number),
    )


def assemble_invoice(flats: list[FlatExtraction], ctx: GroundingCtx) -> InvoiceFields:
    """Turn flat extractions into a validated InvoiceFields model."""
    grouped = group_by_class(flats)
    return InvoiceFields(
        vendor=scalar_field(grouped, "vendor", ctx, to_text),
        invoice_no=scalar_field(grouped, "invoice_no", ctx, to_text),
        po_number=scalar_field(grouped, "po_number", ctx, to_text),
        invoice_date=scalar_field(grouped, "invoice_date", ctx, to_text),
        due_date=scalar_field(grouped, "due_date", ctx, to_text),
        line_items=[_line_item(f, ctx) for f in grouped.get("line_item", [])],
        subtotal=scalar_field(grouped, "subtotal", ctx, to_number),
        tax=scalar_field(grouped, "tax", ctx, to_number),
        total=scalar_field(grouped, "total", ctx, to_number),
        currency=scalar_field(grouped, "currency", ctx, to_text),
        payment_terms=scalar_field(grouped, "payment_terms", ctx, to_text),
        bank_details_present=presence_field(grouped, "bank_details", ctx),
    )


def _examples() -> list:
    """Few-shot examples (lazy: imports langextract only when the engine runs)."""
    import langextract as lx

    return [
        lx.data.ExampleData(
            text=(
                "Acme Supplies Inc.\n"
                "Invoice #INV-2024-001   PO: PO-5567\n"
                "Date: 2024-03-01   Due: 2024-03-31\n"
                "10 x Widget @ 12.50 = 125.00\n"
                "Subtotal: 125.00  Tax: 10.00  Total: $135.00 USD\n"
                "Payment terms: Net 30\n"
                "Remit to IBAN GB29 NWBK 6016 1331 9268 19"
            ),
            extractions=[
                lx.data.Extraction(extraction_class="vendor", extraction_text="Acme Supplies Inc."),
                lx.data.Extraction(extraction_class="invoice_no", extraction_text="INV-2024-001"),
                lx.data.Extraction(extraction_class="po_number", extraction_text="PO-5567"),
                lx.data.Extraction(extraction_class="invoice_date", extraction_text="2024-03-01"),
                lx.data.Extraction(extraction_class="due_date", extraction_text="2024-03-31"),
                lx.data.Extraction(
                    extraction_class="line_item",
                    extraction_text="10 x Widget @ 12.50 = 125.00",
                    attributes={
                        "desc": "Widget",
                        "qty": "10",
                        "unit_price": "12.50",
                        "amount": "125.00",
                    },
                ),
                lx.data.Extraction(extraction_class="subtotal", extraction_text="125.00"),
                lx.data.Extraction(extraction_class="tax", extraction_text="10.00"),
                lx.data.Extraction(extraction_class="total", extraction_text="$135.00"),
                lx.data.Extraction(extraction_class="currency", extraction_text="USD"),
                lx.data.Extraction(extraction_class="payment_terms", extraction_text="Net 30"),
                lx.data.Extraction(
                    extraction_class="bank_details",
                    extraction_text="IBAN GB29 NWBK 6016 1331 9268 19",
                ),
            ],
        ),
        lx.data.ExampleData(
            # Second example deliberately omits PO and bank details -> the model
            # learns to leave absent fields unextracted rather than invent them.
            text=(
                "Globex Ltd\n"
                "Invoice No: 7781   Issued 05/02/2024\n"
                "Consulting services .......... 2,000.00\n"
                "Total due: 2,000.00 EUR"
            ),
            extractions=[
                lx.data.Extraction(extraction_class="vendor", extraction_text="Globex Ltd"),
                lx.data.Extraction(extraction_class="invoice_no", extraction_text="7781"),
                lx.data.Extraction(extraction_class="invoice_date", extraction_text="05/02/2024"),
                lx.data.Extraction(
                    extraction_class="line_item",
                    extraction_text="Consulting services .......... 2,000.00",
                    attributes={"desc": "Consulting services", "amount": "2,000.00"},
                ),
                lx.data.Extraction(extraction_class="total", extraction_text="2,000.00"),
                lx.data.Extraction(extraction_class="currency", extraction_text="EUR"),
            ],
        ),
    ]


SPEC = DocTypeSpec(
    prompt=PROMPT,
    examples_factory=_examples,
    extraction_classes=EXTRACTION_CLASSES,
    field_model=InvoiceFields,
    assemble=assemble_invoice,
    core_paths=["vendor", "invoice_no", "total", "line_items"],
)
