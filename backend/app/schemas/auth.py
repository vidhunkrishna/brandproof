from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from datetime import datetime
from app.models.enums import UserRole


class UserRegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, description="Password must be at least 8 characters long")
    full_name: str = Field(..., min_length=1, max_length=255)
    organization_name: str = Field(..., min_length=2, max_length=255, description="Organization name to join or create")
    role: Optional[UserRole] = Field(default=UserRole.CREATOR, description="Initial role within organization")


class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str


class OrganizationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    slug: str
    created_at: datetime


class MembershipResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    organization_id: str
    organization_name: str
    organization_slug: str
    role: UserRole


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    email: str
    full_name: str
    is_active: bool
    created_at: datetime


class UserProfileResponse(BaseModel):
    user: UserResponse
    active_organization: OrganizationResponse
    role: UserRole
    memberships: List[MembershipResponse]


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
    active_organization: OrganizationResponse
    role: UserRole
