"""OCR engine interface + shared aggregation.

Each engine implements only the engine-specific ``_ocr_pages`` step; the base
class handles timing, per-page/document confidence aggregation, and stamping the
normalized :class:`OCRResult`. This keeps adapters thin and guarantees both
engines emit the *same* shape so downstream stages stay engine-agnostic.

Heavy / optional imports (docling, the openai client for qwen-vl) live inside the
adapters' methods — never at module load — so the app boots without those deps.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from statistics import mean
from time import perf_counter

from app import storage
from app.config import settings
from app.models import Document, DocumentStatus
from app.schemas import OCRPage, OCRResult


class OCREngine(ABC):
    """Common contract for swappable OCR engines."""

    name: str = "base"
    version: str = "0"

    def __init__(self, device: str | None = None) -> None:
        self.device = device or settings.ocr_device

    @abstractmethod
    def _ocr_pages(self, doc_id: str, pages: list[Path]) -> tuple[list[OCRPage], list[str]]:
        """Run the engine over each page PNG. Returns (pages, warnings).

        Implementations set ``page``, ``text``, ``blocks``, ``tables`` and
        (optionally) ``markdown_url`` on each :class:`OCRPage`; the base class
        recomputes ``char_count``/``avg_confidence`` and the document rollups.
        """

    def run(self, doc: Document) -> OCRResult:
        """Execute OCR over the document's rasterized pages and aggregate."""
        page_paths = [storage.page_path(doc.id, n) for n in range(1, doc.page_count + 1)]

        start = perf_counter()
        pages, warnings = self._ocr_pages(doc.id, page_paths)
        latency_ms = int((perf_counter() - start) * 1000)

        all_confs: list[float] = []
        for page in pages:
            confs = [b.confidence for b in page.blocks if b.confidence is not None]
            page.char_count = len(page.text)
            page.avg_confidence = round(mean(confs), 4) if confs else None
            all_confs.extend(confs)

        avg_confidence = round(mean(all_confs), 4) if all_confs else None
        warnings = list(warnings)
        if avg_confidence is not None and avg_confidence < settings.ocr_confidence_warn:
            warnings.append(f"low average OCR confidence ({avg_confidence:.2f})")

        return OCRResult(
            document_id=doc.id,
            status=DocumentStatus.ocr_done,
            engine_name=self.name,
            engine_version=self.version,
            device=self.device,
            full_text="\n\n".join(p.text for p in pages),
            pages=pages,
            avg_confidence=avg_confidence,
            table_count=sum(len(p.tables) for p in pages),
            latency_ms=latency_ms,
            warnings=warnings,
        )

    def warm(self) -> None:
        """Load + exercise the engine's models on a tiny synthetic page.

        The first real OCR call otherwise pays the model download/load cost (PP-OCRv5
        was ~350s cold on CPU) — brutal on camera. Pre-warming at startup moves that
        cost off the critical path. Best-effort: the caller swallows failures so a warm
        problem never blocks the server.
        """
        import tempfile

        import cv2
        import numpy as np

        img = np.full((120, 400), 255, dtype=np.uint8)
        cv2.putText(img, "warmup 123", (10, 75), cv2.FONT_HERSHEY_SIMPLEX, 1.2, 0, 2)
        with tempfile.TemporaryDirectory() as tmp:
            page = Path(tmp) / "warm.png"
            cv2.imwrite(str(page), img)
            self._ocr_pages("warmup", [page])
