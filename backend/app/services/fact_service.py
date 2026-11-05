from typing import List, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.api.deps import TenantContext
from app.models.knowledge import ApprovedFact
from app.models.enums import FactStatus, UserRole
from app.schemas.knowledge import FactCreateRequest, FactUpdateRequest, FactSupersedeRequest


class FactService:
    @staticmethod
    def create(db: Session, ctx: TenantContext, req: FactCreateRequest) -> ApprovedFact:
        # Admins create approved facts; creators submit pending approval facts
        initial_status = FactStatus.APPROVED if ctx.role == UserRole.ADMIN else FactStatus.PENDING_APPROVAL
        approved_by = ctx.user.id if ctx.role == UserRole.ADMIN else None
        approved_at = datetime.now(timezone.utc) if ctx.role == UserRole.ADMIN else None

        fact = ApprovedFact(
            organization_id=ctx.org_id,
            fact_name=req.fact_name.strip(),
            approved_value=req.approved_value.strip(),
            numeric_value=req.numeric_value,
            numeric_operator=req.numeric_operator.strip() if req.numeric_operator else None,
            unit=req.unit.strip() if req.unit else None,
            description=req.description.strip() if req.description else None,
            category=req.category.strip().lower(),
            source=req.source.strip() if req.source else "Manual Entry",
            scope=req.scope.strip() if req.scope else "global",
            required_qualifiers=req.required_qualifiers or [],
            valid_from=req.valid_from,
            valid_until=req.valid_until,
            version=1,
            status=initial_status,
            approved_by_user_id=approved_by,
            approved_at=approved_at
        )
        db.add(fact)
        db.commit()
        db.refresh(fact)
        return fact

    @staticmethod
    def list(
        db: Session,
        ctx: TenantContext,
        category: Optional[str] = None,
        status_filter: Optional[FactStatus] = None,
        scope: Optional[str] = None,
        search: Optional[str] = None
    ) -> List[ApprovedFact]:
        query = db.query(ApprovedFact).filter(ApprovedFact.organization_id == ctx.org_id)
        if category:
            query = query.filter(ApprovedFact.category == category.lower())
        if status_filter:
            query = query.filter(ApprovedFact.status == status_filter)
        if scope:
            query = query.filter(ApprovedFact.scope == scope)
        if search:
            pattern = f"%{search.lower()}%"
            query = query.filter(
                (ApprovedFact.fact_name.ilike(pattern)) | (ApprovedFact.approved_value.ilike(pattern))
            )
        return query.order_by(ApprovedFact.created_at.desc()).all()

    @staticmethod
    def get(db: Session, ctx: TenantContext, fact_id: str) -> ApprovedFact:
        fact = db.query(ApprovedFact).filter(
            ApprovedFact.id == fact_id,
            ApprovedFact.organization_id == ctx.org_id
        ).first()
        if not fact:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Approved fact with ID '{fact_id}' not found in this organization."
            )
        return fact

    @staticmethod
    def update(db: Session, ctx: TenantContext, fact_id: str, req: FactUpdateRequest) -> ApprovedFact:
        fact = FactService.get(db, ctx, fact_id)
        if ctx.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only Organization Admins can directly update approved facts. Use supersede for new revisions."
            )

        if req.fact_name is not None:
            fact.fact_name = req.fact_name.strip()
        if req.approved_value is not None:
            fact.approved_value = req.approved_value.strip()
        if req.numeric_value is not None:
            fact.numeric_value = req.numeric_value
        if req.numeric_operator is not None:
            fact.numeric_operator = req.numeric_operator.strip()
        if req.unit is not None:
            fact.unit = req.unit.strip()
        if req.description is not None:
            fact.description = req.description.strip()
        if req.category is not None:
            fact.category = req.category.strip().lower()
        if req.source is not None:
            fact.source = req.source.strip()
        if req.scope is not None:
            fact.scope = req.scope.strip()
        if req.required_qualifiers is not None:
            fact.required_qualifiers = req.required_qualifiers
        if req.valid_from is not None:
            fact.valid_from = req.valid_from
        if req.valid_until is not None:
            fact.valid_until = req.valid_until

        db.commit()
        db.refresh(fact)
        return fact

    @staticmethod
    def supersede(db: Session, ctx: TenantContext, old_fact_id: str, req: FactSupersedeRequest) -> ApprovedFact:
        """Creates a new version of the fact and marks the predecessor as SUPERSEDED.
        Preserves full lineage and audit history.
        """
        if ctx.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only Organization Admins can supersede approved facts."
            )

        old_fact = FactService.get(db, ctx, old_fact_id)

        # Create new version
        new_fact = ApprovedFact(
            organization_id=ctx.org_id,
            fact_name=old_fact.fact_name,
            approved_value=req.approved_value.strip(),
            numeric_value=req.numeric_value if req.numeric_value is not None else old_fact.numeric_value,
            numeric_operator=req.numeric_operator.strip() if req.numeric_operator else old_fact.numeric_operator,
            unit=req.unit.strip() if req.unit else old_fact.unit,
            description=req.description.strip() if req.description else old_fact.description,
            category=old_fact.category,
            source=req.source.strip() if req.source else old_fact.source,
            scope=req.scope.strip() if req.scope else old_fact.scope,
            required_qualifiers=req.required_qualifiers if req.required_qualifiers is not None else old_fact.required_qualifiers,
            valid_from=req.valid_from or datetime.now(timezone.utc),
            valid_until=req.valid_until,
            version=old_fact.version + 1,
            status=FactStatus.APPROVED,
            approved_by_user_id=ctx.user.id,
            approved_at=datetime.now(timezone.utc)
        )
        db.add(new_fact)
        db.flush()

        # Update old fact pointer
        old_fact.status = FactStatus.SUPERSEDED
        old_fact.superseded_by_id = new_fact.id
        db.commit()
        db.refresh(new_fact)
        return new_fact

    @staticmethod
    def approve(db: Session, ctx: TenantContext, fact_id: str) -> ApprovedFact:
        if ctx.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only Organization Admins have permission to approve facts."
            )
        fact = FactService.get(db, ctx, fact_id)
        fact.status = FactStatus.APPROVED
        fact.approved_by_user_id = ctx.user.id
        fact.approved_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(fact)
        return fact

    @staticmethod
    def archive(db: Session, ctx: TenantContext, fact_id: str) -> ApprovedFact:
        if ctx.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only Organization Admins have permission to archive facts."
            )
        fact = FactService.get(db, ctx, fact_id)
        fact.status = FactStatus.ARCHIVED
        db.commit()
        db.refresh(fact)
        return fact

