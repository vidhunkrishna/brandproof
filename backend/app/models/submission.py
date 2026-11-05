from typing import Optional
from sqlalchemy import Boolean, Column, String, Text, Integer, Float, ForeignKey, DateTime, Enum as SQLEnum, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base
from app.models.base import generate_uuid, TimestampMixin
from app.models.enums import (
    ContentType,
    SubmissionStatus,
    FindingVerdict,
    RevisionVerdict,
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

    @property
    def latest_revision(self) -> Optional["SubmissionRevision"]:
        return self.revisions[-1] if self.revisions else None

    @property
    def total_revisions(self) -> int:
        return len(self.revisions) if self.revisions else 0


class SubmissionRevision(Base):
    __tablename__ = "submission_revisions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    submission_id = Column(String(36), ForeignKey("submissions.id", ondelete="CASCADE"), nullable=False, index=True)
    revision_number = Column(Integer, default=1, nullable=False)
    content_text = Column(Text, nullable=False)
    change_summary = Column(Text, nullable=True)
    overall_verdict = Column(SQLEnum(RevisionVerdict, name="revisionverdict"), default=RevisionVerdict.NEEDS_REVIEW, nullable=False)
    # Nullable preserves revisions created before review mode was retained.
    review_used_fallback = Column(Boolean, nullable=True)
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
    # Zero-based, half-open UTF-16 code-unit offsets [start_offset, end_offset)
    # Binary-compatible with JavaScript `contentText.substring(start_offset, end_offset)`
    start_offset = Column(Integer, nullable=True)
    end_offset = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    revision = relationship("SubmissionRevision", back_populates="findings")
    fact = relationship("ApprovedFact", back_populates="findings")
    guideline = relationship("Guideline", back_populates="findings")
    disputes = relationship("Dispute", back_populates="finding", cascade="all, delete-orphan")

    @property
    def fact_name(self) -> Optional[str]:
        return self.fact.fact_name if self.fact else None

    @property
    def fact_version(self) -> Optional[int]:
        return self.fact.version if self.fact else None

    @property
    def fact_approved_value(self) -> Optional[str]:
        return self.fact.approved_value if self.fact else None

    @property
    def fact_source(self) -> Optional[str]:
        return self.fact.source if self.fact else None

    @property
    def guideline_title(self) -> Optional[str]:
        return self.guideline.title if self.guideline else None

    @property
    def guideline_version(self) -> Optional[int]:
        return self.guideline.version if self.guideline else None

    @property
    def guideline_source(self) -> Optional[str]:
        return self.guideline.source if self.guideline else None


class Dispute(Base, TimestampMixin):
    __tablename__ = "disputes"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    finding_id = Column(String(36), ForeignKey("findings.id", ondelete="CASCADE"), nullable=False, index=True)
    raised_by_user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    reason = Column(Text, nullable=False)
    status = Column(SQLEnum(DisputeStatus), default=DisputeStatus.OPEN, nullable=False, index=True)
    resolution_note = Column(Text, nullable=True)
    # An override is layered over the immutable original Finding; the finding itself is never edited.
    override_verdict = Column(SQLEnum(FindingVerdict), nullable=True)
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

