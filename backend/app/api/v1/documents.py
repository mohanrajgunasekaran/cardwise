import os
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.models import SourceDocument, User
from app.schemas.schemas import SourceDocumentResponse
from app.api.deps import get_current_user

router = APIRouter()

DOCS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "docs", "official_documents"))

@router.get("", response_model=List[SourceDocumentResponse])
def list_documents(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List all cataloged official bank documents with provenance and status.
    """
    return db.query(SourceDocument).order_by(SourceDocument.issuer.asc(), SourceDocument.document_title.asc()).all()

@router.get("/{doc_id}", response_model=SourceDocumentResponse)
def get_document(
    doc_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieve metadata for a specific official document.
    """
    doc = db.query(SourceDocument).filter(SourceDocument.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Official document not found")
    return doc

@router.get("/{doc_id}/file")
def view_document_file(
    doc_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Serve the official bank PDF document directly for inline viewing or download.
    """
    doc = db.query(SourceDocument).filter(SourceDocument.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Official document not found")
    
    file_path = os.path.join(DOCS_DIR, doc.file_name)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"PDF file '{doc.file_name}' not found on server")
    
    return FileResponse(
        path=file_path,
        media_type="application/pdf",
        filename=doc.file_name,
        headers={"Content-Disposition": f"inline; filename=\"{doc.file_name}\""}
    )
