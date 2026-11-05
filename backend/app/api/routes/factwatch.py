from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.deps import TenantContext, require_roles
from app.models.enums import UserRole
from app.services.factwatch_service import FactWatchService
router = APIRouter(prefix="/factwatch", tags=["FactWatch"])
@router.get("/")
def dashboard(horizon_days: int = Query(30, ge=1, le=365), db: Session = Depends(get_db), ctx: TenantContext = Depends(require_roles([UserRole.ADMIN]))): return FactWatchService.dashboard(db, ctx, horizon_days)
@router.put("/{fact_id}/review")
def review(fact_id: str, review_status: str, db: Session = Depends(get_db), ctx: TenantContext = Depends(require_roles([UserRole.ADMIN]))): return FactWatchService.review(db, ctx, fact_id, review_status)
