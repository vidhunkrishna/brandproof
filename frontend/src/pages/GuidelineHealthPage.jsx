import { useCallback, useEffect, useState } from 'react';
import { AlertCircle, CheckCircle2, LoaderCircle } from 'lucide-react';
import apiClient from '../api/client';
import { useAuth } from '../contexts/AuthContext';

export default function GuidelineHealthPage() {
  const { role } = useAuth();
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const load = useCallback(async () => {
    try {
      setError(null);
      setData((await apiClient.get('/api/v1/guideline-health/')).data);
    } catch (e) {
      setError(e.response?.data?.detail || 'Unable to load guideline health.');
    }
  }, []);

  useEffect(() => {
    if (role === 'admin') {
      load();
    }
    return () => {};
  }, [role, load]);
  if (role !== 'admin') return <div className="rounded-xl border border-amber-200 bg-amber-50 p-6 text-sm text-amber-900">Guideline Health is available to organization administrators.</div>;
  if (!data && !error) return <div className="p-10 text-center text-sm text-slate-500"><LoaderCircle className="mx-auto mb-2 h-6 w-6 animate-spin" />Loading guideline health…</div>;
  if (error) return <div role="alert" className="rounded-xl border border-rose-200 bg-rose-50 p-5 text-rose-900"><AlertCircle className="mr-2 inline h-4 w-4" />{error}</div>;
  return <div className="space-y-6"><div><h1 className="text-2xl font-bold text-slate-900">Guideline Health</h1><p className="mt-1 text-sm text-slate-500">Warnings use persisted findings, disputes, and explicit phrase configuration. Nothing is changed automatically.</p></div><div className="grid gap-3 sm:grid-cols-2"><div className="rounded-xl border border-slate-200 bg-white p-4"><p className="text-xs font-bold uppercase text-slate-400">Active guidelines</p><p className="mt-1 text-3xl font-bold text-slate-900">{data.active_guideline_count}</p></div><div className="rounded-xl border border-slate-200 bg-white p-4"><p className="text-xs font-bold uppercase text-slate-400">Warnings</p><p className="mt-1 text-3xl font-bold text-amber-700">{data.warnings.length}</p></div></div>{data.warnings.length === 0 ? <div className="rounded-xl border border-dashed border-slate-300 p-10 text-center text-sm text-slate-600"><CheckCircle2 className="mx-auto mb-2 h-6 w-6 text-emerald-600" />No health warnings were derived from the current persisted data.</div> : <div className="space-y-3">{data.warnings.map((warning, i) => <article key={`${warning.type}-${warning.guideline_id}-${i}`} className="rounded-xl border border-amber-200 bg-white p-5"><p className="text-xs font-bold uppercase text-amber-700">{warning.type.replaceAll('_', ' ')}</p><h2 className="mt-1 font-bold text-slate-900">{warning.guideline_title}</h2><p className="mt-2 text-sm text-slate-700">{warning.reason}</p><p className="mt-2 text-sm font-semibold text-indigo-800">Recommended action: {warning.recommendation}</p><pre className="mt-3 overflow-auto rounded bg-slate-50 p-2 text-xs text-slate-600">{JSON.stringify(warning.evidence, null, 2)}</pre></article>)}</div>}</div>;
}
