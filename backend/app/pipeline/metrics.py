"""Pure image-quality metrics for the Phase 2 pre-flight pass.

These functions are deliberately framework-free (no FastAPI / SQLModel) so they
stay trivially unit-testable. Thresholds are passed in by the caller, which pulls
defaults from ``app.config.settings``. Every metric returns a ``("pass" | "warn")``
verdict plus the measured value — the pre-flight stage is advisory and never
hard-fails; the authoritative ``needs_review`` verdict comes from OCR confidence
in later phases.
"""

from __future__ import annotations

import cv2
import numpy as np

Verdict = str  # "pass" | "warn"


def effective_dpi(
    width_px: int,
    height_px: int,
    *,
    source: str,
    render_dpi: int,
    assumed_height_in: float,
) -> float:
    """Estimate the effective DPI of a page.

    PDF pages are rasterized at a known ``render_dpi`` so we report that directly.
    For uploaded images we have no physical size, so we estimate from the longer
    edge under a US-Letter (``assumed_height_in`` tall) assumption — orientation
    robust because we use ``max(width, height)``.
    """
    if source == "pdf":
        return float(render_dpi)
    return round(max(width_px, height_px) / assumed_height_in, 1)


def resolution_metric(
    width_px: int,
    height_px: int,
    *,
    source: str,
    render_dpi: int,
    assumed_height_in: float,
    min_dpi: int,
) -> tuple[float, Verdict]:
    """Effective DPI vs. ``min_dpi``. Below threshold -> warn."""
    dpi = effective_dpi(
        width_px,
        height_px,
        source=source,
        render_dpi=render_dpi,
        assumed_height_in=assumed_height_in,
    )
    verdict = "warn" if dpi < min_dpi else "pass"
    return dpi, verdict


def sharpness_metric(
    gray: np.ndarray,
    *,
    normalize_width: int,
    blur_warn: float,
) -> tuple[float, Verdict]:
    """Variance of the Laplacian (focus measure). Below ``blur_warn`` -> warn.

    The image is downscaled to ``normalize_width`` first so the score is
    comparable across a 1700px PDF render and a 784px phone photo.
    """
    h, w = gray.shape[:2]
    if w > normalize_width:
        scale = normalize_width / w
        gray = cv2.resize(gray, (normalize_width, max(1, int(h * scale))))
    variance = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    verdict = "warn" if variance < blur_warn else "pass"
    return round(variance, 1), verdict


def contrast_brightness(gray: np.ndarray) -> tuple[float, float]:
    """Return (std, mean) of pixel intensities — contrast and brightness proxies."""
    return float(gray.std()), float(gray.mean())


def near_blank(gray: np.ndarray, *, ink_ratio_max: float) -> bool:
    """True when a page is essentially empty (e.g. a sparse signature page).

    Such pages are mostly white and legitimately have a low pixel std, which would
    otherwise trip the low-contrast warn and drag a clean multi-page doc to ``warn``.
    We measure the fraction of clearly-non-background ("ink") pixels; below
    ``ink_ratio_max`` the page has too little content to judge contrast on.
    """
    return float((gray < 200).mean()) < ink_ratio_max


def contrast_metric(std: float, *, contrast_warn: float, blank: bool = False) -> Verdict:
    """Low pixel std means a washed-out / low-contrast page.

    A near-blank page (``blank=True``) is exempt: empty white pages have low std by
    nature, not because they're degraded.
    """
    if blank:
        return "pass"
    return "warn" if std < contrast_warn else "pass"


def brightness_metric(mean: float, *, brightness_dark: float) -> Verdict:
    """Warn only on too-dark pages.

    Clean documents are mostly white background and legitimately average ~245-250,
    so a high-brightness warn fires on every clean page. Washed-out / overexposed
    pages destroy information as *low contrast*, which the contrast metric catches —
    so brightness here is purely a darkness floor.
    """
    return "warn" if mean < brightness_dark else "pass"


def worst(*verdicts: Verdict) -> Verdict:
    """Aggregate verdicts: a single warn drags the result to warn."""
    return "warn" if any(v == "warn" for v in verdicts) else "pass"
