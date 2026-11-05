from datetime import datetime, timezone
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.api.deps import TenantContext
from app.models.submission import Submission, SubmissionRevision, Finding, Dispute, ReviewLog
from app.models.knowledge import Guideline, ApprovedFact

class AnalyticsService:
 @staticmethod
 def dashboard(db: Session, ctx: TenantContext, start: datetime|None, end: datetime|None):
  submission_query=db.query(Submission).filter(Submission.organization_id==ctx.org_id)
  if start: submission_query=submission_query.filter(Submission.created_at>=start)
  if end: submission_query=submission_query.filter(Submission.created_at<=end)
  submissions=submission_query.all(); ids=[s.id for s in submissions]
  revisions=db.query(SubmissionRevision).filter(SubmissionRevision.submission_id.in_(ids)).all() if ids else []
  revision_ids=[r.id for r in revisions]
  findings=db.query(Finding).filter(Finding.submission_revision_id.in_(revision_ids)).all() if revision_ids else []
  verdicts={}; trends={}
  for finding in findings: verdicts[finding.verdict.value]=verdicts.get(finding.verdict.value,0)+1
  for revision in revisions:
   key=revision.created_at.date().isoformat(); bucket=trends.setdefault(key,{"date":key,"approved":0,"rejected":0,"total":0});bucket["total"]+=1
   if revision.overall_verdict.value=="CORRECT":bucket["approved"]+=1
   elif revision.overall_verdict.value not in {"MIXED","NEEDS_REVIEW"}:bucket["rejected"]+=1
  guideline_counts={}
  for f in findings:
   if f.guideline_id: guideline_counts[f.guideline_id]=guideline_counts.get(f.guideline_id,0)+1
  guideline_names={g.id:g.title for g in db.query(Guideline).filter(Guideline.organization_id==ctx.org_id).all()}
  ranking=[{"guideline_id":k,"title":guideline_names.get(k,"Archived guideline"),"finding_count":v} for k,v in sorted(guideline_counts.items(),key=lambda x:x[1],reverse=True)[:10]]
  dispute_query=db.query(Dispute).filter(Dispute.organization_id==ctx.org_id)
  disputes=dispute_query.all(); logs=db.query(ReviewLog).filter(ReviewLog.organization_id==ctx.org_id,ReviewLog.action.like("dispute_%")).order_by(ReviewLog.created_at.desc()).limit(20).all()
  fact_warnings=db.query(ApprovedFact).filter(ApprovedFact.organization_id==ctx.org_id,ApprovedFact.review_status=="pending").count()
  return {"kpis":{"total_submissions":len(submissions),"total_revisions":len(revisions),"total_findings":len(findings),"pending_factwatch_actions":fact_warnings},"verdicts":verdicts,"trends":list(sorted(trends.values(),key=lambda x:x["date"])),"guideline_violations":ranking,"disputes":{"total":len(disputes),"open":sum(x.status.value in {"open","needs_info"} for x in disputes),"overrides":sum(x.status.value=="rejected" for x in disputes)},"recent_review_activity":[{"action":x.action,"comment":x.comment,"created_at":x.created_at,"submission_id":x.submission_id} for x in logs],"data_note":"Metrics are calculated from persisted records in the selected date range; empty lists represent unavailable data."}
