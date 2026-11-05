from typing import List, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.api.deps import TenantContext
from app.models.knowledge import Guideline
from app.models.enums import GuidelineStatus, UserRole
from app.schemas.knowledge import GuidelineCreateRequest, GuidelineUpdateRequest


class GuidelineService:
    @staticmethod
    def create(db: Session, ctx: TenantContext, req: GuidelineCreateRequest) -> Guideline:
        # Admins can create active guidelines immediately; creators submit drafts
        initial_status = GuidelineStatus.ACTIVE if ctx.role == UserRole.ADMIN else GuidelineStatus.DRAFT
        approved_by = ctx.user.id if ctx.role == UserRole.ADMIN else None
        approved_at = datetime.now(timezone.utc) if ctx.role == UserRole.ADMIN else None

        guideline = Guideline(
            organization_id=ctx.org_id,
            title=req.title.strip(),
            description=req.description.strip() if req.description else None,
            category=req.category.strip().lower(),
            rule_text=req.rule_text.strip(),
            prohibited_phrases=req.prohibited_phrases or [],
            required_phrases=req.required_phrases or [],
            source=req.source.strip() if req.source else "Manual Entry",
            scope=req.scope.strip() if req.scope else None,
            owner_user_id=req.owner_user_id,
            review_due_at=req.review_due_at,
            version=1,
            status=initial_status,
            created_by_user_id=ctx.user.id,
            approved_by_user_id=approved_by,
            approved_at=approved_at
        )
        db.add(guideline)
        db.commit()
        db.refresh(guideline)
        return guideline

    @staticmethod
    def list(
        db: Session,
        ctx: TenantContext,
        category: Optional[str] = None,
        status_filter: Optional[GuidelineStatus] = None,
        search: Optional[str] = None
    ) -> List[Guideline]:
        query = db.query(Guideline).filter(Guideline.organization_id == ctx.org_id)
        if category:
            query = query.filter(Guideline.category == category.lower())
        if status_filter:
            query = query.filter(Guideline.status == status_filter)
        if search:
            pattern = f"%{search.lower()}%"
            query = query.filter(
                (Guideline.title.ilike(pattern)) | (Guideline.rule_text.ilike(pattern))
            )
        return query.order_by(Guideline.created_at.desc()).all()

    @staticmethod
    def get(db: Session, ctx: TenantContext, guideline_id: str) -> Guideline:
        guideline = db.query(Guideline).filter(
            Guideline.id == guideline_id,
            Guideline.organization_id == ctx.org_id
        ).first()
        if not guideline:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Guideline with ID '{guideline_id}' not found in this organization."
            )
        return guideline

    @staticmethod
    def update(db: Session, ctx: TenantContext, guideline_id: str, req: GuidelineUpdateRequest) -> Guideline:
        guideline = GuidelineService.get(db, ctx, guideline_id)

        # Check if rule content changed to bump version
        content_changed = False
        if req.title is not None and req.title.strip() != guideline.title:
            guideline.title = req.title.strip()
        if req.description is not None:
            guideline.description = req.description.strip()
        if req.category is not None:
            guideline.category = req.category.strip().lower()
        if req.source is not None:
            guideline.source = req.source.strip()
        if req.scope is not None:
            guideline.scope = req.scope.strip() or None
        if req.owner_user_id is not None:
            guideline.owner_user_id = req.owner_user_id
        if req.review_due_at is not None:
            guideline.review_due_at = req.review_due_at

        if req.rule_text is not None and req.rule_text.strip() != guideline.rule_text:
            guideline.rule_text = req.rule_text.strip()
            content_changed = True
        if req.prohibited_phrases is not None and req.prohibited_phrases != guideline.prohibited_phrases:
            guideline.prohibited_phrases = req.prohibited_phrases
            content_changed = True
        if req.required_phrases is not None and req.required_phrases != guideline.required_phrases:
            guideline.required_phrases = req.required_phrases
            content_changed = True

        if content_changed:
            guideline.version += 1
            # If a non-admin modifies an active guideline, it falls back to draft requiring re-approval
            if ctx.role != UserRole.ADMIN:
                guideline.status = GuidelineStatus.DRAFT
                guideline.approved_by_user_id = None
                guideline.approved_at = None

        db.commit()
        db.refresh(guideline)
        return guideline

    @staticmethod
    def approve(db: Session, ctx: TenantContext, guideline_id: str) -> Guideline:
        if ctx.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only Organization Admins have permission to approve brand guidelines."
            )
        guideline = GuidelineService.get(db, ctx, guideline_id)
        guideline.status = GuidelineStatus.ACTIVE
        guideline.approved_by_user_id = ctx.user.id
        guideline.approved_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(guideline)
        return guideline

    @staticmethod
    def archive(db: Session, ctx: TenantContext, guideline_id: str) -> Guideline:
        if ctx.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only Organization Admins have permission to archive brand guidelines."
            )
        guideline = GuidelineService.get(db, ctx, guideline_id)
        guideline.status = GuidelineStatus.ARCHIVED
        db.commit()
        db.refresh(guideline)
        return guideline

