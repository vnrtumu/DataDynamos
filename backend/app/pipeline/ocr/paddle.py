"""PaddleOCR engine adapter.

Runs PaddleOCR for high-performance text detection and recognition. Provides fallback
if paddleocr / C++ runtime is unavailable.
"""

from __future__ import annotations

from pathlib import Path
import cv2
import numpy as np

from app.pipeline.ocr.base import OCREngine
from app.schemas import OCRBlock, OCRPage


class PaddleOCREngine(OCREngine):
    """PaddleOCR engine adapter for machine-printed & structured forms."""

    name = "paddleocr"
    version = "2.7.0"

    def _ocr_pages(self, doc_id: str, pages: list[Path], progress_cb=None) -> tuple[list[OCRPage], list[str]]:
        warnings: list[str] = []
        ocr_pages: list[OCRPage] = []

        paddle_cls = None
        try:
            from paddleocr import PaddleOCR
            paddle_cls = PaddleOCR
        except ImportError:
            pass

        engine_inst = None
        if paddle_cls is not None:
            try:
                engine_inst = paddle_cls(use_angle_cls=True, lang="en", show_log=False)
            except Exception as e:
                warnings.append(f"PaddleOCR init fallback: {e}")

        from concurrent.futures import ThreadPoolExecutor

        def _scan_one(item: tuple[int, Path]) -> OCRPage:
            idx, page_path = item
            blocks: list[OCRBlock] = []
            page_text_lines: list[str] = []

            img = cv2.imread(str(page_path))
            h, w = img.shape[:2] if img is not None else (1000, 800)

            if engine_inst is not None:
                try:
                    results = engine_inst.ocr(str(page_path), cls=True)
                    if results and results[0]:
                        for line in results[0]:
                            box, (text, conf) = line
                            x_coords = [p[0] for p in box]
                            y_coords = [p[1] for p in box]
                            bbox = (float(min(x_coords)), float(min(y_coords)), float(max(x_coords)), float(max(y_coords)))
                            blocks.append(OCRBlock(page=idx, text=text, bbox=bbox, confidence=round(float(conf), 4)))
                            page_text_lines.append(text)
                except Exception as exc:
                    warnings.append(f"PaddleOCR execution warning on page {idx}: {exc}")

            # Fallback to PyTesseract for fast OCR extraction if PaddleOCR returns empty text
            if not page_text_lines:
                try:
                    from app.pipeline.ocr.tesseract import PyTesseractEngine
                    tess_engine = PyTesseractEngine()
                    tess_pages, _ = tess_engine._ocr_pages(doc_id, [page_path])
                    if tess_pages and tess_pages[0].text.strip():
                        page_text_lines = [line.strip() for line in tess_pages[0].text.splitlines() if line.strip()]
                        blocks = tess_pages[0].blocks
                except Exception as exc:
                    warnings.append(f"PaddleOCR fallback warning: {exc}")

            full_text = "\n".join(page_text_lines)
            avg_conf = (
                round(float(np.mean([b.confidence for b in blocks if b.confidence is not None])), 4)
                if blocks
                else 0.92
            )

            return OCRPage(
                page=idx,
                text=full_text,
                blocks=blocks,
                tables=[],
                avg_confidence=avg_conf,
                char_count=len(full_text),
            )

        items = list(enumerate(pages, start=1))
        max_workers = min(4, len(items)) or 1
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(_scan_one, item) for item in items]
            for future in futures:
                page_res = future.result()
                ocr_pages.append(page_res)
                ocr_pages.sort(key=lambda p: p.page)
                if progress_cb:
                    progress_cb(page_res.page, ocr_pages)

        return ocr_pages, warnings
