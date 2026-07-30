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


from app.schemas import AccuracyMetrics, CostSummary  # noqa: E402


def compute_cost_summary(
    doc_type: object | None,
    page_count: int,
    engine_name: str = "paddleocr",
    vlm_used: bool = False,
) -> CostSummary:
    """Compute exact line-item costs and projected cost per 1M documents."""
    type_str = str(getattr(doc_type, "value", doc_type or "cms1500"))

    tier_map = {
        "cms1500": "Tier A",
        "cms1500_multi": "Tier B",
        "ub04": "Tier C",
        "unstructured_claim": "Tier D",
    }
    tier_label = tier_map.get(type_str, "Tier A")

    preprocessing_cost = round(page_count * 0.0001, 5)

    engine_cost_map = {
        "paddleocr": 0.0002,
        "paddle": 0.0002,
        "pytesseract": 0.0001,
        "tesseract": 0.0001,
        "docling": 0.0005,
        "qwen-vl": 0.0030,
        "mock": 0.0001,
    }
    unit_ocr_cost = engine_cost_map.get(engine_name.lower(), 0.0002)
    ocr_engine_cost = round(page_count * unit_ocr_cost, 5)

    vlm_cost = 0.0035 if vlm_used else 0.0

    total_cost = round(preprocessing_cost + ocr_engine_cost + vlm_cost, 5)
    cost_per_million = round(total_cost * 1_000_000, 2)

    hitl = vlm_used or total_cost > 0.005
    hitl_cost = 0.45 if hitl else 0.0

    return CostSummary(
        tier=tier_label,
        preprocessing_cost=preprocessing_cost,
        ocr_engine_cost=ocr_engine_cost,
        vlm_llm_cost=vlm_cost,
        total_cost=total_cost,
        cost_per_million=cost_per_million,
        hitl_recommended=hitl,
        hitl_estimated_cost=hitl_cost,
    )


def compute_accuracy_metrics(
    extraction_confidence: float = 0.95,
    ocr_avg_confidence: float | None = 0.94,
    checks_passed_ratio: float = 1.0,
    grounding_ratio: float = 0.92,
) -> AccuracyMetrics:
    """Calculate composite extraction accuracy percentages."""
    ocr_conf_pct = round((ocr_avg_confidence or 0.90) * 100.0, 1)
    field_acc_pct = round(extraction_confidence * 100.0, 1)
    rule_pass_pct = round(checks_passed_ratio * 100.0, 1)
    ground_pct = round(grounding_ratio * 100.0, 1)

    overall = round(
        0.35 * field_acc_pct + 0.35 * rule_pass_pct + 0.15 * ocr_conf_pct + 0.15 * ground_pct,
        1,
    )

    return AccuracyMetrics(
        overall_accuracy=overall,
        field_accuracy=field_acc_pct,
        rule_pass_rate=rule_pass_pct,
        ocr_confidence=ocr_conf_pct,
        grounded_ratio=ground_pct,
    )
