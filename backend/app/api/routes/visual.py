from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.deps import TenantContext, get_tenant_context, require_roles
from app.models.enums import UserRole
from app.schemas.visual import VisualConfigRequest, VisualConfigResponse, VisualAssetResponse
from app.services.visual_service import VisualService
router = APIRouter(prefix="/visual", tags=["Visual Brand Compliance"])
@router.get("/config", response_model=VisualConfigResponse)
def get_config(db: Session=Depends(get_db), ctx: TenantContext=Depends(require_roles([UserRole.ADMIN]))): return VisualService.get_config(db,ctx)
@router.put("/config", response_model=VisualConfigResponse)
def set_config(req: VisualConfigRequest, db: Session=Depends(get_db), ctx: TenantContext=Depends(require_roles([UserRole.ADMIN]))): return VisualService.config(db,ctx,req)
@router.post("/reviews", response_model=VisualAssetResponse)
async def review(file: UploadFile=File(...), db: Session=Depends(get_db), ctx: TenantContext=Depends(require_roles([UserRole.CREATOR,UserRole.ADMIN]))): return await VisualService.review(db,ctx,file)
@router.get("/reviews", response_model=list[VisualAssetResponse])
def history(db: Session=Depends(get_db), ctx: TenantContext=Depends(get_tenant_context)): return VisualService.list(db,ctx)
