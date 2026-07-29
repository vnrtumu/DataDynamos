"""Qwen3-VL adapter (OCR via a vision-language model over OpenRouter).

A single engine name (``qwen-vl``): each page PNG is sent to a multimodal model
(default ``qwen/qwen3-vl-235b-a22b-instruct``) over OpenRouter's OpenAI-compatible
API, which transcribes it to faithful markdown (text + tables preserved).

Unlike Docling, a VLM returns text but *not* bounding boxes or per-block
confidence — so blocks here carry a zero bbox and ``confidence = None`` (recorded
honestly rather than faked). Docling stays the spatially-grounded engine; this one
trades the on-image highlight overlay for stronger transcription on hard pages.

The ``openai`` import is lazy (optional ``agent`` extra) and the API key is read at
call time, so the app boots and the offline tests run without the dep or a key.
"""

from __future__ import annotations

import base64
from pathlib import Path

from app import storage
from app.config import settings
from app.schemas import OCRBlock, OCRPage, OCRTable

from .base import OCREngine

_SYSTEM_PROMPT = (
    "You are a precise OCR engine. Transcribe the supplied document page to clean "
    "Markdown, preserving the original reading order. Render any tables as Markdown "
    "tables. Reproduce text exactly as written — never translate, summarize, "
    "correct, or invent content, and add no commentary. Output only the page's "
    "Markdown."
)
_USER_PROMPT = "Transcribe this page to Markdown."


def _extract_md_tables(markdown: str, page_no: int) -> list[OCRTable]:
    """Pull contiguous Markdown table blocks (a header + ``|---|`` separator) out.

    Best-effort: lets the table_count badge and the invoice table backfill work for
    VLM output too. No bbox (the model doesn't give one) — ``OCRTable.bbox`` is optional.
    """
    tables: list[OCRTable] = []
    block: list[str] = []

    def flush() -> None:
        # A real table needs a separator row (---) under the header.
        if len(block) >= 2 and any(set(c.strip()) <= {"-", ":", "|", " "} and "-" in c for c in block[1:2]):
            rows = [r for r in block if r.strip()]
            n_cols = max((r.count("|") - 1 for r in rows), default=0)
            tables.append(
                OCRTable(
                    page=page_no,
                    markdown="\n".join(block).strip(),
                    n_rows=max(len(rows) - 2, 0),  # minus header + separator
                    n_cols=max(n_cols, 0),
                )
            )
        block.clear()

    for line in markdown.splitlines():
        if "|" in line:
            block.append(line)
        else:
            flush()
    flush()
    return tables


class QwenVLEngine(OCREngine):
    name = "qwen-vl"

    def __init__(self, device: str | None = None) -> None:
        super().__init__(device)
        self.version = settings.ocr_vlm_model

    def _client(self):
        if not settings.openrouter_api_key:
            raise ValueError(
                "OPENROUTER_API_KEY is not set; the 'qwen-vl' OCR engine needs it."
            )
        import openai  # lazy: optional dep (the `agent` extra)

        return openai.OpenAI(
            api_key=settings.openrouter_api_key, base_url=settings.ocr_vlm_base_url
        )

    def _transcribe(self, client, path: Path) -> str:
        """One chat-completion: page image in, faithful Markdown out."""
        b64 = base64.b64encode(path.read_bytes()).decode("ascii")
        data_uri = f"data:image/png;base64,{b64}"
        try:
            response = client.chat.completions.create(
                model=settings.ocr_vlm_model,
                messages=[
                    {"role": "system", "content": _SYSTEM_PROMPT},
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": _USER_PROMPT},
                            {"type": "image_url", "image_url": {"url": data_uri}},
                        ],
                    },
                ],
                temperature=0,
            )
        except Exception as exc:  # noqa: BLE001 — surface as a clean 400, not a 500
            raise ValueError(f"Qwen-VL OCR request failed: {exc}") from exc
        return response.choices[0].message.content or ""

    def _ocr_pages(self, doc_id: str, pages: list[Path]) -> tuple[list[OCRPage], list[str]]:
        client = self._client()
        out: list[OCRPage] = []
        for page_no, path in enumerate(pages, start=1):
            markdown = self._transcribe(client, path)

            markdown_url: str | None = None
            if markdown:
                storage.save_ocr_markdown(doc_id, self.name, page_no, markdown)
                markdown_url = storage.ocr_markdown_url(doc_id, self.name, page_no)

            # No spatial info from a VLM: one page-spanning block, zero bbox, no conf.
            blocks = [
                OCRBlock(page=page_no, text=markdown, bbox=(0.0, 0.0, 0.0, 0.0), label="text")
            ]
            out.append(
                OCRPage(
                    page=page_no,
                    text=markdown,
                    blocks=blocks,
                    tables=_extract_md_tables(markdown, page_no),
                    markdown_url=markdown_url,
                )
            )
        return out, ["qwen-vl does not expose bounding boxes or per-block confidence"]

    def warm(self) -> None:
        """No-op: nothing loads locally, and the base warm() would fire a paid call."""
