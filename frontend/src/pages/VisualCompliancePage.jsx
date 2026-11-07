import { useEffect, useState } from 'react';
import apiClient from '../api/client';
import { useAuth } from '../contexts/AuthContext';

export default function VisualCompliancePage() {
  const { role } = useAuth();
  const [file, setFile] = useState(null);
  const [items, setItems] = useState([]);
  const [error, setError] = useState(null);
  const [busy, setBusy] = useState(false);

  const load = () => {
    void apiClient.get('/api/v1/visual/reviews')
      .then((r) => setItems(r.data))
      .catch((e) => setError(e.response?.data?.detail || 'Unable to load visual reviews.'));
  };

  useEffect(() => {
    load();
    return () => {};
  }, []);

  const submit = async (e) => {
    e.preventDefault();
    if (!file) return;
    setBusy(true);
    setError(null);
    try {
      const f = new FormData();
      f.append('file', file);
      await apiClient.post('/api/v1/visual/reviews', f);
      setFile(null);
      load();
    } catch (e) {
      setError(e.response?.data?.detail || 'Unable to review asset.');
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Visual brand compliance</h1>
        <p className="mt-1 text-sm text-slate-500">
          Deterministic color samples, contrast, dimensions, format, and configured logo aspect-ratio checks. Typography and logo identity require manual review unless reliable metadata is available.
        </p>
      </div>
      {error && (
        <div role="alert" className="rounded-lg border border-rose-200 bg-rose-50 p-3 text-sm text-rose-900">
          {error}
        </div>
      )}
      {(role === 'admin' || role === 'creator') && (
        <form onSubmit={submit} className="rounded-xl border bg-white p-5">
          <label className="block text-sm font-semibold">Marketing image (PNG, JPEG, or WebP; maximum 10 MB)</label>
          <input
            type="file"
            accept="image/png,image/jpeg,image/webp"
            onChange={(e) => setFile(e.target.files?.[0] || null)}
            className="mt-3 block text-sm"
          />
          <button
            disabled={!file || busy}
            className="mt-3 rounded-lg bg-indigo-600 px-4 py-2 text-sm font-semibold text-white disabled:bg-slate-400"
          >
            {busy ? 'Reviewing…' : 'Review asset'}
          </button>
        </form>
      )}
      <section>
        <h2 className="mb-3 font-bold text-slate-900">Recent visual reviews</h2>
        {items.length ? (
          items.map((item) => (
            <article key={item.id} className="mb-3 rounded-xl border bg-white p-4">
              <b>{item.filename}</b>
              <p className="text-sm text-slate-600">{item.width} × {item.height} · {item.detected_format}</p>
              {item.findings_json.map((f, i) => (
                <div key={i} className="mt-3 rounded bg-slate-50 p-3 text-sm">
                  <b>{f.type.replaceAll('_', ' ')}</b>: {f.issue}
                  <p className="mt-1 text-slate-600">Measured: {typeof f.measured === 'object' ? JSON.stringify(f.measured) : String(f.measured)}</p>
                </div>
              ))}
            </article>
          ))
        ) : (
          <p className="text-sm text-slate-500">No visual assets have been reviewed.</p>
        )}
      </section>
    </div>
  );
}
