from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.deps import get_tenant_context, TenantContext
from app.models.enums import GuidelineStatus
from app.schemas.knowledge import (
    GuidelineCreateRequest,
    GuidelineUpdateRequest,
    GuidelineResponse,
)
from app.services.guideline_service import GuidelineService

router = APIRouter(prefix="/guidelines", tags=["Brand Guidelines"])


@router.post("/", response_model=GuidelineResponse, status_code=status.HTTP_201_CREATED)
def create_guideline(
    req: GuidelineCreateRequest,
    db: Session = Depends(get_db),
    ctx: TenantContext = Depends(get_tenant_context)
):
    """Create a new brand guideline (active if Admin, draft if Creator)."""
    return GuidelineService.create(db, ctx, req)


@router.get("/", response_model=List[GuidelineResponse])
def list_guidelines(
    category: Optional[str] = Query(None, description="Filter by category"),
    status: Optional[GuidelineStatus] = Query(None, description="Filter by status (draft, active, archived)"),
    search: Optional[str] = Query(None, description="Keyword search in title and rule text"),
    db: Session = Depends(get_db),
    ctx: TenantContext = Depends(get_tenant_context)
):
    """List brand guidelines scoped to the authenticated organization."""
    return GuidelineService.list(db, ctx, category, status, search)


@router.get("/{guideline_id}", response_model=GuidelineResponse)
def get_guideline(
    guideline_id: str,
    db: Session = Depends(get_db),
    ctx: TenantContext = Depends(get_tenant_context)
):
    """Retrieve an individual brand guideline by ID."""
    return GuidelineService.get(db, ctx, guideline_id)


@router.put("/{guideline_id}", response_model=GuidelineResponse)
def update_guideline(
    guideline_id: str,
    req: GuidelineUpdateRequest,
    db: Session = Depends(get_db),
    ctx: TenantContext = Depends(get_tenant_context)
):
    """Update a brand guideline. Bumps version number if rule content changes."""
    return GuidelineService.update(db, ctx, guideline_id, req)


@router.put("/{guideline_id}/approve", response_model=GuidelineResponse)
def approve_guideline(
    guideline_id: str,
    db: Session = Depends(get_db),
    ctx: TenantContext = Depends(get_tenant_context)
):
    """Approve a draft/candidate guideline to make it active. (Admin only)"""
    return GuidelineService.approve(db, ctx, guideline_id)


@router.delete("/{guideline_id}", response_model=GuidelineResponse)
def archive_guideline(
    guideline_id: str,
    db: Session = Depends(get_db),
    ctx: TenantContext = Depends(get_tenant_context)
):
    """Archive a brand guideline. (Admin only)"""
    return GuidelineService.archive(db, ctx, guideline_id)

