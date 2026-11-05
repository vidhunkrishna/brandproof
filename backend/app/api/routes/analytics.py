from datetime import datetime
from fastapi import APIRouter,Depends,Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.deps import TenantContext,require_roles
from app.models.enums import UserRole
from app.services.analytics_service import AnalyticsService
router=APIRouter(prefix="/analytics",tags=["Governance Analytics"])
@router.get("/")
def dashboard(start:datetime|None=Query(None),end:datetime|None=Query(None),db:Session=Depends(get_db),ctx:TenantContext=Depends(require_roles([UserRole.ADMIN]))):return AnalyticsService.dashboard(db,ctx,start,end)
