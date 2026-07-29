"""FastAPI entrypoint for the document auto-approval backend."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.db import init_db
from app.routes import documents, pipeline


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    if settings.pre_warm_models:
        # Warm OCR models off the startup path so the server is immediately live and
        # the first real request doesn't pay the cold model-load cost on camera.
        import threading

        from app.pipeline.ocr import available_engines, prewarm

        engines = [e for e in available_engines() if e != "mock"]
        threading.Thread(
            target=prewarm, args=(engines,), kwargs={"log": print}, daemon=True
        ).start()
    yield


app = FastAPI(title="Document Approval System", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    # The API is token-/cookie-free, so credentialed requests aren't needed. Leaving
    # this off also avoids the wildcard-origin footgun if cors_origins is ever widened.
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Importing app.db ensures the data dir exists; mount it for serving page images.
app.mount("/files", StaticFiles(directory=settings.data_path), name="files")

app.include_router(documents.router)
app.include_router(pipeline.router)


@app.get("/health")
def health() -> dict[str, str]:
    """Liveness probe used by the frontend status indicator."""
    return {"status": "ok"}
