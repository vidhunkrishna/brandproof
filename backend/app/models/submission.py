from sqlalchemy import Column, String, Text, Integer, Float, ForeignKey, DateTime, Enum as SQLEnum, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base
from app.models.base import generate_uuid, TimestampMixin
from app.models.enums import (
    ContentType,
    SubmissionStatus,
    FindingVerdict,
    ReviewLane,
    DisputeStatus
)


class Submission(Base, TimestampMixin):
    __tablename__ = "submissions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    creator_user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    content_type = Column(SQLEnum(ContentType), default=ContentType.GENERAL, nullable=False)
    current_status = Column(SQLEnum(SubmissionStatus), default=SubmissionStatus.DRAFT, nullable=False, index=True)

    # Relationships
    organization = relationship("Organization", back_populates="submissions")
    creator = relationship("User", back_populates="submissions", foreign_keys=[creator_user_id])
    revisions = relationship("SubmissionRevision", back_populates="submission", cascade="all, delete-orphan", order_by="SubmissionRevision.revision_number")
    review_logs = relationship("ReviewLog", back_populates="submission", cascade="all, delete-orphan")


class SubmissionRevision(Base):
    __tablename__ = "submission_revisions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    submission_id = Column(String(36), ForeignKey("submissions.id", ondelete="CASCADE"), nullable=False, index=True)
    revision_number = Column(Integer, default=1, nullable=False)
    content_text = Column(Text, nullable=False)
    change_summary = Column(Text, nullable=True)
    overall_verdict = Column(String(50), default="PENDING", nullable=False)  # CORRECT, CONTRADICTED, MIXED, etc.
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    submission = relationship("Submission", back_populates="revisions")
    findings = relationship("Finding", back_populates="revision", cascade="all, delete-orphan")


class Finding(Base):
    __tablename__ = "findings"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    submission_revision_id = Column(String(36), ForeignKey("submission_revisions.id", ondelete="CASCADE"), nullable=False, index=True)
    claim_text = Column(Text, nullable=False)
    verdict = Column(SQLEnum(FindingVerdict), nullable=False, index=True)
    lane = Column(SQLEnum(ReviewLane), nullable=False)
    explanation = Column(Text, nullable=False)
    suggested_correction = Column(Text, nullable=True)
    fact_id = Column(String(36), ForeignKey("approved_facts.id", ondelete="SET NULL"), nullable=True, index=True)
    guideline_id = Column(String(36), ForeignKey("guidelines.id", ondelete="SET NULL"), nullable=True, index=True)
    confidence_score = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    revision = relationship("SubmissionRevision", back_populates="findings")
    fact = relationship("ApprovedFact", back_populates="findings")
    guideline = relationship("Guideline", back_populates="findings")
    disputes = relationship("Dispute", back_populates="finding", cascade="all, delete-orphan")


class Dispute(Base, TimestampMixin):
    __tablename__ = "disputes"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    finding_id = Column(String(36), ForeignKey("findings.id", ondelete="CASCADE"), nullable=False, index=True)
    raised_by_user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    reason = Column(Text, nullable=False)
    status = Column(SQLEnum(DisputeStatus), default=DisputeStatus.OPEN, nullable=False, index=True)
    resolution_note = Column(Text, nullable=True)
    resolved_by_user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # Relationships
    organization = relationship("Organization", back_populates="disputes")
    finding = relationship("Finding", back_populates="disputes")
    raised_by = relationship("User", back_populates="disputes_raised", foreign_keys=[raised_by_user_id])
    resolved_by = relationship("User", foreign_keys=[resolved_by_user_id])


class ReviewLog(Base):
    __tablename__ = "review_logs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    submission_id = Column(String(36), ForeignKey("submissions.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    action = Column(String(100), nullable=False)  # e.g., "submit", "request_changes", "approve", "dispute"
    comment = Column(Text, nullable=True)
    metadata_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    organization = relationship("Organization", back_populates="review_logs")
    submission = relationship("Submission", back_populates="review_logs")
    user = relationship("User")

