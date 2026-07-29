"""Phase 2 pre-flight orchestration for a single document.

Loads each rasterized page, computes advisory quality metrics, optionally writes
cleaned (deskewed / grayscale / threshold) variants for OCR + the demo toggle, and
assembles a :class:`QualityReport`. File I/O + ``settings`` live here; the actual CV
lives in :mod:`metrics` / :mod:`preprocess`. No FastAPI / SQLModel imports, so this
is callable from tests and a future orchestrator.
"""

from __future__ import annotations

import cv2

from app import storage
from app.config import settings
from app.models import Document, DocumentStatus
from app.pipeline import metrics, preprocess
from app.schemas import MetricResult, PageQuality, QualityReport


def _page_reasons(page: PageQuality) -> list[str]:
    """Human-readable notes for each non-pass metric on a page."""
    reasons: list[str] = []
    if page.resolution.verdict == "warn":
        reasons.append(
            f"low resolution (~{page.resolution.value:.0f} DPI, "
            f"recommended >= {settings.min_dpi})"
        )
    if page.sharpness.verdict == "warn":
        reasons.append(
            f"possibly blurry (sharpness {page.sharpness.value:.0f}, "
            f"recommended >= {settings.blur_warn:.0f})"
        )
    if page.contrast.verdict == "warn":
        reasons.append(f"low contrast (std {page.contrast.value:.0f})")
    if page.brightness.verdict == "warn":
        reasons.append(f"too dark (brightness {page.brightness.value:.0f})")
    if page.deskewed:
        reasons.append(f"skewed by {page.skew_angle_deg:.1f}deg, auto-deskewed")
    return reasons


def run_prescan(doc: Document, *, deskew: bool = True, clean: bool = False) -> QualityReport:
    """Compute the pre-flight report for ``doc`` and write any cleaned page variants."""
    source = "pdf" if doc.mime == "application/pdf" else "image"
    pages: list[PageQuality] = []
    preprocess_applied = False
    urls = storage.page_urls(doc.id, doc.page_count)

    for page_no in range(1, doc.page_count + 1):
        path = storage.page_path(doc.id, page_no)
        bgr = cv2.imread(str(path), cv2.IMREAD_COLOR)
        if bgr is None:
            raise FileNotFoundError(f"missing rasterized page: {path}")
        gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
        h, w = gray.shape[:2]

        dpi_value, dpi_verdict = metrics.resolution_metric(
            w,
            h,
            source=source,
            render_dpi=settings.render_dpi,
            assumed_height_in=settings.assumed_page_height_in,
            min_dpi=settings.min_dpi,
        )
        blur_value, blur_verdict = metrics.sharpness_metric(
            gray,
            normalize_width=settings.prescan_normalize_width,
            blur_warn=settings.blur_warn,
        )
        std, mean = metrics.contrast_brightness(gray)
        blank = metrics.near_blank(gray, ink_ratio_max=settings.blank_ink_ratio)
        contrast_verdict = metrics.contrast_metric(
            std, contrast_warn=settings.contrast_warn, blank=blank
        )
        brightness_verdict = metrics.brightness_metric(
            mean, brightness_dark=settings.brightness_dark
        )
        # A near-blank page has no meaningful text to straighten; skip deskew so a
        # spurious angle can't rotate (and warn on) an essentially empty page.
        angle = 0.0 if blank else preprocess.detect_skew_angle(gray)

        deskewed_url: str | None = None
        gray_url: str | None = None
        thresh_url: str | None = None
        did_deskew = False

        # Preprocessing artifacts: deskew (default) + optional grayscale/threshold.
        working = bgr
        if deskew and abs(angle) >= settings.skew_deskew_deg:
            working = preprocess.deskew(bgr, angle)
            storage.save_prescan_page(doc.id, page_no, "deskewed", working)
            deskewed_url = storage.prescan_url(doc.id, page_no, "deskewed")
            did_deskew = True
            preprocess_applied = True

        if clean:
            cleaned_gray = preprocess.to_grayscale(working)
            storage.save_prescan_page(doc.id, page_no, "gray", cleaned_gray)
            storage.save_prescan_page(
                doc.id, page_no, "thresh", preprocess.adaptive_threshold(cleaned_gray)
            )
            gray_url = storage.prescan_url(doc.id, page_no, "gray")
            thresh_url = storage.prescan_url(doc.id, page_no, "thresh")
            preprocess_applied = True

        page = PageQuality(
            page=page_no,
            width_px=w,
            height_px=h,
            resolution=MetricResult(
                value=dpi_value, verdict=dpi_verdict, threshold=float(settings.min_dpi)
            ),
            sharpness=MetricResult(
                value=blur_value, verdict=blur_verdict, threshold=settings.blur_warn
            ),
            contrast=MetricResult(
                value=round(std, 1), verdict=contrast_verdict, threshold=settings.contrast_warn
            ),
            brightness=MetricResult(value=round(mean, 1), verdict=brightness_verdict),
            skew_angle_deg=angle,
            verdict=metrics.worst(dpi_verdict, blur_verdict, contrast_verdict, brightness_verdict),
            reasons=[],
            deskewed=did_deskew,
            image_url=str(urls[page_no - 1]["image_url"]),
            deskewed_url=deskewed_url,
            gray_url=gray_url,
            thresh_url=thresh_url,
        )
        page.reasons = _page_reasons(page)
        pages.append(page)

    doc_verdict = metrics.worst(*(p.verdict for p in pages)) if pages else "pass"
    aggregated: list[str] = []
    for p in pages:
        for reason in p.reasons:
            entry = f"page {p.page}: {reason}"
            if entry not in aggregated:
                aggregated.append(entry)

    return QualityReport(
        document_id=doc.id,
        status=DocumentStatus.prescanned,
        verdict=doc_verdict,
        reasons=aggregated,
        preprocess_applied=preprocess_applied,
        pages=pages,
    )
