import { useEffect, useState } from 'react';
import apiClient from '../api/client';
import { useAuth } from '../contexts/AuthContext';
import { Sparkles, CheckCircle2, AlertTriangle } from 'lucide-react';

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

  const generateSampleImage = (type) => {
    setError(null);
    const canvas = document.createElement('canvas');
    canvas.width = 1200;
    canvas.height = 630;
    const ctx = canvas.getContext('2d');

    if (type === 'compliant') {
      ctx.fillStyle = '#4F46E5';
      ctx.fillRect(0, 0, 1200, 630);

      ctx.strokeStyle = '#6366F1';
      ctx.lineWidth = 16;
      ctx.strokeRect(8, 8, 1184, 614);

      ctx.fillStyle = '#FFFFFF';
      ctx.font = 'bold 56px Inter, sans-serif';
      ctx.textAlign = 'center';
      ctx.fillText('Lumen Smart Lighting', 600, 260);

      ctx.fillStyle = '#E0E7FF';
      ctx.font = '32px Inter, sans-serif';
      ctx.fillText('Intelligent illumination with verified 60% energy savings.', 600, 340);

      ctx.fillStyle = '#C7D2FE';
      ctx.font = '22px Inter, sans-serif';
      ctx.fillText('Official Brand Assets · High Contrast AA Compliant', 600, 420);

      canvas.toBlob((blob) => {
        if (blob) {
          setFile(new File([blob], 'lumen_compliant_banner.png', { type: 'image/png' }));
        }
      }, 'image/png');
    } else {
      ctx.fillStyle = '#F3F4F6';
      ctx.fillRect(0, 0, 1200, 630);

      ctx.fillStyle = '#FACC15';
      ctx.font = 'bold 56px Inter, sans-serif';
      ctx.textAlign = 'center';
      ctx.fillText('Low Contrast Warning Sample', 600, 290);

      ctx.fillStyle = '#FEF08A';
      ctx.font = '30px Inter, sans-serif';
      ctx.fillText('Yellow text on light gray background fails WCAG 4.5:1 ratio.', 600, 360);

      canvas.toBlob((blob) => {
        if (blob) {
          setFile(new File([blob], 'lumen_low_contrast_test.png', { type: 'image/png' }));
        }
      }, 'image/png');
    }
  };

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

      {/* 1-Click Demo Image Helper */}
      <div className="bg-indigo-50/70 border border-indigo-200/80 rounded-xl p-4 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 shadow-xs">
        <div className="flex items-start gap-3">
          <div className="p-2 rounded-lg bg-indigo-600 text-white shrink-0">
            <Sparkles className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-slate-900">Try Sample Marketing Banners</h3>
            <p className="text-xs text-slate-600 mt-0.5">
              Test visual compliance instantly without uploading files from your computer.
            </p>
          </div>
        </div>
        <div className="flex flex-wrap items-center gap-2 self-end sm:self-auto shrink-0">
          <button
            type="button"
            onClick={() => generateSampleImage('compliant')}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold shadow-xs transition cursor-pointer"
          >
            <CheckCircle2 className="w-3.5 h-3.5" />
            Load Compliant Banner
          </button>
          <button
            type="button"
            onClick={() => generateSampleImage('low-contrast')}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-amber-600 hover:bg-amber-700 text-white text-xs font-semibold shadow-xs transition cursor-pointer"
          >
            <AlertTriangle className="w-3.5 h-3.5" />
            Load Contrast Warning
          </button>
        </div>
      </div>

      {(role === 'admin' || role === 'creator') && (
        <form onSubmit={submit} className="rounded-xl border bg-white p-5 space-y-3">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <label className="block text-sm font-semibold text-slate-900">Marketing image (PNG, JPEG, or WebP; maximum 10 MB)</label>
            {file && (
              <span className="text-xs font-bold text-indigo-600 bg-indigo-50 px-2.5 py-1 rounded-md border border-indigo-200">
                Staged: {file.name} ({(file.size / 1024).toFixed(1)} KB)
              </span>
            )}
          </div>
          <input
            type="file"
            accept="image/png,image/jpeg,image/webp"
            onChange={(e) => setFile(e.target.files?.[0] || null)}
            className="block text-sm text-slate-600 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-xs file:font-semibold file:bg-indigo-50 file:text-indigo-700 hover:file:bg-indigo-100 cursor-pointer"
          />
          <button
            disabled={!file || busy}
            className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-semibold text-white disabled:bg-slate-400 cursor-pointer disabled:cursor-not-allowed transition"
          >
            {busy ? 'Reviewing…' : 'Review asset'}
          </button>
        </form>
      )}

      <section>
        <h2 className="mb-3 font-bold text-slate-900">Recent visual reviews</h2>
        {items.length ? (
          items.map((item) => (
            <article key={item.id} className="mb-3 rounded-xl border bg-white p-4 shadow-xs">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <b className="text-slate-900">{item.filename}</b>
                <span className="text-xs text-slate-500 font-medium">{item.width} × {item.height} · {item.detected_format}</span>
              </div>
              <div className="mt-3 space-y-2">
                {item.findings_json.map((f, i) => (
                  <div key={i} className="rounded-lg bg-slate-50 border border-slate-200/60 p-3 text-sm">
                    <span className="font-semibold capitalize text-slate-800">{f.type?.replaceAll('_', ' ')}</span>:{' '}
                    <span className="text-slate-600">{f.issue || f.message}</span>
                    {f.measured !== undefined && (
                      <p className="mt-1 text-xs text-slate-500">
                        Measured: {typeof f.measured === 'object' ? JSON.stringify(f.measured) : String(f.measured)}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            </article>
          ))
        ) : (
          <p className="text-sm text-slate-500">No visual assets have been reviewed.</p>
        )}
      </section>
    </div>
  );
}
