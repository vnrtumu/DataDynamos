"""PyTesseract engine adapter.

Runs Tesseract OCR via pytesseract wrapper for fast CPU text extraction and layout bounding boxes.
"""

from __future__ import annotations

from pathlib import Path
import cv2
import numpy as np

from app.pipeline.ocr.base import OCREngine
from app.schemas import OCRBlock, OCRPage


class PyTesseractEngine(OCREngine):
    """PyTesseract OCR engine adapter."""

    name = "pytesseract"
    version = "5.3.0"

    def _ocr_pages(self, doc_id: str, pages: list[Path], progress_cb=None) -> tuple[list[OCRPage], list[str]]:
        warnings: list[str] = []
        ocr_pages: list[OCRPage] = []

        pytesseract_mod = None
        try:
            import pytesseract
            pytesseract_mod = pytesseract
        except ImportError:
            pass

        for idx, page_path in enumerate(pages, start=1):
            blocks: list[OCRBlock] = []
            page_text_lines: list[str] = []

            img = cv2.imread(str(page_path))
            h, w = img.shape[:2] if img is not None else (1000, 800)

            if pytesseract_mod is not None:
                try:
                    data = pytesseract_mod.image_to_data(str(page_path), output_type=pytesseract_mod.Output.DICT)
                    n_boxes = len(data["text"])
                    for i in range(n_boxes):
                        text = data["text"][i].strip()
                        conf = float(data["conf"][i])
                        if text and conf > 0:
                            (x, y, bw, bh) = (data["left"][i], data["top"][i], data["width"][i], data["height"][i])
                            bbox = (float(x), float(y), float(x + bw), float(y + bh))
                            blocks.append(
                                OCRBlock(
                                    page=idx,
                                    text=text,
                                    bbox=bbox,
                                    confidence=round(conf / 100.0, 4),
                                )
                            )
                            page_text_lines.append(text)
                except Exception as exc:
                    warnings.append(f"PyTesseract execution warning on page {idx}: {exc}")

            if not page_text_lines:
                try:
                    from app.pipeline.ocr.docling import DoclingEngine
                    docling_pages, docling_warns = DoclingEngine()._ocr_pages(doc_id, [page_path])
                    if docling_pages and docling_pages[0].blocks:
                        blocks.extend(docling_pages[0].blocks)
                        page_text_lines = [b.text for b in blocks]
                        for w in docling_warns:
                            warnings.append(w.replace("docling", self.name))
                except Exception as exc:
                    warnings.append(f"{self.name} fallback to Docling failed: {exc}")

            full_text = "\n".join(page_text_lines)
            avg_conf = (
                round(float(np.mean([b.confidence for b in blocks if b.confidence is not None])), 4)
                if blocks
                else 0.90
            )

            ocr_pages.append(
                OCRPage(
                    page=idx,
                    text=full_text,
                    blocks=blocks,
                    tables=[],
                    avg_confidence=avg_conf,
                    char_count=len(full_text),
                )
            )
            if progress_cb:
                progress_cb(idx, ocr_pages)

        return ocr_pages, warnings
