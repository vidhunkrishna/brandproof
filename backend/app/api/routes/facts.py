from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.deps import get_tenant_context, TenantContext
from app.models.enums import FactStatus
from app.schemas.knowledge import (
    FactCreateRequest,
    FactUpdateRequest,
    FactSupersedeRequest,
    FactResponse,
)
from app.services.fact_service import FactService

router = APIRouter(prefix="/facts", tags=["Approved Facts"])


@router.post("/", response_model=FactResponse, status_code=status.HTTP_201_CREATED)
def create_fact(
    req: FactCreateRequest,
    db: Session = Depends(get_db),
    ctx: TenantContext = Depends(get_tenant_context)
):
    """Create a new fact (approved if Admin, pending approval if Creator)."""
    return FactService.create(db, ctx, req)


@router.get("/", response_model=List[FactResponse])
def list_facts(
    category: Optional[str] = Query(None, description="Filter by category"),
    status: Optional[FactStatus] = Query(None, description="Filter by status"),
    scope: Optional[str] = Query(None, description="Filter by scope"),
    search: Optional[str] = Query(None, description="Search fact name or value"),
    db: Session = Depends(get_db),
    ctx: TenantContext = Depends(get_tenant_context)
):
    """List approved brand facts scoped to the authenticated organization."""
    return FactService.list(db, ctx, category, status, scope, search)


@router.get("/{fact_id}", response_model=FactResponse)
def get_fact(
    fact_id: str,
    db: Session = Depends(get_db),
    ctx: TenantContext = Depends(get_tenant_context)
):
    """Retrieve an individual approved fact by ID."""
    return FactService.get(db, ctx, fact_id)


@router.put("/{fact_id}", response_model=FactResponse)
def update_fact(
    fact_id: str,
    req: FactUpdateRequest,
    db: Session = Depends(get_db),
    ctx: TenantContext = Depends(get_tenant_context)
):
    """Directly update an existing approved fact. (Admin only)"""
    return FactService.update(db, ctx, fact_id, req)


@router.post("/{fact_id}/supersede", response_model=FactResponse, status_code=status.HTTP_201_CREATED)
def supersede_fact(
    fact_id: str,
    req: FactSupersedeRequest,
    db: Session = Depends(get_db),
    ctx: TenantContext = Depends(get_tenant_context)
):
    """Supersede an approved fact with a new version, preserving full historical audit trail. (Admin only)"""
    return FactService.supersede(db, ctx, fact_id, req)


@router.put("/{fact_id}/approve", response_model=FactResponse)
def approve_fact(
    fact_id: str,
    db: Session = Depends(get_db),
    ctx: TenantContext = Depends(get_tenant_context)
):
    """Approve a pending fact. (Admin only)"""
    return FactService.approve(db, ctx, fact_id)


@router.delete("/{fact_id}", response_model=FactResponse)
def archive_fact(
    fact_id: str,
    db: Session = Depends(get_db),
    ctx: TenantContext = Depends(get_tenant_context)
):
    """Archive an approved fact. (Admin only)"""
    return FactService.archive(db, ctx, fact_id)

