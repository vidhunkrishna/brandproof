from sqlalchemy import Column, String, ForeignKey, Enum as SQLEnum, UniqueConstraint
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import generate_uuid, TimestampMixin
from app.models.enums import UserRole


class Organization(Base, TimestampMixin):
    __tablename__ = "organizations"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False)
    slug = Column(String(100), unique=True, index=True, nullable=False)

    # Relationships
    members = relationship("OrganizationMember", back_populates="organization", cascade="all, delete-orphan")
    guidelines = relationship("Guideline", back_populates="organization", cascade="all, delete-orphan")
    approved_facts = relationship("ApprovedFact", back_populates="organization", cascade="all, delete-orphan")
    submissions = relationship("Submission", back_populates="organization", cascade="all, delete-orphan")
    disputes = relationship("Dispute", back_populates="organization", cascade="all, delete-orphan")
    review_logs = relationship("ReviewLog", back_populates="organization", cascade="all, delete-orphan")


class OrganizationMember(Base, TimestampMixin):
    __tablename__ = "organization_members"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(SQLEnum(UserRole), nullable=False, default=UserRole.CREATOR)

    # Relationships
    organization = relationship("Organization", back_populates="members")
    user = relationship("User", back_populates="memberships")

    __table_args__ = (
        UniqueConstraint("organization_id", "user_id", name="uq_org_user"),
    )

