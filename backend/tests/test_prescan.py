"""Phase 2 pre-flight tests: pure CV metrics + the prescan route end-to-end."""

import cv2
import numpy as np
from fastapi.testclient import TestClient

from app.config import settings
from app.main import app
from app.pipeline import metrics, preprocess
from tests.conftest import SAMPLES


def _gray(name: str):
    img = cv2.imread(str(SAMPLES / name), cv2.IMREAD_GRAYSCALE)
    assert img is not None, f"sample not found / unreadable: {name}"
    return img


# --- pure metric functions ---------------------------------------------------


def test_sharpness_separates_blurry_from_sharp():
    blurry, blurry_verdict = metrics.sharpness_metric(
        _gray("scan-lowres-skewed.jpg"),
        normalize_width=settings.prescan_normalize_width,
        blur_warn=settings.blur_warn,
    )
    sharp, sharp_verdict = metrics.sharpness_metric(
        _gray("invoice-gen.jpg"),
        normalize_width=settings.prescan_normalize_width,
        blur_warn=settings.blur_warn,
    )
    assert blurry_verdict == "warn"
    assert sharp_verdict == "pass"
    assert sharp > blurry


def test_degraded_image_low_contrast_warns():
    std, _mean = metrics.contrast_brightness(_gray("degraded.png"))
    assert metrics.contrast_metric(std, contrast_warn=settings.contrast_warn) == "warn"


def test_deskew_reduces_skew_angle():
    gray = _gray("scan-lowres-skewed.jpg")
    angle = preprocess.detect_skew_angle(gray)
    straightened = preprocess.deskew(gray, angle)
    residual = preprocess.detect_skew_angle(straightened)
    assert abs(residual) <= abs(angle) + 0.5  # deskew never makes it worse


def test_upright_text_is_not_read_as_90deg_skew():
    """Regression: OpenCV 4.5+ reports minAreaRect angles in (0, 90], so an upright
    page must normalize to ~0, not 90 (which would bogusly 'deskew' clean pages)."""
    img = np.full((300, 500), 255, dtype=np.uint8)
    for y in range(40, 260, 30):  # horizontal text-like bars
        cv2.rectangle(img, (40, y), (460, y + 12), 0, -1)
    angle = preprocess.detect_skew_angle(img)
    assert abs(angle) < 5.0, f"upright page read as {angle}deg skew"


def test_near_blank_page_is_exempt_from_contrast_warn():
    """A sparse near-white page (e.g. a signature page) shouldn't trip low-contrast."""
    blank = np.full((300, 300), 255, dtype=np.uint8)
    cv2.rectangle(blank, (120, 250), (180, 262), 0, -1)  # one tiny mark
    assert metrics.near_blank(blank, ink_ratio_max=settings.blank_ink_ratio) is True
    std, _ = metrics.contrast_brightness(blank)
    assert metrics.contrast_metric(std, contrast_warn=settings.contrast_warn, blank=True) == "pass"

    dense = _gray("degraded.png")  # real, content-rich page
    assert metrics.near_blank(dense, ink_ratio_max=settings.blank_ink_ratio) is False


def test_pdf_effective_dpi_is_render_dpi():
    dpi = metrics.effective_dpi(
        100, 100, source="pdf", render_dpi=settings.render_dpi, assumed_height_in=11.0
    )
    assert dpi == float(settings.render_dpi)


# --- route end-to-end --------------------------------------------------------


def _upload(client: TestClient, name: str) -> str:
    with (SAMPLES / name).open("rb") as fh:
        resp = client.post("/documents", files={"file": (name, fh)})
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


def test_prescan_route_persists_and_advances_status():
    with TestClient(app) as client:
        doc_id = _upload(client, "invoice-clean.pdf")

        post = client.post(f"/documents/{doc_id}/prescan")
        assert post.status_code == 200, post.text
        report = post.json()
        assert report["status"] == "prescanned"
        assert report["verdict"] in {"pass", "warn"}
        assert len(report["pages"]) >= 1

        # status advanced on the document
        detail = client.get(f"/documents/{doc_id}").json()
        assert detail["status"] == "prescanned"

        # GET returns the same persisted report (no recompute)
        got = client.get(f"/documents/{doc_id}/prescan").json()
        assert got["verdict"] == report["verdict"]


def test_prescan_route_deskews_skewed_scan():
    with TestClient(app) as client:
        doc_id = _upload(client, "scan-lowres-skewed.jpg")
        report = client.post(f"/documents/{doc_id}/prescan", params={"clean": True}).json()

        page = report["pages"][0]
        assert page["verdict"] == "warn"  # low-res + blurry sample
        assert page["reasons"]  # human-readable notes present
        if page["deskewed"]:
            assert page["deskewed_url"] is not None
            variant = settings.data_path / doc_id / "prescan" / "page-001-deskewed.png"
            assert variant.exists()
        # clean=true always writes grayscale + threshold variants
        assert (settings.data_path / doc_id / "prescan" / "page-001-gray.png").exists()
        assert (settings.data_path / doc_id / "prescan" / "page-001-thresh.png").exists()


def test_prescan_missing_document_returns_404():
    with TestClient(app) as client:
        assert client.post("/documents/does-not-exist/prescan").status_code == 404
        assert client.get("/documents/does-not-exist/prescan").status_code == 404
