"""Tenant-scoped human review workflow for immutable review findings."""
from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException, status
from app.api.deps import TenantContext
from app.models.enums import DisputeStatus, UserRole
from app.models.submission import Dispute, Finding, ReviewLog, Submission, SubmissionRevision
from app.schemas.submission import DisputeCreateRequest, DisputeResolutionRequest, DisputeResponse, FindingResponse


class DisputeService:
    ACTIVE_STATUSES = (DisputeStatus.OPEN, DisputeStatus.NEEDS_INFO)

    @staticmethod
    def _finding(db: Session, ctx: TenantContext, finding_id: str) -> Finding:
        finding = (
            db.query(Finding)
            .join(SubmissionRevision, Finding.submission_revision_id == SubmissionRevision.id)
            .join(Submission, SubmissionRevision.submission_id == Submission.id)
            .options(joinedload(Finding.fact), joinedload(Finding.guideline))
            .filter(Finding.id == finding_id)
            .first()
        )
        if not finding or finding.revision.submission.organization_id != ctx.org_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Finding not found.")
        return finding

    @staticmethod
    def _response(dispute: Dispute) -> DisputeResponse:
        finding = dispute.finding
        revision = finding.revision
        submission = revision.submission
        return DisputeResponse(
            id=dispute.id, organization_id=dispute.organization_id, finding_id=dispute.finding_id,
            submission_id=submission.id, revision_id=revision.id, revision_number=revision.revision_number,
            raised_by_user_id=dispute.raised_by_user_id,
            raised_by_name=dispute.raised_by.full_name if dispute.raised_by else None,
            reason=dispute.reason, status=dispute.status, resolution_note=dispute.resolution_note,
            override_verdict=dispute.override_verdict, resolved_by_user_id=dispute.resolved_by_user_id,
            resolved_by_name=dispute.resolved_by.full_name if dispute.resolved_by else None,
            created_at=dispute.created_at, updated_at=dispute.updated_at,
            finding=FindingResponse.model_validate(finding),
        )

    @classmethod
    def create(cls, db: Session, ctx: TenantContext, req: DisputeCreateRequest) -> DisputeResponse:
        finding = cls._finding(db, ctx, req.finding_id)
        if ctx.role == UserRole.CREATOR and finding.revision.submission.creator_user_id != ctx.user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Creators can only dispute findings on their own submissions.")
        duplicate = db.query(Dispute).filter(
            Dispute.organization_id == ctx.org_id, Dispute.finding_id == finding.id,
            Dispute.raised_by_user_id == ctx.user.id, Dispute.status.in_(cls.ACTIVE_STATUSES),
        ).first()
        if duplicate:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="An active dispute already exists for this finding.")
        dispute = Dispute(organization_id=ctx.org_id, finding_id=finding.id, raised_by_user_id=ctx.user.id, reason=req.reason)
        db.add(dispute)
        db.flush()
        db.add(ReviewLog(organization_id=ctx.org_id, submission_id=finding.revision.submission_id, user_id=ctx.user.id,
                         action="dispute_created", comment=req.reason,
                         metadata_json={"dispute_id": dispute.id, "finding_id": finding.id, "original_verdict": finding.verdict.value}))
        db.commit()
        return cls.get(db, ctx, dispute.id)

    @classmethod
    def get(cls, db: Session, ctx: TenantContext, dispute_id: str) -> DisputeResponse:
        dispute = db.query(Dispute).options(
            joinedload(Dispute.raised_by), joinedload(Dispute.resolved_by),
            joinedload(Dispute.finding).joinedload(Finding.fact), joinedload(Dispute.finding).joinedload(Finding.guideline),
            joinedload(Dispute.finding).joinedload(Finding.revision).joinedload(SubmissionRevision.submission),
        ).filter(Dispute.id == dispute_id, Dispute.organization_id == ctx.org_id).first()
        if not dispute:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dispute not found.")
        finding = dispute.finding
        if ctx.role == UserRole.CREATOR and finding.revision.submission.creator_user_id != ctx.user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Creators can only view disputes on their own submissions.")
        return cls._response(dispute)

    @classmethod
    def list(cls, db: Session, ctx: TenantContext, offset: int, limit: int, queue_only: bool) -> list[DisputeResponse]:
        query = db.query(Dispute).join(Finding, Dispute.finding_id == Finding.id).join(SubmissionRevision, Finding.submission_revision_id == SubmissionRevision.id).join(Submission, SubmissionRevision.submission_id == Submission.id)
        query = query.filter(Dispute.organization_id == ctx.org_id)
        if ctx.role == UserRole.CREATOR:
            query = query.filter(Submission.creator_user_id == ctx.user.id)
        if queue_only:
            query = query.filter(Dispute.status.in_(cls.ACTIVE_STATUSES))
        disputes = query.options(
            joinedload(Dispute.raised_by), joinedload(Dispute.resolved_by),
            joinedload(Dispute.finding).joinedload(Finding.fact), joinedload(Dispute.finding).joinedload(Finding.guideline),
            joinedload(Dispute.finding).joinedload(Finding.revision).joinedload(SubmissionRevision.submission),
        ).order_by(Dispute.created_at.desc()).offset(offset).limit(limit).all()
        return [cls._response(dispute) for dispute in disputes]

    @classmethod
    def resolve(cls, db: Session, ctx: TenantContext, dispute_id: str, req: DisputeResolutionRequest) -> DisputeResponse:
        if ctx.role not in (UserRole.ADMIN, UserRole.REVIEWER):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only reviewers and admins can resolve disputes.")
        dispute_response = cls.get(db, ctx, dispute_id)
        dispute = db.get(Dispute, dispute_response.id)
        if dispute.status not in cls.ACTIVE_STATUSES:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="This dispute is already resolved.")
        finding = cls._finding(db, ctx, dispute.finding_id)
        action_map = {"uphold": DisputeStatus.UPHELD, "override": DisputeStatus.REJECTED, "request_info": DisputeStatus.NEEDS_INFO}
        dispute.status = action_map[req.action]
        dispute.resolution_note = req.reason
        dispute.override_verdict = req.override_verdict
        dispute.resolved_by_user_id = ctx.user.id if req.action != "request_info" else None
        db.add(ReviewLog(organization_id=ctx.org_id, submission_id=finding.revision.submission_id, user_id=ctx.user.id,
                         action=f"dispute_{req.action}", comment=req.reason,
                         metadata_json={"dispute_id": dispute.id, "finding_id": finding.id,
                                        "previous_verdict": finding.verdict.value,
                                        "updated_verdict": req.override_verdict.value if req.override_verdict else finding.verdict.value}))
        db.commit()
        return cls.get(db, ctx, dispute.id)
