from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.deps import TenantContext, require_roles
from app.models.enums import UserRole
from app.services.guideline_health_service import GuidelineHealthService

router = APIRouter(prefix="/guideline-health", tags=["Guideline Health"])

@router.get("/")
def guideline_health(db: Session = Depends(get_db), ctx: TenantContext = Depends(require_roles([UserRole.ADMIN]))):
    return GuidelineHealthService.dashboard(db, ctx)
