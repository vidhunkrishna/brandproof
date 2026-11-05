from enum import Enum


class UserRole(str, Enum):
    ADMIN = "admin"
    CREATOR = "creator"
    REVIEWER = "reviewer"


class GuidelineStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"


class FactStatus(str, Enum):
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    SUPERSEDED = "superseded"
    ARCHIVED = "archived"


class ContentType(str, Enum):
    WEBSITE_COPY = "website_copy"
    EMAIL = "email"
    SOCIAL_MEDIA = "social_media"
    GENERAL = "general"


class SubmissionStatus(str, Enum):
    DRAFT = "draft"
    REVIEW_PENDING = "review_pending"
    CHANGES_REQUESTED = "changes_requested"
    APPROVED = "approved"
    DISPUTED = "disputed"


class FindingVerdict(str, Enum):
    CORRECT = "CORRECT"
    CONTRADICTED = "CONTRADICTED"
    OUTDATED = "OUTDATED"
    UNSUPPORTED = "UNSUPPORTED"
    UNVERIFIABLE = "UNVERIFIABLE"


class RevisionVerdict(str, Enum):
    CORRECT = "CORRECT"
    CONTRADICTED = "CONTRADICTED"
    OUTDATED = "OUTDATED"
    UNSUPPORTED = "UNSUPPORTED"
    UNVERIFIABLE = "UNVERIFIABLE"
    MIXED = "MIXED"
    NEEDS_REVIEW = "NEEDS_REVIEW"


class ReviewLane(str, Enum):
    LANE_1_DETERMINISTIC = "LANE_1_DETERMINISTIC"
    LANE_2_GROUNDED_FACT = "LANE_2_GROUNDED_FACT"
    LANE_3_ADVISORY_AI = "LANE_3_ADVISORY_AI"


class DisputeStatus(str, Enum):
    OPEN = "open"
    UPHELD = "upheld"
    REJECTED = "rejected"
    RESOLVED = "resolved"

