import { useState, useEffect } from 'react';
import apiClient from './api/client';
import { 
  ShieldCheck, 
  CheckCircle2, 
  AlertTriangle, 
  Cpu, 
  Database, 
  Layers, 
  RefreshCw 
} from 'lucide-react';

export default function App() {
  const [health, setHealth] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchHealth = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await apiClient.get('/health');
      setHealth(response.data);
    } catch (err) {
      setError(err.message || 'Unable to connect to BrandProof backend API');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHealth();
  }, []);

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 flex flex-col font-sans">
      {/* Top Navigation */}
      <header className="border-b border-slate-200 bg-white sticky top-0 z-50 shadow-sm">
        <div className="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="bg-indigo-600 text-white p-2 rounded-lg flex items-center justify-center shadow-sm">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <div>
              <span className="font-bold text-lg tracking-tight text-slate-900">BrandProof</span>
              <span className="ml-2 text-xs font-medium px-2 py-0.5 bg-indigo-50 text-indigo-700 rounded-full border border-indigo-100">
                Phase 2 Scaffolding
              </span>
            </div>
          </div>
          <div className="flex items-center gap-4 text-sm text-slate-500">
            <span className="inline-flex items-center gap-1.5 text-xs font-medium text-emerald-700 bg-emerald-50 px-2.5 py-1 rounded-full border border-emerald-200">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
              React + Tailwind v4 Active
            </span>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <main className="flex-1 max-w-6xl mx-auto px-6 py-12 w-full space-y-10">
        <div className="text-center max-w-3xl mx-auto space-y-4">
          <div className="inline-block px-3 py-1 text-xs font-semibold uppercase tracking-wider text-indigo-700 bg-indigo-50 border border-indigo-100 rounded-full">
            CodeNexus India 2026 Hackathon
          </div>
          <h1 className="text-4xl md:text-5xl font-extrabold text-slate-900 tracking-tight">
            Evidence Before Approval.
          </h1>
          <p className="text-lg text-slate-600 leading-relaxed">
            AI-assisted brand governance platform verifying marketing copy against 
            approved guidelines, factual bounds, and terminology before publication.
          </p>
        </div>

        {/* Live Backend Connection Status Card */}
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6 max-w-2xl mx-auto">
          <div className="flex items-center justify-between pb-4 border-b border-slate-100">
            <div className="flex items-center gap-2">
              <Database className="w-5 h-5 text-indigo-600" />
              <h2 className="font-semibold text-slate-900">Backend Connectivity Check</h2>
            </div>
            <button
              onClick={fetchHealth}
              disabled={loading}
              className="inline-flex items-center gap-1.5 text-xs font-medium text-slate-600 hover:text-slate-900 px-2.5 py-1.5 rounded border border-slate-200 hover:bg-slate-50 transition"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
              Refresh
            </button>
          </div>

          <div className="pt-4">
            {loading && (
              <div className="text-sm text-slate-500 flex items-center gap-2">
                <RefreshCw className="w-4 h-4 animate-spin text-indigo-600" />
                Connecting to http://localhost:8000/health...
              </div>
            )}

            {!loading && error && (
              <div className="p-4 rounded-lg bg-amber-50 border border-amber-200 text-amber-800 space-y-1">
                <div className="flex items-center gap-2 font-medium">
                  <AlertTriangle className="w-4 h-4 text-amber-600" />
                  API Offline or Initializing
                </div>
                <p className="text-xs text-amber-700">{error}</p>
                <p className="text-xs text-amber-600 mt-2">
                  Start the backend server with: <code>uvicorn app.main:app --reload</code>
                </p>
              </div>
            )}

            {!loading && health && (
              <div className="space-y-3">
                <div className="flex items-center justify-between p-3 rounded-lg bg-emerald-50 border border-emerald-100">
                  <div className="flex items-center gap-2 text-emerald-800 font-medium text-sm">
                    <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                    FastAPI Health: {health.status.toUpperCase()}
                  </div>
                  <span className="text-xs bg-emerald-200/60 text-emerald-800 font-mono px-2 py-0.5 rounded">
                    v{health.version}
                  </span>
                </div>

                <div className="grid grid-cols-2 gap-3 text-xs">
                  <div className="p-3 rounded-lg bg-slate-50 border border-slate-200">
                    <span className="text-slate-500 block mb-1">Database Engine</span>
                    <span className="font-semibold text-slate-800">
                      {health.database?.database || 'PostgreSQL'}
                    </span>
                  </div>
                  <div className="p-3 rounded-lg bg-slate-50 border border-slate-200">
                    <span className="text-slate-500 block mb-1">DB Connection</span>
                    <span className={`font-semibold ${health.database?.status === 'connected' ? 'text-emerald-600' : 'text-amber-600'}`}>
                      {health.database?.status || 'Unknown'}
                    </span>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Three-Lane Review Architecture Showcase */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 pt-4">
          <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-3">
            <div className="w-9 h-9 rounded-lg bg-blue-50 text-blue-700 flex items-center justify-center font-bold text-sm">
              L1
            </div>
            <h3 className="font-semibold text-slate-900">Lane 1: Deterministic</h3>
            <p className="text-xs text-slate-600 leading-relaxed">
              Sub-millisecond regex & token evaluation of mandatory qualifiers, forbidden phrasing, and exact terminology.
            </p>
          </div>

          <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-3">
            <div className="w-9 h-9 rounded-lg bg-emerald-50 text-emerald-700 flex items-center justify-center font-bold text-sm">
              L2
            </div>
            <h3 className="font-semibold text-slate-900">Lane 2: Grounded Facts</h3>
            <p className="text-xs text-slate-600 leading-relaxed">
              Direct verification against PostgreSQL approved facts with temporal validity windows, scope matching, and versioning.
            </p>
          </div>

          <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-3">
            <div className="w-9 h-9 rounded-lg bg-purple-50 text-purple-700 flex items-center justify-center font-bold text-sm">
              L3
            </div>
            <h3 className="font-semibold text-slate-900">Lane 3: Advisory AI</h3>
            <p className="text-xs text-slate-600 leading-relaxed">
              Contextual claim extraction and suggested wording via external LLM with strict deterministic fallback on failure.
            </p>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-200 py-6 bg-white text-center text-xs text-slate-500">
        BrandProof &copy; 2026 &bull; CodeNexus India 2026 Hackathon &bull; Modular Monolith Architecture
      </footer>
    </div>
  );
}
