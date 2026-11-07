import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { Link, useLocation, useParams, useSearchParams } from 'react-router-dom';
import { AlertCircle, ArrowLeft, CheckCircle2, ChevronRight, History, Pencil, RefreshCw, Save, X } from 'lucide-react';
import apiClient from '../api/client';
import { useAuth } from '../contexts/AuthContext';
import { HighlightedCopy, ReviewMode, VerdictBadge, countFindings, formatLane, verdictMeta } from '../components/reviews/ReviewPrimitives';

function requestErrorMessage(error, fallback) {
  const detail = error.response?.data?.detail;
  if (Array.isArray(detail)) return detail.map((item) => item.msg).join(' ');
  return detail || error.message || fallback;
}

function readableStatus(status) {
  return status?.replaceAll('_', ' ') || 'Unknown status';
}

function formatDate(date) {
  if (!date) return 'Date unavailable';
  return new Intl.DateTimeFormat(undefined, { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(date));
}

const COUNT_ORDER = ['CORRECT', 'CONTRADICTED', 'OUTDATED', 'UNSUPPORTED', 'UNVERIFIABLE'];

function FindingCard({ finding, index, onDispute }) {
  const hasFact = Boolean(finding.fact_name || finding.fact_approved_value || finding.fact_source);
  const hasGuideline = Boolean(finding.guideline_title || finding.guideline_source);

  return (
    <article className="rounded-xl border border-slate-200 bg-white p-4 shadow-xs">
      <div className="flex flex-col justify-between gap-3 sm:flex-row sm:items-start">
        <div className="min-w-0">
          <p className="text-[11px] font-bold uppercase tracking-[0.14em] text-slate-400">Finding {index + 1}</p>
          <p className="mt-1 text-sm font-semibold leading-6 text-slate-900">“{finding.claim_text}”</p>
        </div>
        <VerdictBadge verdict={finding.verdict} className="shrink-0" />
      </div>

      <p className="mt-3 text-sm leading-6 text-slate-700">{finding.explanation}</p>

      <div className="mt-3 flex flex-wrap items-center gap-2 text-xs">
        <span className="rounded-md bg-slate-100 px-2 py-1 font-medium text-slate-700">{formatLane(finding.lane)}</span>
        {typeof finding.confidence_score === 'number' && (
          <span className="text-slate-400">Confidence {Math.round(finding.confidence_score * 100)}%</span>
        )}
      </div>

      {(hasFact || hasGuideline) && (
        <div className="mt-4 grid gap-3 border-t border-slate-100 pt-3 sm:grid-cols-2">
          {hasFact && (
            <div className="rounded-lg bg-emerald-50/70 p-3 text-xs leading-5 text-emerald-950">
              <p className="font-bold uppercase tracking-wide text-emerald-700">Approved fact</p>
              {finding.fact_name && <p className="mt-1 font-semibold">{finding.fact_name}{finding.fact_version ? ` · v${finding.fact_version}` : ''}</p>}
              {finding.fact_approved_value && <p>Approved value: {finding.fact_approved_value}</p>}
              {finding.fact_source && <p className="text-emerald-800">Source: {finding.fact_source}</p>}
            </div>
          )}
          {hasGuideline && (
            <div className="rounded-lg bg-indigo-50/70 p-3 text-xs leading-5 text-indigo-950">
              <p className="font-bold uppercase tracking-wide text-indigo-700">Supporting guideline</p>
              {finding.guideline_title && <p className="mt-1 font-semibold">{finding.guideline_title}{finding.guideline_version ? ` · v${finding.guideline_version}` : ''}</p>}
              {finding.guideline_source && <p className="text-indigo-800">Source: {finding.guideline_source}</p>}
            </div>
          )}
        </div>
      )}

      {finding.suggested_correction && (
        <div className="mt-3 rounded-lg border border-blue-100 bg-blue-50 p-3 text-xs leading-5 text-blue-950">
          <span className="font-bold">Suggested correction: </span>{finding.suggested_correction}
        </div>
      )}
      {onDispute && (
        <button onClick={() => onDispute(finding)} className="mt-4 text-xs font-semibold text-indigo-700 hover:text-indigo-900">Dispute this finding</button>
      )}
    </article>
  );
}

export default function ReviewResultPage() {
  const { submissionId } = useParams();
  const { role, user } = useAuth();
  const location = useLocation();
  const [searchParams, setSearchParams] = useSearchParams();
  const [submission, setSubmission] = useState(location.state?.submission || null);
  const [latestReviewResult, setLatestReviewResult] = useState(location.state?.reviewResult || null);
  const [loading, setLoading] = useState(!location.state?.submission);
  const [error, setError] = useState(null);
  const [editing, setEditing] = useState(false);
  const [contentText, setContentText] = useState('');
  const [changeSummary, setChangeSummary] = useState('');
  const [rechecking, setRechecking] = useState(false);
  const [recheckError, setRecheckError] = useState(null);
  const [disputeFinding, setDisputeFinding] = useState(null);
  const [disputeReason, setDisputeReason] = useState('');
  const [disputeError, setDisputeError] = useState(null);
  const [submittingDispute, setSubmittingDispute] = useState(false);

  const requestedRevisionId = searchParams.get('revision');

  const loadSubmission = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await apiClient.get(`/api/v1/submissions/${submissionId}`);
      setSubmission(response.data);
    } catch (requestError) {
      setError(requestErrorMessage(requestError, 'Unable to load this submission.'));
    } finally {
      setLoading(false);
    }
  }, [submissionId]);

  useEffect(() => {
    loadSubmission();
    return () => {};
  }, [loadSubmission]);

  const revisions = useMemo(
    () => [...(submission?.revisions || [])].sort((a, b) => b.revision_number - a.revision_number),
    [submission]
  );
  const selectedRevision = revisions.find((revision) => revision.id === requestedRevisionId)
    || submission?.latest_revision
    || revisions[0]
    || null;
  const canRecheck = role === 'admin' || role === 'creator';
  const canDispute = role === 'creator' && submission?.creator_user_id === user?.id;
  const isLatestRevision = selectedRevision?.id === submission?.latest_revision?.id;

  useEffect(() => {
    if (selectedRevision) {
      setContentText(selectedRevision.content_text);
      setChangeSummary('');
      setEditing(false);
      setRecheckError(null);
    }
    return () => {};
  }, [selectedRevision?.id]);

  const reviewResultForSelected = latestReviewResult?.revision_id === selectedRevision?.id
    ? latestReviewResult
    : null;
  const findings = reviewResultForSelected?.findings || selectedRevision?.findings || [];
  const counts = reviewResultForSelected
    ? {
      CORRECT: reviewResultForSelected.correct_claims,
      CONTRADICTED: reviewResultForSelected.contradicted_claims,
      OUTDATED: reviewResultForSelected.outdated_claims,
      UNSUPPORTED: reviewResultForSelected.unsupported_claims,
      UNVERIFIABLE: reviewResultForSelected.unverifiable_claims,
    }
    : countFindings(findings);
  const reviewFallback = reviewResultForSelected ? reviewResultForSelected.is_fallback : selectedRevision?.review_used_fallback;

  const selectRevision = (revisionId) => {
    setSearchParams({ revision: revisionId });
  };

  const handleRecheck = async (event) => {
    event.preventDefault();
    setRechecking(true);
    setRecheckError(null);
    try {
      const response = await apiClient.post(`/api/v1/submissions/${submissionId}/recheck`, {
        content_text: contentText.trim(),
        change_summary: changeSummary.trim() || null,
      });
      setSubmission(response.data);
      setLatestReviewResult(response.data.review_result || null);
      const newRevisionId = response.data.latest_revision?.id;
      setEditing(false);
      if (newRevisionId) setSearchParams({ revision: newRevisionId });
    } catch (requestError) {
      setRecheckError(requestErrorMessage(requestError, 'Unable to recheck this revision.'));
    } finally {
      setRechecking(false);
    }
  };

  const handleDispute = async (event) => {
    event.preventDefault();
    setSubmittingDispute(true); setDisputeError(null);
    try {
      await apiClient.post('/api/v1/disputes/', { finding_id: disputeFinding.id, reason: disputeReason.trim() });
      setDisputeFinding(null); setDisputeReason('');
    } catch (requestError) {
      setDisputeError(requestErrorMessage(requestError, 'Unable to submit the dispute.'));
    } finally { setSubmittingDispute(false); }
  };

  if (loading && !submission) {
    return (
      <div className="rounded-xl border border-slate-200 bg-white p-12 text-center text-sm text-slate-500">
        <RefreshCw className="mx-auto mb-3 h-6 w-6 animate-spin text-indigo-600" />
        Loading review evidence…
      </div>
    );
  }

  if (error && !submission) {
    return (
      <div className="mx-auto max-w-2xl rounded-xl border border-rose-200 bg-rose-50 p-6 text-center">
        <AlertCircle className="mx-auto mb-3 h-7 w-7 text-rose-600" />
        <h1 className="font-bold text-rose-950">Review unavailable</h1>
        <p className="mt-1 text-sm text-rose-800">{error}</p>
        <Link to="/submissions" className="mt-4 inline-flex text-sm font-semibold text-indigo-700 hover:text-indigo-900">Return to history</Link>
      </div>
    );
  }

  if (!submission || !selectedRevision) {
    return null;
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
        <div className="min-w-0">
          <Link to="/submissions" className="inline-flex items-center gap-1 text-sm font-semibold text-indigo-700 hover:text-indigo-900">
            <ArrowLeft className="h-4 w-4" /> Submission history
          </Link>
          <div className="mt-3 flex flex-wrap items-center gap-3">
            <h1 className="max-w-3xl truncate text-2xl font-bold tracking-tight text-slate-900">{submission.title}</h1>
            <VerdictBadge verdict={selectedRevision.overall_verdict} />
          </div>
          <p className="mt-1 text-sm text-slate-500">
            Revision {selectedRevision.revision_number} · {readableStatus(submission.current_status)} · submitted {formatDate(selectedRevision.created_at)}
          </p>
        </div>
        <div className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-xs text-slate-600 shadow-xs">
          <span className="font-semibold text-slate-700">Review mode: </span><ReviewMode isFallback={reviewFallback} />
        </div>
      </div>

      {error && (
        <div role="alert" className="flex items-center justify-between gap-3 rounded-lg border border-amber-200 bg-amber-50 p-3 text-sm text-amber-900">
          <span>{error}</span>
          <button onClick={loadSubmission} className="font-semibold underline">Try again</button>
        </div>
      )}

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
        {COUNT_ORDER.map((verdict) => {
          const meta = verdictMeta(verdict);
          return (
            <div key={verdict} className={`rounded-xl border p-4 ${meta.badge}`}>
              <p className="text-[11px] font-bold uppercase tracking-[0.12em] opacity-75">{meta.label}</p>
              <p className="mt-1 text-2xl font-bold">{counts[verdict] || 0}</p>
            </div>
          );
        })}
      </div>

      <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_300px]">
        <div className="space-y-6">
          <section className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-xs">
            <div className="flex flex-col gap-3 border-b border-slate-100 px-5 py-4 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <h2 className="font-bold text-slate-900">Submitted text</h2>
                <p className="mt-0.5 text-xs text-slate-500">Highlights use the backend’s UTF-16 offsets. Hover a highlight to see every overlapping finding.</p>
              </div>
              {canRecheck && isLatestRevision && !editing && (
                <button
                  onClick={() => setEditing(true)}
                  className="inline-flex items-center justify-center gap-2 rounded-lg border border-slate-200 px-3 py-2 text-sm font-semibold text-slate-700 transition hover:border-indigo-300 hover:bg-indigo-50 hover:text-indigo-800"
                >
                  <Pencil className="h-4 w-4" /> Edit and recheck
                </button>
              )}
            </div>

            {editing ? (
              <form onSubmit={handleRecheck} className="space-y-4 p-5">
                {recheckError && (
                  <div role="alert" className="flex gap-2 rounded-lg border border-rose-200 bg-rose-50 p-3 text-sm text-rose-800">
                    <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" /> {recheckError}
                  </div>
                )}
                <div>
                  <label htmlFor="recheck-copy" className="mb-1.5 block text-sm font-semibold text-slate-800">Revised marketing copy</label>
                  <textarea
                    id="recheck-copy"
                    required
                    maxLength={100000}
                    rows={12}
                    value={contentText}
                    onChange={(event) => setContentText(event.target.value)}
                    className="w-full resize-y rounded-lg border border-slate-200 p-3 font-mono text-sm leading-6 outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100"
                  />
                </div>
                <div>
                  <label htmlFor="change-summary" className="mb-1.5 block text-sm font-semibold text-slate-800">Change summary <span className="font-normal text-slate-400">(optional)</span></label>
                  <input
                    id="change-summary"
                    maxLength={500}
                    value={changeSummary}
                    onChange={(event) => setChangeSummary(event.target.value)}
                    placeholder="e.g. Added the approved qualifier and removed the warranty claim"
                    className="w-full rounded-lg border border-slate-200 px-3 py-2.5 text-sm outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100"
                  />
                </div>
                <div className="flex flex-wrap justify-end gap-2">
                  <button type="button" onClick={() => setEditing(false)} className="inline-flex items-center gap-1 rounded-lg px-3 py-2 text-sm font-semibold text-slate-600 hover:bg-slate-100">
                    <X className="h-4 w-4" /> Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={!contentText.trim() || rechecking}
                    className="inline-flex items-center gap-2 rounded-lg bg-indigo-600 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-700 disabled:cursor-not-allowed disabled:bg-slate-300"
                  >
                    <Save className="h-4 w-4" /> {rechecking ? 'Rechecking…' : 'Create new revision'}
                  </button>
                </div>
              </form>
            ) : (
              <div className="whitespace-pre-wrap break-words p-5 text-sm leading-7 text-slate-800">
                <HighlightedCopy text={selectedRevision.content_text} findings={findings} />
              </div>
            )}
          </section>

          <section>
            <div className="mb-3 flex items-center justify-between gap-3">
              <div>
                <h2 className="font-bold text-slate-900">Evidence-linked findings</h2>
                <p className="mt-0.5 text-xs text-slate-500">{findings.length} finding{findings.length === 1 ? '' : 's'} for revision {selectedRevision.revision_number}</p>
              </div>
              {reviewResultForSelected?.total_findings !== undefined && (
                <span className="text-xs text-slate-400">{reviewResultForSelected.total_findings} total</span>
              )}
            </div>
            {findings.length === 0 ? (
              <div className="rounded-xl border border-dashed border-slate-300 bg-white p-8 text-center">
                <CheckCircle2 className="mx-auto mb-2 h-6 w-6 text-emerald-600" />
                <p className="text-sm font-semibold text-slate-700">No claim findings were recorded for this revision.</p>
              </div>
            ) : (
              <div className="space-y-3">
                {findings.map((finding, index) => <FindingCard key={finding.id || `${finding.start_offset}-${index}`} finding={finding} index={index} onDispute={canDispute ? setDisputeFinding : null} />)}
              </div>
            )}
          </section>
        </div>

        <aside className="h-fit rounded-xl border border-slate-200 bg-white shadow-xs xl:sticky xl:top-24">
          <div className="border-b border-slate-100 px-4 py-3">
            <div className="flex items-center gap-2 font-bold text-slate-900"><History className="h-4 w-4 text-slate-500" /> Revision history</div>
            <p className="mt-1 text-xs leading-5 text-slate-500">Each review remains immutable after recheck.</p>
          </div>
          <div className="p-2">
            {revisions.map((revision) => {
              const selected = revision.id === selectedRevision.id;
              return (
                <button
                  key={revision.id}
                  onClick={() => selectRevision(revision.id)}
                  className={`mb-1 w-full rounded-lg p-3 text-left transition last:mb-0 ${selected ? 'bg-indigo-50 ring-1 ring-indigo-100' : 'hover:bg-slate-50'}`}
                >
                  <div className="flex items-center justify-between gap-2">
                    <span className="text-sm font-semibold text-slate-800">Revision {revision.revision_number}</span>
                    {selected && <ChevronRight className="h-4 w-4 text-indigo-600" />}
                  </div>
                  <div className="mt-1 flex flex-wrap items-center gap-2">
                    <VerdictBadge verdict={revision.overall_verdict} className="px-2 py-0.5 text-[10px]" />
                    <span className="text-[11px] text-slate-400">{formatDate(revision.created_at)}</span>
                  </div>
                  {revision.change_summary && <p className="mt-2 line-clamp-2 text-xs leading-5 text-slate-500">{revision.change_summary}</p>}
                </button>
              );
            })}
          </div>
          {canRecheck && !isLatestRevision && (
            <div className="border-t border-slate-100 p-3 text-xs leading-5 text-slate-500">
              Rechecks are created from the latest revision so the selected historical record stays unchanged.
            </div>
          )}
        </aside>
      </div>
      {disputeFinding && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/40 p-4">
          <form onSubmit={handleDispute} className="w-full max-w-lg rounded-xl bg-white p-6 shadow-xl">
            <h2 className="text-lg font-bold text-slate-900">Dispute finding</h2>
            <p className="mt-1 text-sm text-slate-600">Explain why “{disputeFinding.claim_text}” should be reconsidered. The original finding will remain preserved.</p>
            {disputeError && <div role="alert" className="mt-4 rounded-lg border border-rose-200 bg-rose-50 p-3 text-sm text-rose-800">{disputeError}</div>}
            <textarea required minLength={10} maxLength={4000} value={disputeReason} onChange={(event) => setDisputeReason(event.target.value)} className="mt-4 min-h-32 w-full rounded-lg border border-slate-300 p-3 text-sm" placeholder="Provide supporting context or evidence…" />
            <div className="mt-4 flex justify-end gap-2"><button type="button" onClick={() => { setDisputeFinding(null); setDisputeError(null); }} className="rounded-lg px-3 py-2 text-sm font-semibold text-slate-600">Cancel</button><button disabled={submittingDispute || disputeReason.trim().length < 10} className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-semibold text-white disabled:bg-slate-400">{submittingDispute ? 'Submitting…' : 'Submit dispute'}</button></div>
          </form>
        </div>
      )}
    </div>
  );
}
