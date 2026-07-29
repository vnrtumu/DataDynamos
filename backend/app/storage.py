"""Filesystem ingestion + normalization: save originals, rasterize to per-page PNGs.

On-disk layout per document::

    data/<doc_id>/
        original.<ext>
        pages/page-001.png      # full-res rasterized page
        thumbs/page-001.png     # downscaled preview

PDFs are rendered with PyMuPDF (fitz); images are normalized with Pillow.
"""

from __future__ import annotations

import logging
import shutil
from pathlib import Path

import fitz  # PyMuPDF
import numpy as np
from PIL import Image, ImageSequence

from app.config import settings

logger = logging.getLogger(__name__)

# Allowed upload types: extension -> canonical MIME.
ALLOWED_TYPES: dict[str, str] = {
    ".pdf": "application/pdf",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".tif": "image/tiff",
    ".tiff": "image/tiff",
}


class UnsupportedFileType(Exception):
    """Raised when an upload has an extension we don't accept."""


def _doc_dir(doc_id: str) -> Path:
    return settings.data_path / doc_id


def detect_type(filename: str) -> tuple[str, str]:
    """Return (lowercased extension, MIME) for an accepted file, else raise."""
    ext = Path(filename).suffix.lower()
    mime = ALLOWED_TYPES.get(ext)
    if mime is None:
        raise UnsupportedFileType(ext or filename)
    return ext, mime


def delete_document_dir(doc_id: str) -> None:
    """Recursively remove data/<doc_id>/ (originals, pages, thumbs, stage artifacts).

    A missing directory (e.g. a doc whose normalization failed before any file was
    written) is treated as success, so deletion stays idempotent. Real failures
    (permissions, a locked file) are logged rather than silently swallowed — the DB
    row is already gone, so a leftover tree is an orphan worth surfacing.
    """
    doc_dir = _doc_dir(doc_id)
    if not doc_dir.exists():
        return
    shutil.rmtree(
        doc_dir,
        onexc=lambda _func, path, exc: logger.warning(
            "Failed to delete %s while removing document %s: %s", path, doc_id, exc
        ),
    )


def save_original(doc_id: str, ext: str, content: bytes) -> Path:
    """Persist the raw upload bytes as data/<doc_id>/original.<ext>."""
    doc_dir = _doc_dir(doc_id)
    doc_dir.mkdir(parents=True, exist_ok=True)
    original = doc_dir / f"original{ext}"
    original.write_bytes(content)
    return original


def _save_page(doc_id: str, page_no: int, image: Image.Image) -> None:
    """Write one normalized page PNG + its thumbnail."""
    doc_dir = _doc_dir(doc_id)
    pages_dir = doc_dir / "pages"
    thumbs_dir = doc_dir / "thumbs"
    pages_dir.mkdir(parents=True, exist_ok=True)
    thumbs_dir.mkdir(parents=True, exist_ok=True)

    rgb = image.convert("RGB")
    name = f"page-{page_no:03d}.png"
    rgb.save(pages_dir / name, "PNG")

    # The full-res page is already written; downscale ``rgb`` in place for the thumb
    # (height is left effectively unbounded so the aspect ratio is preserved).
    rgb.thumbnail((settings.thumbnail_width, settings.thumbnail_width * 10))
    rgb.save(thumbs_dir / name, "PNG")


def normalize_to_pages(doc_id: str, original: Path, mime: str) -> int:
    """Render the original into per-page PNGs (+ thumbnails). Returns page count."""
    if mime == "application/pdf":
        return _normalize_pdf(doc_id, original)
    return _normalize_image(doc_id, original)


def _normalize_pdf(doc_id: str, original: Path) -> int:
    zoom = settings.render_dpi / 72.0  # PDF user space is 72 DPI.
    matrix = fitz.Matrix(zoom, zoom)
    with fitz.open(original) as pdf:
        for index, page in enumerate(pdf, start=1):
            pix = page.get_pixmap(matrix=matrix)
            image = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
            _save_page(doc_id, index, image)
        return pdf.page_count


def _normalize_image(doc_id: str, original: Path) -> int:
    """Single images become one page; multi-frame TIFFs become one page per frame."""
    page_no = 0
    with Image.open(original) as image:
        for frame in ImageSequence.Iterator(image):
            page_no += 1
            _save_page(doc_id, page_no, frame)
    return page_no


def page_urls(doc_id: str, page_count: int) -> list[dict[str, object]]:
    """Relative URLs (served via the /files static mount) for each page + thumbnail."""
    return [
        {
            "page": n,
            "image_url": f"/files/{doc_id}/pages/page-{n:03d}.png",
            "thumbnail_url": f"/files/{doc_id}/thumbs/page-{n:03d}.png",
        }
        for n in range(1, page_count + 1)
    ]


def page_path(doc_id: str, page_no: int) -> Path:
    """Absolute path to one rasterized full-res page PNG."""
    return _doc_dir(doc_id) / "pages" / f"page-{page_no:03d}.png"


# --- Phase 2: pre-flight preprocessing artifacts -----------------------------


def prescan_dir(doc_id: str) -> Path:
    """Directory holding cleaned (deskewed/grayscale/threshold) page variants."""
    return _doc_dir(doc_id) / "prescan"


def save_prescan_page(doc_id: str, page_no: int, variant: str, image: np.ndarray) -> Path:
    """Write a cleaned page variant as prescan/page-NNN-<variant>.png.

    Accepts an OpenCV ndarray: 2-D arrays are treated as grayscale, 3-D arrays
    as BGR (OpenCV's default channel order) and converted to RGB before saving.
    """
    out_dir = prescan_dir(doc_id)
    out_dir.mkdir(parents=True, exist_ok=True)

    if image.ndim == 2:
        pil = Image.fromarray(image, mode="L")
    else:
        pil = Image.fromarray(image[:, :, ::-1])  # BGR -> RGB

    path = out_dir / f"page-{page_no:03d}-{variant}.png"
    pil.save(path, "PNG")
    return path


def prescan_url(doc_id: str, page_no: int, variant: str) -> str:
    """Relative URL (served via /files) for a cleaned page variant."""
    return f"/files/{doc_id}/prescan/page-{page_no:03d}-{variant}.png"


# --- Phase 3: OCR artifacts (per-engine markdown) ----------------------------


def ocr_dir(doc_id: str, engine: str) -> Path:
    """Directory holding an engine's OCR artifacts, e.g. per-page markdown."""
    return _doc_dir(doc_id) / "ocr" / engine


def save_ocr_markdown(doc_id: str, engine: str, page_no: int, markdown: str) -> Path:
    """Write a page's OCR markdown as ocr/<engine>/page-NNN.md."""
    out_dir = ocr_dir(doc_id, engine)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"page-{page_no:03d}.md"
    path.write_text(markdown, encoding="utf-8")
    return path


def ocr_markdown_url(doc_id: str, engine: str, page_no: int) -> str:
    """Relative URL (served via /files) for a page's saved OCR markdown."""
    return f"/files/{doc_id}/ocr/{engine}/page-{page_no:03d}.md"


# --- Phase 4: structuring artifacts (raw extractor output) -------------------


def structure_dir(doc_id: str) -> Path:
    """Directory holding the structuring stage's raw extractor output."""
    return _doc_dir(doc_id) / "structure"


def save_structure_artifact(doc_id: str, content: str, name: str = "extractions.jsonl") -> Path:
    """Persist the raw extractor output (e.g. LangExtract JSONL) for debugging/demo."""
    out_dir = structure_dir(doc_id)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / name
    path.write_text(content, encoding="utf-8")
    return path


def structure_artifact_url(doc_id: str, name: str = "extractions.jsonl") -> str:
    """Relative URL (served via /files) for the saved structuring artifact."""
    return f"/files/{doc_id}/structure/{name}"
