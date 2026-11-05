from sqlalchemy import Column, String, Text, Integer, Float, ForeignKey, DateTime, Enum as SQLEnum, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import generate_uuid, TimestampMixin
from app.models.enums import GuidelineStatus, FactStatus


class Guideline(Base, TimestampMixin):
    __tablename__ = "guidelines"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(100), index=True, nullable=False, default="general")
    rule_text = Column(Text, nullable=False)
    prohibited_phrases = Column(JSON, nullable=True)  # List[str] for deterministic matching
    required_phrases = Column(JSON, nullable=True)    # List[str] for deterministic matching
    source = Column(String(255), nullable=True)
    scope = Column(String(255), nullable=True)
    owner_user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    review_due_at = Column(DateTime, nullable=True)
    version = Column(Integer, default=1, nullable=False)
    status = Column(SQLEnum(GuidelineStatus), default=GuidelineStatus.ACTIVE, nullable=False)
    created_by_user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    approved_by_user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    approved_at = Column(DateTime, nullable=True)

    # Relationships
    organization = relationship("Organization", back_populates="guidelines")
    findings = relationship("Finding", back_populates="guideline")


class ApprovedFact(Base, TimestampMixin):
    __tablename__ = "approved_facts"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    fact_name = Column(String(255), nullable=False)
    approved_value = Column(String(255), nullable=False)
    numeric_value = Column(Float, nullable=True)
    numeric_operator = Column(String(10), nullable=True)  # e.g., "<=", "==", ">="
    unit = Column(String(50), nullable=True)              # e.g., "%", "years"
    description = Column(Text, nullable=True)
    category = Column(String(100), index=True, nullable=False, default="general")
    source = Column(String(255), nullable=True)
    scope = Column(String(255), default="global", nullable=False)
    required_qualifiers = Column(JSON, nullable=True)     # List[str] e.g. ["in laboratory tests"]
    valid_from = Column(DateTime, nullable=True)
    valid_until = Column(DateTime, nullable=True)         # Checked for OUTDATED verdict
    version = Column(Integer, default=1, nullable=False)
    superseded_by_id = Column(String(36), ForeignKey("approved_facts.id", ondelete="SET NULL"), nullable=True)
    status = Column(SQLEnum(FactStatus), default=FactStatus.APPROVED, nullable=False)
    approved_by_user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    review_status = Column(String(30), nullable=False, default="pending")
    reviewed_by_user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)

    # Relationships
    organization = relationship("Organization", back_populates="approved_facts")
    findings = relationship("Finding", back_populates="fact")
    superseded_by = relationship("ApprovedFact", remote_side=[id])

