from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict, model_validator, field_validator
from app.models.enums import ContentType, SubmissionStatus, FindingVerdict, ReviewLane, DisputeStatus


class SubmissionCreateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=255, description="Headline or title of the marketing draft")
    content_type: ContentType = Field(default=ContentType.GENERAL, description="Channel / medium of marketing copy")
    content_text: str = Field(..., min_length=1, max_length=100000, description="Full marketing copy text to review")

    @field_validator("title", "content_text")
    @classmethod
    def validate_non_empty_whitespace(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("Field cannot be empty or consist solely of whitespace.")
        return stripped


class SubmissionRevisionCreateRequest(BaseModel):
    content_text: str = Field(..., min_length=1, max_length=100000, description="Revised marketing copy text")
    change_summary: Optional[str] = Field(None, max_length=500, description="Brief description of edits made")

    @field_validator("content_text")
    @classmethod
    def validate_non_empty_whitespace(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("Revised content cannot be empty or consist solely of whitespace.")
        return stripped


class FindingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    submission_revision_id: str
    claim_text: str
    verdict: FindingVerdict
    lane: ReviewLane
    explanation: str
    suggested_correction: Optional[str] = None
    fact_id: Optional[str] = None
    fact_name: Optional[str] = None
    fact_version: Optional[int] = None
    fact_approved_value: Optional[str] = None
    fact_source: Optional[str] = None
    guideline_id: Optional[str] = None
    guideline_title: Optional[str] = None
    guideline_version: Optional[int] = None
    guideline_source: Optional[str] = None
    confidence_score: Optional[float] = None
    start_offset: Optional[int] = Field(
        None,
        description="Zero-based start offset (half-open UTF-16 code units) matching JavaScript String.prototype.substring()."
    )
    end_offset: Optional[int] = Field(
        None,
        description="Zero-based end offset (half-open UTF-16 code units) matching JavaScript String.prototype.substring()."
    )
    created_at: datetime

    @model_validator(mode="after")
    def validate_offsets(self) -> "FindingResponse":
        if self.start_offset is not None and self.start_offset < 0:
            raise ValueError("start_offset must be non-negative (>= 0).")
        if self.end_offset is not None and self.end_offset < 0:
            raise ValueError("end_offset must be non-negative (>= 0).")
        if (self.start_offset is None) != (self.end_offset is None):
            raise ValueError("Both start_offset and end_offset must be provided together, or both must be None.")
        if self.start_offset is not None and self.end_offset is not None:
            if self.start_offset >= self.end_offset:
                raise ValueError(
                    f"start_offset ({self.start_offset}) must be strictly less than end_offset ({self.end_offset}) for a non-empty interval."
                )
        return self


class SubmissionRevisionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    submission_id: str
    revision_number: int
    content_text: str
    change_summary: Optional[str] = None
    overall_verdict: str
    review_used_fallback: Optional[bool] = None
    findings: List[FindingResponse] = Field(default_factory=list)
    created_at: datetime


class SubmissionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    organization_id: str
    creator_user_id: str
    title: str
    content_type: ContentType
    current_status: SubmissionStatus
    latest_revision: Optional[SubmissionRevisionResponse] = None
    revisions: List[SubmissionRevisionResponse] = Field(default_factory=list)
    review_result: Optional["ReviewResultResponse"] = None
    total_revisions: Optional[int] = 1
    created_at: datetime
    updated_at: datetime


class ReviewResultResponse(BaseModel):
    submission_id: str
    revision_id: str
    revision_number: int
    overall_verdict: str
    content_text: str
    is_fallback: bool = False
    total_findings: int
    correct_claims: int = 0
    contradicted_claims: int = 0
    outdated_claims: int = 0
    unsupported_claims: int = 0
    unverifiable_claims: int = 0
    findings: List[FindingResponse] = Field(default_factory=list)


class DisputeCreateRequest(BaseModel):
    finding_id: str = Field(..., min_length=1)
    reason: str = Field(..., min_length=10, max_length=4000)

    @field_validator("reason")
    @classmethod
    def validate_reason(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("A dispute reason is required.")
        return value


class DisputeResolutionRequest(BaseModel):
    action: str = Field(..., pattern="^(uphold|override|request_info)$")
    reason: str = Field(..., min_length=10, max_length=4000)
    override_verdict: Optional[FindingVerdict] = None

    @model_validator(mode="after")
    def validate_override(self) -> "DisputeResolutionRequest":
        if self.action == "override" and self.override_verdict is None:
            raise ValueError("override_verdict is required when overriding a finding.")
        if self.action != "override" and self.override_verdict is not None:
            raise ValueError("override_verdict is only valid for an override action.")
        return self


class DisputeResponse(BaseModel):
    id: str
    organization_id: str
    finding_id: str
    submission_id: str
    revision_id: str
    revision_number: int
    raised_by_user_id: str
    raised_by_name: Optional[str] = None
    reason: str
    status: DisputeStatus
    resolution_note: Optional[str] = None
    override_verdict: Optional[FindingVerdict] = None
    resolved_by_user_id: Optional[str] = None
    resolved_by_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    finding: FindingResponse
