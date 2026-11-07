from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.enums import UserRole
from app.models.organization import OrganizationMember
from app.schemas.auth import (
    UserRegisterRequest,
    UserLoginRequest,
    TokenResponse,
    UserResponse,
    OrganizationResponse,
    MembershipResponse,
    UserProfileResponse,
)
from app.services.auth_service import AuthService
from app.api.deps import get_tenant_context, require_roles, TenantContext

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(request: UserRegisterRequest, db: Session = Depends(get_db)):
    """Register a new user and create/join an organization."""
    return AuthService.register(db, request)


@router.post("/login", response_model=TokenResponse)
def login(request: UserLoginRequest, db: Session = Depends(get_db)):
    """Authenticate a user and return an access token."""
    return AuthService.login(db, request)


@router.get("/me", response_model=UserProfileResponse)
def get_current_user_profile(
    ctx: TenantContext = Depends(get_tenant_context),
    db: Session = Depends(get_db)
):
    """Retrieve profile and role information for the currently authenticated user in their active organization."""
    memberships_db = db.query(OrganizationMember).filter(
        OrganizationMember.user_id == ctx.user.id
    ).all()

    memberships_list = [
        MembershipResponse(
            organization_id=m.organization_id,
            organization_name=m.organization.name,
            organization_slug=m.organization.slug,
            role=m.role
        )
        for m in memberships_db
    ]

    return UserProfileResponse(
        user=UserResponse.model_validate(ctx.user),
        active_organization=OrganizationResponse.model_validate(ctx.organization),
        role=ctx.role,
        memberships=memberships_list
    )


@router.get("/admin-only-check", response_model=dict)
def admin_only_check(ctx: TenantContext = Depends(require_roles([UserRole.ADMIN]))):
    """Diagnostic endpoint to verify admin role enforcement."""
    return {
        "status": "authorized",
        "message": f"Welcome Admin {ctx.user.full_name} to {ctx.organization.name}."
    }


@router.post("/seed-demo", response_model=dict)
def seed_demo_endpoint(db: Session = Depends(get_db)):
    """Initialize or refresh demonstration data for the synthetic Lumen brand.
    Safe and idempotent: populates demo users, guidelines, approved facts, submissions, and dispute queue.
    """
    from app.seed import seed_database
    seed_database(db)
    return {
        "status": "success",
        "message": "Demo data initialized successfully with Lumen organization, demo users, guidelines, facts, submissions, and dispute queue."
    }

