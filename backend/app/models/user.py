from sqlalchemy import Boolean, Column, DateTime, String
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base
from app.models.base import generate_uuid, TimestampMixin


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    # Relationships
    memberships = relationship("OrganizationMember", back_populates="user", cascade="all, delete-orphan")
    submissions = relationship("Submission", back_populates="creator", foreign_keys="Submission.creator_user_id")
    disputes_raised = relationship("Dispute", back_populates="raised_by", foreign_keys="Dispute.raised_by_user_id")

