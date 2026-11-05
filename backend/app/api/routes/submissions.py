"""
Marketing Submissions and Review API Routes for BrandProof.

Endpoints:
- POST /api/v1/submissions/ : Create submission and execute initial 3-lane review
- GET /api/v1/submissions/ : List submissions with pagination (creator isolated to own submissions)
- GET /api/v1/submissions/{submission_id} : Retrieve submission, revision history, and findings
- POST /api/v1/submissions/{submission_id}/recheck : Recheck revised content and create new revision
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.deps import get_tenant_context, require_roles, TenantContext
from app.models.enums import UserRole, ContentType, SubmissionStatus
from app.schemas.submission import (
    SubmissionCreateRequest,
    SubmissionRevisionCreateRequest,
    SubmissionResponse,
)
from app.services.submission_service import SubmissionService

router = APIRouter(prefix="/submissions", tags=["Marketing Submissions"])


@router.post("/", response_model=SubmissionResponse, status_code=status.HTTP_201_CREATED)
def create_submission(
    req: SubmissionCreateRequest,
    db: Session = Depends(get_db),
    ctx: TenantContext = Depends(require_roles([UserRole.CREATOR, UserRole.ADMIN])),
):
    """
    Create a new marketing submission and run the three-lane governance review.
    Accessible to creators and admins.
    """
    return SubmissionService.create_submission(db=db, ctx=ctx, req=req)


@router.get("/", response_model=List[SubmissionResponse])
def list_submissions(
    skip: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(50, ge=1, le=100, description="Items per page"),
    content_type: Optional[ContentType] = Query(None, description="Filter by content type"),
    status: Optional[SubmissionStatus] = Query(None, description="Filter by submission status"),
    db: Session = Depends(get_db),
    ctx: TenantContext = Depends(get_tenant_context),
):
    """
    List submissions scoped to the active organization.
    Creators only see their own submissions; Reviewers and Admins see all organization submissions.
    """
    return SubmissionService.list_submissions(
        db=db,
        ctx=ctx,
        skip=skip,
        limit=limit,
        content_type=content_type,
        status_filter=status,
    )
@router.get("/{submission_id}", response_model=SubmissionResponse)
def get_submission(
    submission_id: str,
    db: Session = Depends(get_db),
    ctx: TenantContext = Depends(get_tenant_context),
):
    """
    Retrieve full submission details, revision history, and evidence findings.
    Enforces tenant isolation and creator ownership restrictions.
    """
    return SubmissionService.get_submission(db=db, ctx=ctx, submission_id=submission_id)


@router.post("/{submission_id}/recheck", response_model=SubmissionResponse)
def recheck_submission(
    submission_id: str,
    req: SubmissionRevisionCreateRequest,
    db: Session = Depends(get_db),
    ctx: TenantContext = Depends(require_roles([UserRole.CREATOR, UserRole.ADMIN])),
):
    """
    Submit revised marketing copy for an existing submission.
    Creates a new immutable revision, re-executes the three-lane review,
    and preserves all previous revisions and findings.
    """
    return SubmissionService.recheck_submission(
        db=db,
        ctx=ctx,
        submission_id=submission_id,
        req=req,
    )
