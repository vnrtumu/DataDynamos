"""OCR engine layer: a registry of swappable engines + the stage entrypoint.

Adapters keep their heavy ML imports lazy, so importing this package is cheap and
the app boots without the optional OCR deps installed.
"""

from __future__ import annotations

from app.models import Document
from app.schemas import OCRResult

from .base import OCREngine
from .docling import DoclingEngine
from .mock import MockEngine
from .qwen_vl import QwenVLEngine

# Engine name -> factory. The route validates ?engine= against these keys.
ENGINES: dict[str, type[OCREngine]] = {
    "qwen-vl": QwenVLEngine,
    "docling": DoclingEngine,
    "mock": MockEngine,
}


def available_engines() -> list[str]:
    """Names accepted by the OCR route's ``engine`` parameter."""
    return list(ENGINES)


def run_ocr(doc: Document, engine_name: str) -> OCRResult:
    """Run the named engine over the document's pages, returning a normalized result."""
    factory = ENGINES.get(engine_name)
    if factory is None:
        raise ValueError(
            f"Unknown OCR engine '{engine_name}'. Available: {', '.join(ENGINES)}"
        )
    return factory().run(doc)


def prewarm(engine_names: list[str], *, log=print) -> None:
    """Load each named engine's models so the first real request is fast.

    Skips ``mock`` (nothing to load). Each engine warms independently; a failure
    (e.g. an uninstalled optional dep) is logged and skipped, never raised.
    """
    for name in engine_names:
        if name == "mock":
            continue
        factory = ENGINES.get(name)
        if factory is None:
            continue
        try:
            log(f"[prewarm] loading {name} models…")
            factory().warm()
            log(f"[prewarm] {name} ready")
        except Exception as exc:  # noqa: BLE001 — warming is best-effort
            log(f"[prewarm] {name} skipped: {type(exc).__name__}: {exc}")


__all__ = ["ENGINES", "available_engines", "run_ocr", "prewarm", "OCREngine"]
