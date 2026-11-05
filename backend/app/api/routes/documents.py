from fastapi import APIRouter, Depends, UploadFile, File, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.deps import get_tenant_context, TenantContext
from app.schemas.knowledge import DocumentImportResponse
from app.services.document_service import DocumentService

router = APIRouter(prefix="/documents", tags=["Document Processing"])


@router.post("/import", response_model=DocumentImportResponse, status_code=status.HTTP_201_CREATED)
async def import_document(
    file: UploadFile = File(..., description="Text-based PDF or Microsoft Word (.docx) brand book"),
    db: Session = Depends(get_db),
    ctx: TenantContext = Depends(get_tenant_context)
):
    """Upload a brand guidelines document (PDF or DOCX).
    Extracts text, identifies policy/governance rules, and stages them as candidate guidelines in DRAFT status.
    """
    return await DocumentService.import_document(db, ctx, file)

