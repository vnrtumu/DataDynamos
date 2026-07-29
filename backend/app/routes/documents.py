"""Document ingestion + retrieval endpoints (Phase 1)."""

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlmodel import Session, delete, select

from app import storage
from app.config import settings
from app.db import get_session
from app.models import DocType, Document, PipelineRun
from app.schemas import DocumentDetail, DocumentSummary, PageInfo

router = APIRouter(prefix="/documents", tags=["documents"])


def _to_detail(doc: Document) -> DocumentDetail:
    pages = [PageInfo(**p) for p in storage.page_urls(doc.id, doc.page_count)]
    return DocumentDetail(**doc.model_dump(), pages=pages)


@router.post("", response_model=DocumentDetail, status_code=201)
async def upload_document(
    file: UploadFile = File(...),
    doc_type: DocType | None = Form(default=None),
    session: Session = Depends(get_session),
) -> DocumentDetail:
    """Upload a PDF/PNG/JPG/TIFF, persist it, and rasterize pages to PNGs."""
    try:
        ext, mime = storage.detect_type(file.filename or "")
    except storage.UnsupportedFileType:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported file type. Accepted: {', '.join(sorted(storage.ALLOWED_TYPES))}",
        ) from None

    content = await file.read()
    max_bytes = settings.max_upload_mb * 1024 * 1024
    if len(content) > max_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"File exceeds the {settings.max_upload_mb} MB upload limit.",
        )
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    doc = Document(filename=file.filename or f"upload{ext}", doc_type=doc_type, mime=mime)
    original = storage.save_original(doc.id, ext, content)
    try:
        doc.page_count = storage.normalize_to_pages(doc.id, original, mime)
    except Exception as exc:  # corrupt/unreadable file
        # Don't leak internal (PyMuPDF/Pillow) exception text to the client; the chained
        # `from exc` keeps the full traceback server-side for debugging.
        raise HTTPException(
            status_code=422, detail="Could not process file; it may be corrupt or unsupported."
        ) from exc

    session.add(doc)
    session.commit()
    session.refresh(doc)
    return _to_detail(doc)


@router.get("", response_model=list[DocumentSummary])
def list_documents(session: Session = Depends(get_session)) -> list[Document]:
    """List documents, newest first."""
    return session.exec(select(Document).order_by(Document.created_at.desc())).all()


@router.get("/{doc_id}", response_model=DocumentDetail)
def get_document(doc_id: str, session: Session = Depends(get_session)) -> DocumentDetail:
    """Document detail with per-page image + thumbnail URLs."""
    doc = session.get(Document, doc_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="Document not found.")
    return _to_detail(doc)


@router.delete("", status_code=204)
def delete_all_documents(session: Session = Depends(get_session)) -> None:
    """Permanently remove every document: all pipeline runs, DB rows, and files.

    Ids are collected before the rows are deleted so the on-disk ``data/<id>/``
    trees can be removed after the DB commit.
    """
    doc_ids = list(session.exec(select(Document.id)).all())
    session.exec(delete(PipelineRun))
    session.exec(delete(Document))
    session.commit()

    for doc_id in doc_ids:
        storage.delete_document_dir(doc_id)


@router.delete("/{doc_id}", status_code=204)
def delete_document(doc_id: str, session: Session = Depends(get_session)) -> None:
    """Permanently remove a document: its pipeline runs, DB row, and on-disk files.

    The PipelineRun -> Document foreign key has no DB cascade configured, so the
    runs are deleted explicitly before the document.
    """
    doc = session.get(Document, doc_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="Document not found.")

    session.exec(delete(PipelineRun).where(PipelineRun.document_id == doc_id))
    session.delete(doc)
    session.commit()

    storage.delete_document_dir(doc_id)
