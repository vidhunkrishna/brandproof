import React, { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { AlertCircle, ChevronLeft, ChevronRight, ClipboardList, FilePlus2, RefreshCw } from 'lucide-react';
import apiClient from '../api/client';
import { useAuth } from '../contexts/AuthContext';
import { VerdictBadge } from '../components/reviews/ReviewPrimitives';

const PAGE_SIZE = 20;

function requestErrorMessage(error, fallback) {
  const detail = error.response?.data?.detail;
  return detail || error.message || fallback;
}

function readable(value) {
  return value?.replaceAll('_', ' ') || 'Unknown';
}

function formatDate(date) {
  if (!date) return 'Date unavailable';
  return new Intl.DateTimeFormat(undefined, { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(date));
}

export default function SubmissionHistoryPage() {
  const { role } = useAuth();
  const [page, setPage] = useState(0);
  const [submissions, setSubmissions] = useState([]);
  const [hasNextPage, setHasNextPage] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const canSubmit = role === 'admin' || role === 'creator';

  const fetchSubmissions = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      // The API returns an array without a total count. Fetch one extra record to
      // determine whether a next offset page exists without guessing.
      const response = await apiClient.get('/api/v1/submissions/', {
        params: { skip: page * PAGE_SIZE, limit: PAGE_SIZE + 1 },
      });
      const rows = Array.isArray(response.data) ? response.data : [];
      setSubmissions(rows.slice(0, PAGE_SIZE));
      setHasNextPage(rows.length > PAGE_SIZE);
    } catch (requestError) {
      setError(requestErrorMessage(requestError, 'Unable to load submission history.'));
      setSubmissions([]);
      setHasNextPage(false);
    } finally {
      setLoading(false);
    }
  }, [page]);

  useEffect(() => {
    fetchSubmissions();
    return () => {};
  }, [fetchSubmissions]);

  return (
    <div className="space-y-6">
      <div className="flex flex-col justify-between gap-3 sm:flex-row sm:items-end">
        <div>
          <p className="text-xs font-bold uppercase tracking-[0.16em] text-indigo-600">Governance workspace</p>
          <h1 className="mt-1 text-2xl font-bold tracking-tight text-slate-900">Submission history</h1>
          <p className="mt-1 text-sm text-slate-500">Review outcomes for this organization, ordered from newest to oldest.</p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={fetchSubmissions}
            disabled={loading}
            className="inline-flex items-center gap-2 rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50 disabled:text-slate-400"
          >
            <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} /> Refresh
          </button>
          {canSubmit && (
            <Link to="/submit" className="inline-flex items-center gap-2 rounded-lg bg-indigo-600 px-3 py-2 text-sm font-semibold text-white hover:bg-indigo-700">
              <FilePlus2 className="h-4 w-4" /> Submit copy
            </Link>
          )}
        </div>
      </div>

      {error ? (
        <div role="alert" className="rounded-xl border border-rose-200 bg-rose-50 p-5 text-sm text-rose-900">
          <div className="flex gap-2"><AlertCircle className="h-5 w-5 shrink-0 text-rose-600" /> <span>{error}</span></div>
          <button onClick={fetchSubmissions} className="mt-3 font-semibold underline">Try again</button>
        </div>
      ) : loading ? (
        <div className="rounded-xl border border-slate-200 bg-white p-12 text-center text-sm text-slate-500">
          <RefreshCw className="mx-auto mb-3 h-6 w-6 animate-spin text-indigo-600" />
          Loading organization submissions…
        </div>
      ) : submissions.length === 0 ? (
        <div className="rounded-xl border border-dashed border-slate-300 bg-white p-12 text-center">
          <ClipboardList className="mx-auto mb-3 h-8 w-8 text-slate-400" />
          <h2 className="font-bold text-slate-800">No submissions on this page</h2>
          <p className="mt-1 text-sm text-slate-500">Submit marketing copy to create the first evidence-backed review.</p>
          {page > 0 ? (
            <button onClick={() => setPage((current) => Math.max(0, current - 1))} className="mt-4 text-sm font-semibold text-indigo-700 hover:text-indigo-900">Go to previous page</button>
          ) : canSubmit ? (
            <Link to="/submit" className="mt-4 inline-flex text-sm font-semibold text-indigo-700 hover:text-indigo-900">Submit copy</Link>
          ) : null}
        </div>
      ) : (
        <div className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-xs">
          <div className="hidden grid-cols-[minmax(0,1.5fr)_130px_150px_150px_36px] gap-4 border-b border-slate-100 bg-slate-50 px-5 py-3 text-[11px] font-bold uppercase tracking-[0.12em] text-slate-500 md:grid">
            <span>Submission</span><span>Type</span><span>Status</span><span>Latest verdict</span><span />
          </div>
          <div className="divide-y divide-slate-100">
            {submissions.map((submission) => (
              <Link
                key={submission.id}
                to={`/reviews/${submission.id}`}
                className="group block px-5 py-4 transition hover:bg-slate-50"
              >
                <div className="grid gap-2 md:grid-cols-[minmax(0,1.5fr)_130px_150px_150px_36px] md:items-center md:gap-4">
                  <div className="min-w-0">
                    <p className="truncate text-sm font-semibold text-slate-900 group-hover:text-indigo-700">{submission.title}</p>
                    <p className="mt-1 text-xs text-slate-500">{formatDate(submission.updated_at || submission.created_at)} · Revision {submission.latest_revision?.revision_number || '—'}</p>
                  </div>
                  <span className="text-xs font-medium capitalize text-slate-600">{readable(submission.content_type)}</span>
                  <span className="w-fit rounded-full bg-slate-100 px-2.5 py-1 text-xs font-semibold capitalize text-slate-700">{readable(submission.current_status)}</span>
                  <div>{submission.latest_revision?.overall_verdict ? <VerdictBadge verdict={submission.latest_revision.overall_verdict} /> : <span className="text-xs text-slate-400">No result yet</span>}</div>
                  <ChevronRight className="hidden h-4 w-4 text-slate-400 group-hover:text-indigo-600 md:block" />
                </div>
              </Link>
            ))}
          </div>
        </div>
      )}

      {!error && !loading && (submissions.length > 0 || page > 0) && (
        <div className="flex items-center justify-between">
          <p className="text-xs text-slate-500">Page {page + 1}</p>
          <div className="flex gap-2">
            <button
              onClick={() => setPage((current) => Math.max(0, current - 1))}
              disabled={page === 0}
              className="inline-flex items-center gap-1 rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50 disabled:cursor-not-allowed disabled:text-slate-300"
            >
              <ChevronLeft className="h-4 w-4" /> Previous
            </button>
            <button
              onClick={() => setPage((current) => current + 1)}
              disabled={!hasNextPage}
              className="inline-flex items-center gap-1 rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50 disabled:cursor-not-allowed disabled:text-slate-300"
            >
              Next <ChevronRight className="h-4 w-4" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
