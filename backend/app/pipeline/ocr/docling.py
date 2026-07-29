"""Docling adapter.

Runs Docling's standard pipeline (OCR + table structure) over each page image
and normalizes the result. Docling provides layout, reading order, tables, and
bbox provenance, but does not expose per-OCR-block confidence — so ``confidence``
is left ``None`` here (recorded honestly rather than faked).

The docling import + converter are lazy and cached so the app boots without the
optional dep and repeated runs reuse the loaded models.
"""

from __future__ import annotations

from pathlib import Path

from app import storage
from app.config import settings
from app.schemas import OCRBlock, OCRPage, OCRTable

from .base import OCREngine

_CONVERTER = None  # cached DocumentConverter across requests


def _accelerator_device(name: str):
    """Map our OCR_DEVICE setting to a docling AcceleratorDevice.

    Defaults to CPU. MPS (Apple GPU) is deliberately NOT the default: docling's
    models hit float64 ops that the MPS backend can't run ("Cannot convert a MPS
    Tensor to float64"), so CPU is the reliable on-device path for the demo.
    """
    from docling.datamodel.pipeline_options import AcceleratorDevice

    return {
        "cpu": AcceleratorDevice.CPU,
        "mps": AcceleratorDevice.MPS,
        "gpu": AcceleratorDevice.CUDA,
        "cuda": AcceleratorDevice.CUDA,
        "auto": AcceleratorDevice.AUTO,
    }.get(name.lower(), AcceleratorDevice.CPU)


def _converter():
    global _CONVERTER
    if _CONVERTER is None:
        from docling.datamodel.base_models import InputFormat  # lazy: heavy import
        from docling.datamodel.pipeline_options import AcceleratorOptions, PdfPipelineOptions
        from docling.document_converter import DocumentConverter, PdfFormatOption

        opts = PdfPipelineOptions(do_ocr=True, do_table_structure=True)
        opts.accelerator_options = AcceleratorOptions(
            device=_accelerator_device(settings.ocr_device)
        )
        _CONVERTER = DocumentConverter(
            format_options={InputFormat.IMAGE: PdfFormatOption(pipeline_options=opts)}
        )
    return _CONVERTER


def _bbox(item, doc) -> tuple[float, float, float, float]:
    """Best-effort top-left-origin pixel bbox from a docling item's provenance."""
    try:
        prov = item.prov[0]
        box = prov.bbox
        page = doc.pages.get(prov.page_no)
        if page is not None:
            box = box.to_top_left_origin(page_height=page.size.height)
        return (float(box.l), float(box.t), float(box.r), float(box.b))
    except Exception:
        return (0.0, 0.0, 0.0, 0.0)


class DoclingEngine(OCREngine):
    name = "docling"
    version = "docling"

    def _ocr_pages(self, doc_id: str, pages: list[Path]) -> tuple[list[OCRPage], list[str]]:
        conv = _converter()
        out: list[OCRPage] = []
        warnings: list[str] = []

        for page_no, path in enumerate(pages, start=1):
            doc = conv.convert(str(path)).document

            blocks = [
                OCRBlock(
                    page=page_no,
                    text=item.text,
                    bbox=_bbox(item, doc),
                    confidence=None,  # docling does not surface per-block OCR confidence
                    label=getattr(item.label, "value", str(item.label)),
                )
                for item in doc.texts
                if getattr(item, "text", "").strip()
            ]

            tables: list[OCRTable] = []
            for table in doc.tables:
                try:
                    md = table.export_to_markdown(doc=doc)
                except TypeError:
                    md = table.export_to_markdown()
                data = getattr(table, "data", None)
                tables.append(
                    OCRTable(
                        page=page_no,
                        bbox=_bbox(table, doc),
                        n_rows=getattr(data, "num_rows", 0) or 0,
                        n_cols=getattr(data, "num_cols", 0) or 0,
                        markdown=md,
                    )
                )

            markdown_url: str | None = None
            md_text = doc.export_to_markdown()
            if md_text:
                storage.save_ocr_markdown(doc_id, self.name, page_no, md_text)
                markdown_url = storage.ocr_markdown_url(doc_id, self.name, page_no)

            text = "\n".join(b.text for b in blocks)
            out.append(
                OCRPage(
                    page=page_no,
                    text=text,
                    blocks=blocks,
                    tables=tables,
                    markdown_url=markdown_url,
                )
            )

        warnings.append("docling does not expose per-block OCR confidence")
        return out, warnings
