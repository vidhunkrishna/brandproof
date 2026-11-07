import { useEffect, useState } from 'react';
import apiClient from '../api/client';
import { useAuth } from '../contexts/AuthContext';

export default function AnalyticsPage() {
  const { role } = useAuth();
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (role === 'admin') {
      apiClient.get('/api/v1/analytics/')
        .then((r) => setData(r.data))
        .catch((e) => setError(e.response?.data?.detail || 'Unable to load analytics.'));
    }
    return () => {};
  }, [role]);

  if (role !== 'admin') {
    return (
      <div className="rounded-xl border border-amber-200 bg-amber-50 p-6 text-sm text-amber-900">
        Governance analytics is available to organization administrators.
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-xl border border-rose-200 bg-rose-50 p-5 text-rose-900">
        {error}
      </div>
    );
  }

  if (!data) {
    return <div className="p-10 text-center text-sm text-slate-500">Loading governance analytics…</div>;
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Governance analytics</h1>
        <p className="mt-1 text-sm text-slate-500">{data.data_note}</p>
      </div>
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        {Object.entries(data.kpis).map(([k, v]) => (
          <div key={k} className="rounded-xl border bg-white p-4">
            <p className="text-xs font-bold uppercase text-slate-400">{k.replaceAll('_', ' ')}</p>
            <p className="mt-1 text-3xl font-bold">{v}</p>
          </div>
        ))}
      </div>
      <section className="rounded-xl border bg-white p-5">
        <h2 className="font-bold">Findings by verdict</h2>
        <div className="mt-3 flex flex-wrap gap-3">
          {Object.entries(data.verdicts).map(([k, v]) => (
            <span key={k} className="rounded bg-slate-100 px-3 py-2 text-sm">
              <b>{k}</b> {v}
            </span>
          )) || 'No findings in this range.'}
        </div>
      </section>
      <section className="rounded-xl border bg-white p-5">
        <h2 className="font-bold">Frequently violated guidelines</h2>
        {data.guideline_violations.length ? (
          data.guideline_violations.map((x) => (
            <p key={x.guideline_id} className="mt-2 text-sm">
              {x.title}: <b>{x.finding_count}</b> findings
            </p>
          ))
        ) : (
          <p className="mt-2 text-sm text-slate-500">No linked guideline findings.</p>
        )}
      </section>
      <section className="rounded-xl border bg-white p-5">
        <h2 className="font-bold">Dispute summary</h2>
        <p className="mt-2 text-sm">
          {data.disputes.total} total · {data.disputes.open} open · {data.disputes.overrides} overrides
        </p>
      </section>
    </div>
  );
}
