.PHONY: install warm dev dev-backend dev-frontend test reset

# One-time setup: backend deps (PyPI, hardened) + frontend deps.
install:
	cd backend && uv sync --extra ocr --extra langextract --extra agent
	pnpm install

# Pre-download/load the OCR models to disk so the first request on camera is fast
# (Docling is slow to load cold). Run once after install, before recording. The
# "qwen-vl" engine is a remote VLM with no local models, so its warm step is a no-op.
warm:
	cd backend && PYTORCH_ENABLE_MPS_FALLBACK=1 uv run --no-sync python -c \
		"from app.pipeline.ocr import prewarm, available_engines; prewarm([e for e in available_engines() if e != 'mock'])"

# Run backend (:8000) and frontend (:5173) together. Ctrl+C stops both.
dev:
	@trap 'kill 0' EXIT; \
	(cd backend && PYTORCH_ENABLE_MPS_FALLBACK=1 uv run uvicorn app.main:app --reload --port 8000) & \
	pnpm dev; \
	wait

# Backend only — FastAPI on :8000 with autoreload.
dev-backend:
	cd backend && PYTORCH_ENABLE_MPS_FALLBACK=1 uv run uvicorn app.main:app --reload --port 8000

# Frontend only — Vite dev server on :5173.
dev-frontend:
	pnpm dev

# Backend test suite (offline; uses the mock engine/provider — no models or API key).
test:
	cd backend && uv run --no-sync pytest -q

# Clear uploaded files + SQLite DB (fresh demo state).
reset:
	rm -rf backend/data
	@echo "Cleared backend/data/"
