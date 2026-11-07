import { useEffect, useState } from 'react';
import apiClient from '../api/client';
import { useAuth } from '../contexts/AuthContext';

export default function FactWatchPage() {
  const { role } = useAuth();
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (role === 'admin') {
      apiClient.get('/api/v1/factwatch/')
        .then((r) => setData(r.data))
        .catch((e) => setError(e.response?.data?.detail || 'Unable to load FactWatch.'));
    }
    return () => {};
  }, [role]);

  if (role !== 'admin') {
    return (
      <div className="rounded-xl border border-amber-200 bg-amber-50 p-6 text-sm text-amber-900">
        FactWatch is available to organization administrators.
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
    return <div className="p-10 text-center text-sm text-slate-500">Loading FactWatch…</div>;
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">FactWatch</h1>
        <p className="mt-1 text-sm text-slate-500">
          Lifecycle warnings are derived from approved fact versions and linked findings.
        </p>
      </div>
      <div className="grid gap-3 sm:grid-cols-3">
        {[['Expiring', data.expiring], ['Expired', data.expired], ['Superseded', data.superseded]].map(([name, items]) => (
          <div key={name} className="rounded-xl border bg-white p-4">
            <p className="text-xs font-bold uppercase text-slate-400">{name}</p>
            <p className="mt-1 text-3xl font-bold">{items.length}</p>
          </div>
        ))}
      </div>
      {['expiring', 'expired', 'superseded', 'pending_review'].map((key) => (
        <section key={key}>
          <h2 className="mb-2 font-bold capitalize text-slate-900">{key.replace('_', ' ')}</h2>
          {data[key].length ? (
            <div className="space-y-2">
              {data[key].map((f) => (
                <div key={f.id} className="rounded-lg border bg-white p-3 text-sm">
                  <b>{f.fact_name} · v{f.version}</b>
                  <p className="text-slate-600">{f.approved_value} · {f.affected_findings} linked findings · review: {f.review_status}</p>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-slate-500">No records.</p>
          )}
        </section>
      ))}
    </div>
  );
}
