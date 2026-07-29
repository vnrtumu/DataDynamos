"""Pure CV preprocessing utilities for the Phase 2 pre-flight pass.

Each is a small, toggleable transform. ``deskew`` feeds a straightened image into
OCR; ``to_grayscale`` / ``adaptive_threshold`` produce the extra "cleaned" variants
used for the raw-vs-cleaned demo toggle (Phase 6). No FastAPI / SQLModel imports.
"""

from __future__ import annotations

import cv2
import numpy as np


def detect_skew_angle(gray: np.ndarray) -> float:
    """Estimate document skew in degrees via the min-area rect of text pixels.

    Returns a correction-friendly angle in (-45, 45]: positive means the page is
    rotated counter-clockwise. Pass the result straight to :func:`deskew`. Returns
    ``0.0`` when there's no foreground to measure (e.g. a blank page).
    """
    # Otsu inverse threshold so text becomes white foreground on black.
    _, thresh = cv2.threshold(
        gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU
    )
    coords = np.column_stack(np.where(thresh > 0))
    if coords.shape[0] < 50:  # too few foreground pixels to trust an angle
        return 0.0

    angle = cv2.minAreaRect(coords)[-1]
    # Normalize to a small correction angle in (-45, 45], handling BOTH OpenCV
    # conventions: pre-4.5 reports [-90, 0); 4.5+ reports (0, 90]. Without the
    # `> 45` branch, an upright page reads as 90° on OpenCV 4.5+ and gets bogusly
    # "deskewed" by 90° (the cause of false skew warns on clean multi-page PDFs).
    if angle < -45:
        angle += 90
    elif angle > 45:
        angle -= 90
    return round(float(angle), 2)


def deskew(image: np.ndarray, angle: float) -> np.ndarray:
    """Rotate ``image`` by ``angle`` degrees about its center to straighten it.

    Uses ``BORDER_REPLICATE`` so the corners stay clean (no black wedges) on camera.
    Works on grayscale or BGR arrays.
    """
    h, w = image.shape[:2]
    matrix = cv2.getRotationMatrix2D((w / 2, h / 2), angle, 1.0)
    return cv2.warpAffine(
        image,
        matrix,
        (w, h),
        flags=cv2.INTER_CUBIC,
        borderMode=cv2.BORDER_REPLICATE,
    )


def to_grayscale(image: np.ndarray) -> np.ndarray:
    """Convert a BGR image to single-channel grayscale (passthrough if already 2-D)."""
    if image.ndim == 2:
        return image
    return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)


def adaptive_threshold(gray: np.ndarray) -> np.ndarray:
    """Binarize via adaptive Gaussian thresholding — the high-contrast "cleaned" look."""
    return cv2.adaptiveThreshold(
        gray,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        blockSize=31,
        C=15,
    )
