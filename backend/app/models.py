"""Database models (SQLModel tables) for documents and pipeline runs."""

from datetime import datetime, timezone
from enum import Enum
from uuid import uuid4

from sqlalchemy import Column
from sqlalchemy.types import JSON
from sqlmodel import Field, SQLModel


def _new_id() -> str:
    """A short, filesystem-friendly unique id (also used as the data/<id>/ dir name)."""
    return uuid4().hex


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class DocumentStatus(str, Enum):
    """Lifecycle of a document through the 4-stage pipeline."""

    uploaded = "uploaded"
    prescanned = "prescanned"
    ocr_done = "ocr_done"
    structured = "structured"
    decided = "decided"
    needs_review = "needs_review"


class DocType(str, Enum):
    """The two document kinds this POC handles."""

    contract = "contract"
    invoice = "invoice"


class Document(SQLModel, table=True):
    """An uploaded document plus its ingestion metadata."""

    id: str = Field(default_factory=_new_id, primary_key=True)
    filename: str
    doc_type: DocType | None = None
    mime: str
    page_count: int = 0
    status: DocumentStatus = Field(default=DocumentStatus.uploaded)
    created_at: datetime = Field(default_factory=_utcnow)


class PipelineRun(SQLModel, table=True):
    """A run of the pipeline against a document. Stage results accumulate as JSON.

    Defined now (Phase 1); the prescan/OCR/structure/decide stages populate
    ``stage_results`` in Phases 2-5.
    """

    id: str = Field(default_factory=_new_id, primary_key=True)
    document_id: str = Field(foreign_key="document.id", index=True)
    status: str = "pending"
    stage_results: dict = Field(default_factory=dict, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)
