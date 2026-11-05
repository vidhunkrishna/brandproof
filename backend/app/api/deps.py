from typing import List, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.user import User
from app.models.organization import Organization, OrganizationMember
from app.models.enums import UserRole

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_PREFIX}/auth/login",
    auto_error=False
)


class TenantContext:
    """Encapsulates the authenticated user, validated active organization, and verified role.
    This guarantees organization isolation across all routes.
    """
    def __init__(self, user: User, organization: Organization, role: UserRole):
        self.user = user
        self.organization = organization
        self.role = role
        self.org_id = organization.id


def get_current_user(
    db: Session = Depends(get_db),
    token: Optional[str] = Depends(oauth2_scheme)
) -> User:
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token is missing.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload["sub"]
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive."
        )

    return user


def get_tenant_context(
    db: Session = Depends(get_db),
    token: Optional[str] = Depends(oauth2_scheme)
) -> TenantContext:
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token is missing.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_access_token(token)
    if not payload or "sub" not in payload or "org_id" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload["sub"]
    org_id = payload["org_id"]

    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verify membership strictly in the database (never trust token claims alone)
    membership = db.query(OrganizationMember).filter(
        OrganizationMember.user_id == user.id,
        OrganizationMember.organization_id == org_id
    ).first()

    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: user is not a member of this organization."
        )

    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found."
        )

    return TenantContext(user=user, organization=org, role=membership.role)


def require_roles(allowed_roles: List[UserRole]):
    """Enforces server-side Role-Based Access Control (RBAC)."""
    def role_checker(ctx: TenantContext = Depends(get_tenant_context)) -> TenantContext:
        if ctx.role not in allowed_roles:
            allowed_names = ", ".join([r.value for r in allowed_roles])
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Operation requires one of the following roles: [{allowed_names}]. Current role: '{ctx.role.value}'."
            )
        return ctx
    return role_checker

