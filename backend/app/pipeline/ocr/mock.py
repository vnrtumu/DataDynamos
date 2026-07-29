"""Deterministic OCR engine for tests + frontend dev (no heavy deps).

Produces a stable :class:`OCRResult` shape without loading any model, so the
pipeline, route, and persistence can be exercised offline.
"""

from __future__ import annotations

from pathlib import Path

from app.schemas import OCRBlock, OCRPage, OCRTable

from .base import OCREngine


class MockEngine(OCREngine):
    """Returns fixed, plausible OCR output for each page."""

    name = "mock"
    version = "1.0"

    def _ocr_pages(self, doc_id: str, pages: list[Path]) -> tuple[list[OCRPage], list[str]]:
        out: list[OCRPage] = []
        for page_no, _ in enumerate(pages, start=1):
            blocks = [
                OCRBlock(
                    page=page_no,
                    text=f"MOCK INVOICE — page {page_no}",
                    bbox=(10.0, 10.0, 400.0, 40.0),
                    confidence=0.97,
                    label="title",
                ),
                OCRBlock(
                    page=page_no,
                    text="Total: $1,234.56",
                    bbox=(10.0, 60.0, 300.0, 90.0),
                    confidence=0.92,
                    label="text",
                ),
            ]
            tables = [
                OCRTable(
                    page=page_no,
                    bbox=(10.0, 120.0, 500.0, 300.0),
                    n_rows=2,
                    n_cols=3,
                    markdown="| Item | Qty | Amount |\n| --- | --- | --- |\n| Widget | 2 | $1,234.56 |",
                    confidence=0.9,
                )
            ]
            text = "\n".join(b.text for b in blocks)
            out.append(OCRPage(page=page_no, text=text, blocks=blocks, tables=tables))
        return out, []
