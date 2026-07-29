"""Application settings, loaded from environment / .env file."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Repo path of the backend/ package, used to resolve relative storage paths.
BACKEND_ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    """Env-driven configuration for the document approval backend."""

    # OpenRouter agent (used from Phase 5 onward).
    openrouter_api_key: str = ""
    openrouter_model: str = "deepseek/deepseek-v4-flash"

    # Where uploaded files + the SQLite DB live (relative to backend/).
    data_dir: str = "data"

    # Ingestion settings (Phase 1).
    render_dpi: int = 200  # rasterize PDF pages to PNG at this DPI.
    thumbnail_width: int = 400  # max thumbnail width in px.
    max_upload_mb: int = 25

    # Pre-flight thresholds (Phase 2). Advisory/warn-only; the authoritative
    # needs_review verdict comes from OCR confidence later. Env-overridable.
    min_dpi: int = 100  # effective DPI below this -> warn.
    blur_warn: float = 60.0  # variance-of-Laplacian below this -> blurry.
    contrast_warn: float = 30.0  # pixel std below this -> low contrast.
    blank_ink_ratio: float = 0.01  # ink fraction below this -> near-blank (skips contrast warn).
    brightness_dark: float = 50.0  # pixel mean below this -> too dark.
    skew_deskew_deg: float = 2.0  # |skew| >= this -> auto-deskew.
    prescan_normalize_width: int = 1000  # downscale width before measuring sharpness.
    assumed_page_height_in: float = 11.0  # US-Letter assumption for effective DPI.
    prescan_timeout_s: float = 120.0  # over this -> 504, not a hang.

    # OCR engine layer (Phase 3). Engines swappable behind a common interface.
    ocr_default_engine: str = "docling"  # used when ?engine= is omitted.
    # Load OCR models at startup so the first request skips the cold download.
    # Off by default (fast boot for tests/dev); turn on for the demo via `make warm`.
    pre_warm_models: bool = False
    ocr_device: str = "cpu"  # "cpu" | "gpu" | "mps".
    # "qwen-vl": a VLM over OpenRouter. No local models (instant boot, bills per
    # call); reuses OPENROUTER_API_KEY and lazily imports the `agent` extra.
    ocr_vlm_model: str = "qwen/qwen3-vl-235b-a22b-instruct"
    ocr_vlm_base_url: str = "https://openrouter.ai/api/v1"
    ocr_confidence_warn: float = 0.80  # avg block confidence below this -> warn.
    ocr_timeout_s: float = 600.0  # generous to absorb a cold model download.
    llm_timeout_s: float = 120.0  # structuring + decision (network LLM).

    # Structuring layer (Phase 4). LangExtract turns OCR text into validated JSON;
    # the path is lazily imported, and the offline "mock" provider covers tests.
    structuring_provider: str = "langextract"  # "langextract" | "mock"
    # Verified live 2026-05-30 -> deepseek-v4-flash-20260423. Fallback: deepseek-v3.2.
    structuring_model: str = "deepseek/deepseek-v4-flash"
    structuring_base_url: str = "https://openrouter.ai/api/v1"
    structuring_max_char_buffer: int = 8000  # chunk size fed to the model.
    structuring_extraction_passes: int = 2  # >1 improves recall at ~2x latency.
    extraction_confidence_warn: float = 0.60  # overall conf below this -> warn.

    # Agent decision layer (Phase 5). A single OpenRouter call supplies qualitative
    # judgment; the deterministic rules below run in code and the LLM can never
    # override a hard failure. The "llm" path is lazily imported; "mock" is offline.
    decision_provider: str = "llm"  # "llm" | "mock"
    # Verified live 2026-05-30 -> deepseek-v4-flash-20260423; clean JSON output.
    decision_model: str = "deepseek/deepseek-v4-flash"
    decision_base_url: str = "https://openrouter.ai/api/v1"
    # Business-rule thresholds — editable so they can be tweaked live on camera.
    invoice_auto_approve_max: float = 10000.0  # total over this -> needs_review.
    invoice_total_tolerance: float = 0.01  # |total - (subtotal+tax)| allowance.
    invoice_flag_on_bank_details: bool = False  # True -> bank details = flag.
    contract_value_review_threshold: float = 100000.0  # value over this -> needs_review.
    contract_allowed_governing_law: list[str] = [
        "Delaware",
        "England and Wales",
        "New York",
        "California",
    ]

    # Browser origins allowed to call the API (Vite dev server by default).
    cors_origins: list[str] = ["http://localhost:5173"]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def data_path(self) -> Path:
        """Absolute path to the data dir, resolved relative to backend/."""
        path = Path(self.data_dir)
        return path if path.is_absolute() else BACKEND_ROOT / path


settings = Settings()
