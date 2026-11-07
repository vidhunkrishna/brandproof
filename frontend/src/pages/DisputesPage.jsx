import { useCallback, useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { AlertCircle, CheckCircle2, ClipboardList, LoaderCircle } from 'lucide-react';
import apiClient from '../api/client';
import { useAuth } from '../contexts/AuthContext';
import { VerdictBadge } from '../components/reviews/ReviewPrimitives';

const errorMessage = (error, fallback) => error.response?.data?.detail || error.message || fallback;

export default function DisputesPage() {
  const { disputeId } = useParams();
  const { role } = useAuth();
  const [disputes, setDisputes] = useState([]);
  const [detail, setDetail] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [action, setAction] = useState('uphold');
  const [reason, setReason] = useState('');
  const [overrideVerdict, setOverrideVerdict] = useState('UNVERIFIABLE');
  const [saving, setSaving] = useState(false);

  const load = useCallback(async () => {
    setLoading(true); setError(null);
    try {
      if (disputeId) setDetail((await apiClient.get(`/api/v1/disputes/${disputeId}`)).data);
      else setDisputes((await apiClient.get(`/api/v1/disputes/?queue_only=${role !== 'creator'}`)).data);
    } catch (requestError) { setError(errorMessage(requestError, 'Unable to load disputes.')); }
    finally { setLoading(false); }
  }, [disputeId, role]);
  useEffect(() => {
    load();
    return () => {};
  }, [load]);

  const resolve = async (event) => {
    event.preventDefault(); setSaving(true); setError(null);
    try {
      const payload = { action, reason };
      if (action === 'override') payload.override_verdict = overrideVerdict;
      setDetail((await apiClient.post(`/api/v1/disputes/${detail.id}/resolve`, payload)).data);
      setReason('');
    } catch (requestError) { setError(errorMessage(requestError, 'Unable to save the review decision.')); }
    finally { setSaving(false); }
  };

  if (loading) return <div className="p-10 text-center text-sm text-slate-500"><LoaderCircle className="mx-auto mb-2 h-6 w-6 animate-spin" />Loading disputes…</div>;
  if (error && !detail && !disputes.length) return <div role="alert" className="rounded-xl border border-rose-200 bg-rose-50 p-5 text-rose-900">{error}</div>;

  if (!disputeId) return <div className="space-y-6">
    <div><h1 className="text-2xl font-bold text-slate-900">{role === 'creator' ? 'My disputes' : 'Human review queue'}</h1><p className="mt-1 text-sm text-slate-500">{role === 'creator' ? 'Track the findings you have asked a reviewer to reconsider.' : 'Resolve open organization disputes with a documented decision.'}</p></div>
    {disputes.length === 0 ? <div className="rounded-xl border border-dashed border-slate-300 p-10 text-center text-sm text-slate-500"><CheckCircle2 className="mx-auto mb-2 h-6 w-6 text-emerald-600" />No disputes match this view.</div> : <div className="space-y-3">{disputes.map((item) => <Link key={item.id} to={`/disputes/${item.id}`} className="block rounded-xl border border-slate-200 bg-white p-4 transition hover:border-indigo-300"><div className="flex flex-wrap justify-between gap-3"><div><p className="font-semibold text-slate-900">“{item.finding.claim_text}”</p><p className="mt-1 text-sm text-slate-600">{item.reason}</p></div><div className="flex gap-2"><VerdictBadge verdict={item.finding.verdict} /><span className="rounded-full bg-slate-100 px-2 py-1 text-xs font-semibold capitalize text-slate-700">{item.status.replace('_', ' ')}</span></div></div><p className="mt-3 text-xs text-slate-400">Revision {item.revision_number} · raised by {item.raised_by_name || 'Unknown user'}</p></Link>)}</div>}
  </div>;

  if (!detail) return null;
  const canResolve = role === 'admin' || role === 'reviewer';
  const active = detail.status === 'open' || detail.status === 'needs_info';
  return <div className="mx-auto max-w-3xl space-y-6"><Link to="/disputes" className="text-sm font-semibold text-indigo-700">← Back to disputes</Link><div><h1 className="text-2xl font-bold text-slate-900">Dispute review</h1><p className="mt-1 text-sm text-slate-500">Submission revision {detail.revision_number} · <Link className="font-semibold text-indigo-700" to={`/reviews/${detail.submission_id}?revision=${detail.revision_id}`}>Open original evidence</Link></p></div>{error && <div role="alert" className="rounded-lg border border-rose-200 bg-rose-50 p-3 text-sm text-rose-900"><AlertCircle className="mr-2 inline h-4 w-4" />{error}</div>}<section className="rounded-xl border border-slate-200 bg-white p-5"><div className="flex flex-wrap justify-between gap-3"><h2 className="font-bold text-slate-900">Original finding</h2><VerdictBadge verdict={detail.finding.verdict} /></div><p className="mt-3 font-semibold text-slate-800">“{detail.finding.claim_text}”</p><p className="mt-2 text-sm leading-6 text-slate-600">{detail.finding.explanation}</p><div className="mt-4 border-t pt-4"><p className="text-xs font-bold uppercase text-slate-400">Creator explanation</p><p className="mt-1 text-sm text-slate-700">{detail.reason}</p></div></section>{detail.resolution_note && <section className="rounded-xl border border-slate-200 bg-slate-50 p-5"><p className="font-bold text-slate-900">Latest review decision</p><p className="mt-2 text-sm text-slate-700">{detail.resolution_note}</p><p className="mt-2 text-xs text-slate-500">{detail.resolved_by_name ? `Reviewed by ${detail.resolved_by_name}` : 'Awaiting additional information'}{detail.override_verdict ? ` · Override: ${detail.override_verdict}` : ''}</p></section>}{canResolve && active && <form onSubmit={resolve} className="space-y-4 rounded-xl border border-indigo-200 bg-indigo-50 p-5"><h2 className="font-bold text-indigo-950">Reviewer decision</h2><select value={action} onChange={(event) => setAction(event.target.value)} className="w-full rounded-lg border border-slate-300 p-2 text-sm"><option value="uphold">Uphold original finding</option><option value="override">Override finding</option><option value="request_info">Request additional information</option></select>{action === 'override' && <select value={overrideVerdict} onChange={(event) => setOverrideVerdict(event.target.value)} className="w-full rounded-lg border border-slate-300 p-2 text-sm">{['CORRECT','CONTRADICTED','OUTDATED','UNSUPPORTED','UNVERIFIABLE'].map((item) => <option key={item}>{item}</option>)}</select>}<textarea required minLength={10} maxLength={4000} value={reason} onChange={(event) => setReason(event.target.value)} placeholder="Document the evidence-based decision…" className="min-h-28 w-full rounded-lg border border-slate-300 p-3 text-sm" /><button disabled={saving} className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-semibold text-white disabled:bg-slate-400">{saving ? 'Saving…' : 'Save decision'}</button></form>}</div>;
}
