from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.deps import get_tenant_context, require_roles, TenantContext
from app.models.enums import UserRole
from app.schemas.submission import DisputeCreateRequest, DisputeResolutionRequest, DisputeResponse
from app.services.dispute_service import DisputeService

router = APIRouter(prefix="/disputes", tags=["Human Review Disputes"])

@router.post("/", response_model=DisputeResponse, status_code=status.HTTP_201_CREATED)
def create_dispute(req: DisputeCreateRequest, db: Session = Depends(get_db), ctx: TenantContext = Depends(require_roles([UserRole.CREATOR, UserRole.ADMIN]))):
    return DisputeService.create(db, ctx, req)

@router.get("/", response_model=list[DisputeResponse])
def list_disputes(offset: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=100), queue_only: bool = False, db: Session = Depends(get_db), ctx: TenantContext = Depends(get_tenant_context)):
    return DisputeService.list(db, ctx, offset, limit, queue_only)

@router.get("/{dispute_id}", response_model=DisputeResponse)
def get_dispute(dispute_id: str, db: Session = Depends(get_db), ctx: TenantContext = Depends(get_tenant_context)):
    return DisputeService.get(db, ctx, dispute_id)

@router.post("/{dispute_id}/resolve", response_model=DisputeResponse)
def resolve_dispute(dispute_id: str, req: DisputeResolutionRequest, db: Session = Depends(get_db), ctx: TenantContext = Depends(require_roles([UserRole.ADMIN, UserRole.REVIEWER]))):
    return DisputeService.resolve(db, ctx, dispute_id, req)
