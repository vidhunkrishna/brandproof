import re
from typing import Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.user import User
from app.models.organization import Organization, OrganizationMember
from app.models.enums import UserRole
from app.core.security import get_password_hash, verify_password, create_access_token
from app.schemas.auth import (
    UserRegisterRequest,
    UserLoginRequest,
    TokenResponse,
    UserResponse,
    OrganizationResponse,
    MembershipResponse,
    UserProfileResponse,
)


def slugify(text: str) -> str:
    """Generates a URL-safe lowercase slug from a string."""
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_-]+', '-', text)
    return text.strip('-') or "org"


class AuthService:
    @staticmethod
    def register(db: Session, req: UserRegisterRequest) -> TokenResponse:
        # Check if email is already registered
        existing_user = db.query(User).filter(User.email == req.email.lower()).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A user with this email address already exists."
            )

        # Find or create organization
        org_slug = slugify(req.organization_name)
        org = db.query(Organization).filter(Organization.slug == org_slug).first()
        if not org:
            org = Organization(
                name=req.organization_name.strip(),
                slug=org_slug
            )
            db.add(org)
            db.flush()

        # Create new user
        hashed_pwd = get_password_hash(req.password)
        new_user = User(
            email=req.email.lower(),
            hashed_password=hashed_pwd,
            full_name=req.full_name.strip(),
            is_active=True
        )
        db.add(new_user)
        db.flush()

        # Create organization membership
        role = req.role or UserRole.CREATOR
        membership = OrganizationMember(
            organization_id=org.id,
            user_id=new_user.id,
            role=role
        )
        db.add(membership)
        db.commit()
        db.refresh(new_user)
        db.refresh(org)

        # Generate JWT token with sub, org_id, and role
        token_payload = {
            "sub": new_user.id,
            "email": new_user.email,
            "org_id": org.id,
            "role": role.value
        }
        token = create_access_token(token_payload)

        return TokenResponse(
            access_token=token,
            token_type="bearer",
            user=UserResponse.model_validate(new_user),
            active_organization=OrganizationResponse.model_validate(org),
            role=role
        )

    @staticmethod
    def login(db: Session, req: UserLoginRequest, requested_org_id: Optional[str] = None) -> TokenResponse:
        user = db.query(User).filter(User.email == req.email.lower()).first()
        if not user or not verify_password(req.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is inactive."
            )

        # Determine active organization membership
        if requested_org_id:
            membership = db.query(OrganizationMember).filter(
                OrganizationMember.user_id == user.id,
                OrganizationMember.organization_id == requested_org_id
            ).first()
            if not membership:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="User is not a member of the requested organization."
                )
        else:
            membership = db.query(OrganizationMember).filter(
                OrganizationMember.user_id == user.id
            ).first()
            if not membership:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="User does not belong to any organization."
                )

        org = db.query(Organization).filter(Organization.id == membership.organization_id).first()

        token_payload = {
            "sub": user.id,
            "email": user.email,
            "org_id": org.id,
            "role": membership.role.value
        }
        token = create_access_token(token_payload)

        return TokenResponse(
            access_token=token,
            token_type="bearer",
            user=UserResponse.model_validate(user),
            active_organization=OrganizationResponse.model_validate(org),
            role=membership.role
        )

