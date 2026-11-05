from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.api.deps import TenantContext
from app.models.knowledge import ApprovedFact
from app.models.submission import Finding

class FactWatchService:
    @staticmethod
    def dashboard(db: Session, ctx: TenantContext, horizon_days: int = 30) -> dict:
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        horizon = now + timedelta(days=horizon_days)
        facts = db.query(ApprovedFact).filter(ApprovedFact.organization_id == ctx.org_id).all()
        def affected(fact):
            return db.query(Finding).filter(Finding.fact_id == fact.id).count()
        items = [{"id": fact.id, "fact_name": fact.fact_name, "version": fact.version, "approved_value": fact.approved_value, "valid_until": fact.valid_until, "superseded_by_id": fact.superseded_by_id, "review_status": fact.review_status, "affected_findings": affected(fact)} for fact in facts]
        return {"expiring": [x for x in items if x["valid_until"] and now < x["valid_until"] <= horizon], "expired": [x for x in items if x["valid_until"] and x["valid_until"] <= now], "superseded": [x for x in items if x["superseded_by_id"]], "pending_review": [x for x in items if x["review_status"] == "pending" and (x["valid_until"] and x["valid_until"] <= horizon or x["superseded_by_id"])], "affected_submissions": sum(x["affected_findings"] for x in items)}
    @staticmethod
    def review(db: Session, ctx: TenantContext, fact_id: str, review_status: str) -> ApprovedFact:
        if review_status not in {"acknowledged", "resolved"}:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="review_status must be acknowledged or resolved.")
        fact = db.query(ApprovedFact).filter(ApprovedFact.id == fact_id, ApprovedFact.organization_id == ctx.org_id).first()
        if not fact: raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fact not found.")
        fact.review_status, fact.reviewed_by_user_id, fact.reviewed_at = review_status, ctx.user.id, datetime.now(timezone.utc)
        db.commit(); db.refresh(fact); return fact
