"""
Submission lifecycle and governance review service for BrandProof.

Responsibilities:
- Create new marketing submissions with initial revision and atomic review execution.
- Recheck revised marketing copy by generating immutable subsequent revisions.
- Persist findings with verified evidence IDs, guideline versions, and UTF-16 offsets.
- Preserve full historical revisions and findings without destructive overwrites.
- Enforce organization isolation and role-based access control (creators only access own drafts;
  reviewers and admins access all organization submissions).
- Wrap multi-table operations in database transactions to avoid partial writes.
"""
import logging
from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.api.deps import TenantContext
from app.models.enums import UserRole, SubmissionStatus, ContentType
from app.models.submission import Submission, SubmissionRevision, Finding
from app.schemas.submission import (
    SubmissionCreateRequest,
    SubmissionRevisionCreateRequest,
    SubmissionResponse,
    ReviewResultResponse,
    FindingResponse,
)
from app.review_engine.orchestrator import ReviewOrchestrator, ReviewResult
from app.review_engine.ai_provider import BaseAIProvider

logger = logging.getLogger("brandproof.submission_service")


class SubmissionService:
    @staticmethod
    def _build_review_result_response(
        submission_id: str,
        revision_id: str,
        revision_number: int,
        content_text: str,
        review_result: ReviewResult,
        persisted_findings: List[Finding],
    ) -> ReviewResultResponse:
        """Construct structured ReviewResultResponse from orchestrator result and persisted findings."""
        finding_responses = [FindingResponse.model_validate(f) for f in persisted_findings]
        return ReviewResultResponse(
            submission_id=submission_id,
            revision_id=revision_id,
            revision_number=revision_number,
            overall_verdict=review_result.overall_verdict,
            content_text=content_text,
            is_fallback=review_result.is_fallback,
            total_findings=review_result.total_findings,
            correct_claims=review_result.correct_claims,
            contradicted_claims=review_result.contradicted_claims,
            outdated_claims=review_result.outdated_claims,
            unsupported_claims=review_result.unsupported_claims,
            unverifiable_claims=review_result.unverifiable_claims,
            findings=finding_responses,
        )

    @classmethod
    def create_submission(
        cls,
        db: Session,
        ctx: TenantContext,
        req: SubmissionCreateRequest,
        ai_provider: Optional[BaseAIProvider] = None,
    ) -> SubmissionResponse:
        """
        Create a marketing submission, generate its initial revision, execute the
        three-lane review orchestrator, and persist findings inside an atomic transaction.
        """
        # 1. Run three-lane review orchestrator
        orchestrator = ReviewOrchestrator(ai_provider=ai_provider)
        review_result = orchestrator.run_review(
            db=db,
            organization_id=ctx.org_id,
            content_text=req.content_text,
        )

        # 2. Determine initial submission status from overall verdict
        if review_result.overall_verdict == "CORRECT":
            sub_status = SubmissionStatus.APPROVED
        elif review_result.overall_verdict in ("CONTRADICTED", "OUTDATED"):
            sub_status = SubmissionStatus.CHANGES_REQUESTED
        else:
            sub_status = SubmissionStatus.REVIEW_PENDING

        try:
            # 3. Create Submission record
            submission = Submission(
                organization_id=ctx.org_id,
                creator_user_id=ctx.user.id,
                title=req.title,
                content_type=req.content_type,
                current_status=sub_status,
            )
            db.add(submission)
            db.flush()

            # 4. Create Initial Revision (Revision 1)
            revision = SubmissionRevision(
                submission_id=submission.id,
                revision_number=1,
                content_text=req.content_text,
                change_summary="Initial submission",
                overall_verdict=review_result.overall_verdict,
                review_used_fallback=review_result.is_fallback,
            )
            db.add(revision)
            db.flush()

            # 5. Persist Findings
            persisted_findings: List[Finding] = []
            for ef in review_result.findings:
                finding = Finding(
                    submission_revision_id=revision.id,
                    claim_text=ef.claim_text,
                    verdict=ef.verdict,
                    lane=ef.lane,
                    explanation=ef.explanation,
                    suggested_correction=ef.suggested_correction,
                    fact_id=ef.fact_id,
                    guideline_id=ef.guideline_id,
                    confidence_score=ef.confidence_score,
                    start_offset=ef.start_offset,
                    end_offset=ef.end_offset,
                )
                db.add(finding)
                persisted_findings.append(finding)

            db.commit()
            db.refresh(submission)
            for f in persisted_findings:
                db.refresh(f)

        except Exception as e:
            db.rollback()
            logger.error("Failed to persist submission: %s", str(e), exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to persist submission and review results: {str(e)}",
            )

        resp = SubmissionResponse.model_validate(submission)
        resp.review_result = cls._build_review_result_response(
            submission_id=submission.id,
            revision_id=revision.id,
            revision_number=revision.revision_number,
            content_text=revision.content_text,
            review_result=review_result,
            persisted_findings=persisted_findings,
        )
        return resp

    @classmethod
    def recheck_submission(
        cls,
        db: Session,
        ctx: TenantContext,
        submission_id: str,
        req: SubmissionRevisionCreateRequest,
        ai_provider: Optional[BaseAIProvider] = None,
    ) -> SubmissionResponse:
        """
        Recheck revised copy for an existing submission.
        Creates an immutable subsequent revision, executes review, and preserves historical data.
        """
        # Fetch submission scoped to organization
        submission = (
            db.query(Submission)
            .filter(
                Submission.id == submission_id,
                Submission.organization_id == ctx.org_id,
            )
            .first()
        )
        if not submission:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Submission '{submission_id}' not found in active organization.",
            )

        # RBAC Check: Creators can only recheck their own submissions
        if ctx.role == UserRole.CREATOR and submission.creator_user_id != ctx.user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: creators can only recheck their own submissions.",
            )

        # Determine next revision number
        highest_rev_num = max([r.revision_number for r in submission.revisions], default=0)
        next_rev_num = highest_rev_num + 1

        # Run review engine
        orchestrator = ReviewOrchestrator(ai_provider=ai_provider)
        review_result = orchestrator.run_review(
            db=db,
            organization_id=ctx.org_id,
            content_text=req.content_text,
        )

        # Map overall verdict to updated submission status
        if review_result.overall_verdict == "CORRECT":
            sub_status = SubmissionStatus.APPROVED
        elif review_result.overall_verdict in ("CONTRADICTED", "OUTDATED"):
            sub_status = SubmissionStatus.CHANGES_REQUESTED
        else:
            sub_status = SubmissionStatus.REVIEW_PENDING

        try:
            submission.current_status = sub_status

            # Create new revision (historical revisions remain unchanged)
            new_revision = SubmissionRevision(
                submission_id=submission.id,
                revision_number=next_rev_num,
                content_text=req.content_text,
                change_summary=req.change_summary or f"Revision {next_rev_num}",
                overall_verdict=review_result.overall_verdict,
                review_used_fallback=review_result.is_fallback,
            )
            db.add(new_revision)
            db.flush()

            persisted_findings: List[Finding] = []
            for ef in review_result.findings:
                finding = Finding(
                    submission_revision_id=new_revision.id,
                    claim_text=ef.claim_text,
                    verdict=ef.verdict,
                    lane=ef.lane,
                    explanation=ef.explanation,
                    suggested_correction=ef.suggested_correction,
                    fact_id=ef.fact_id,
                    guideline_id=ef.guideline_id,
                    confidence_score=ef.confidence_score,
                    start_offset=ef.start_offset,
                    end_offset=ef.end_offset,
                )
                db.add(finding)
                persisted_findings.append(finding)

            db.commit()
            db.refresh(submission)
            for f in persisted_findings:
                db.refresh(f)

        except Exception as e:
            db.rollback()
            logger.error("Failed to persist revision recheck: %s", str(e), exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to persist revision and recheck results: {str(e)}",
            )

        resp = SubmissionResponse.model_validate(submission)
        resp.review_result = cls._build_review_result_response(
            submission_id=submission.id,
            revision_id=new_revision.id,
            revision_number=new_revision.revision_number,
            content_text=new_revision.content_text,
            review_result=review_result,
            persisted_findings=persisted_findings,
        )
        return resp

    @classmethod
    def get_submission(
        cls,
        db: Session,
        ctx: TenantContext,
        submission_id: str,
    ) -> SubmissionResponse:
        """
        Retrieve submission details with full revision history and findings.
        Enforces organization isolation and creator ownership restrictions.
        """
        submission = (
            db.query(Submission)
            .filter(
                Submission.id == submission_id,
                Submission.organization_id == ctx.org_id,
            )
            .first()
        )
        if not submission:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Submission '{submission_id}' not found in active organization.",
            )

        # Creators can only view their own submissions; Reviewers/Admins can view any in org
        if ctx.role == UserRole.CREATOR and submission.creator_user_id != ctx.user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: creators can only view their own submissions.",
            )

        return SubmissionResponse.model_validate(submission)

    @classmethod
    def list_submissions(
        cls,
        db: Session,
        ctx: TenantContext,
        skip: int = 0,
        limit: int = 50,
        content_type: Optional[ContentType] = None,
        status_filter: Optional[SubmissionStatus] = None,
    ) -> List[SubmissionResponse]:
        """
        List submissions belonging to the authenticated organization with pagination.
        Creators only see their own submissions; Reviewers and Admins see all org submissions.
        """
        query = db.query(Submission).filter(Submission.organization_id == ctx.org_id)

        # Creators only see their own submissions
        if ctx.role == UserRole.CREATOR:
            query = query.filter(Submission.creator_user_id == ctx.user.id)

        if content_type:
            query = query.filter(Submission.content_type == content_type)

        if status_filter:
            query = query.filter(Submission.current_status == status_filter)

        submissions = (
            query.order_by(Submission.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
        return [SubmissionResponse.model_validate(s) for s in submissions]
