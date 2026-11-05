from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.api.deps import TenantContext
from app.models.enums import GuidelineStatus, DisputeStatus
from app.models.knowledge import Guideline
from app.models.submission import Finding, Dispute


class GuidelineHealthService:
    """Evidence-only guideline warnings. It never changes a guideline."""
    @staticmethod
    def dashboard(db: Session, ctx: TenantContext) -> dict:
        guidelines = db.query(Guideline).filter(Guideline.organization_id == ctx.org_id, Guideline.status == GuidelineStatus.ACTIVE).all()
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        warnings, healthy = [], []
        for guideline in guidelines:
            finding_ids = [row[0] for row in db.query(Finding.id).filter(Finding.guideline_id == guideline.id).all()]
            disputes = db.query(Dispute).filter(Dispute.organization_id == ctx.org_id, Dispute.finding_id.in_(finding_ids)).all() if finding_ids else []
            override_count = sum(item.status == DisputeStatus.REJECTED for item in disputes)
            evidence = {"finding_count": len(finding_ids), "dispute_count": len(disputes), "override_count": override_count}
            issues = []
            if len(disputes) >= 2:
                issues.append(("frequently_disputed", "This active rule has at least two persisted disputes.", "Review the rule wording and its supporting evidence."))
            if override_count >= 2:
                issues.append(("repeated_overrides", "At least two reviewer overrides are recorded for findings tied to this rule.", "Clarify the rule or narrow its scope."))
            missing = [name for name, value in (("source", guideline.source), ("scope", guideline.scope), ("owner", guideline.owner_user_id)) if not value]
            if missing:
                issues.append(("missing_metadata", f"Missing required governance metadata: {', '.join(missing)}.", "Add the missing source, scope, or accountable owner."))
            if guideline.review_due_at and guideline.review_due_at <= now:
                issues.append(("review_due", "The configured review date has passed.", "Schedule and record a periodic rule review."))
            if disputes and not guideline.description:
                issues.append(("ambiguous", "Dispute history exists while the guideline has no explanatory description.", "Add examples or explanatory guidance for creators and reviewers."))
            if issues:
                for kind, reason, recommendation in issues:
                    warnings.append({"type": kind, "guideline_id": guideline.id, "guideline_title": guideline.title, "reason": reason, "recommendation": recommendation, "evidence": evidence})
            else:
                healthy.append({"guideline_id": guideline.id, "guideline_title": guideline.title, "evidence": evidence})
        # Detect only explicit deterministic phrase conflicts, never semantic guesses.
        for left in guidelines:
            for right in guidelines:
                if left.id >= right.id:
                    continue
                overlap = set((left.required_phrases or [])) & set((right.prohibited_phrases or []))
                overlap |= set((right.required_phrases or [])) & set((left.prohibited_phrases or []))
                for phrase in sorted(overlap):
                    warnings.append({"type": "potential_conflict", "guideline_id": left.id, "guideline_title": left.title, "reason": f"Phrase '{phrase}' is required by one active rule and prohibited by another.", "recommendation": "Resolve the conflicting phrase requirements and document precedence.", "evidence": {"phrase": phrase, "other_guideline_id": right.id, "other_guideline_title": right.title}})
        return {"healthy_guidelines": healthy, "warnings": warnings, "active_guideline_count": len(guidelines)}
