import React, { useState, useEffect } from 'react';
import apiClient from '../api/client';
import { useAuth } from '../contexts/AuthContext';
import { 
  Plus, 
  Search, 
  CheckCircle2, 
  Clock, 
  History, 
  Archive, 
  RefreshCw, 
  ArrowRight,
  ShieldCheck,
  X 
} from 'lucide-react';

export default function FactsPage() {
  const { role } = useAuth();
  const [facts, setFacts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [categoryFilter, setCategoryFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [searchQuery, setSearchQuery] = useState('');

  // Modals State
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showSupersedeModal, setShowSupersedeModal] = useState(false);
  const [targetFact, setTargetFact] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [formError, setFormError] = useState(null);

  // Form State
  const [formData, setFormData] = useState({
    fact_name: '',
    approved_value: '',
    numeric_value: '',
    numeric_operator: '<=',
    unit: '%',
    category: 'performance',
    scope: 'laboratory tests',
    source: 'Certified Lab Report 2026',
    required_qualifiers: '',
  });

  const [supersedeData, setSupersedeData] = useState({
    approved_value: '',
    numeric_value: '',
    numeric_operator: '<=',
    unit: '%',
    source: '',
    scope: '',
    required_qualifiers: '',
  });

  const fetchFacts = async () => {
    setLoading(true);
    setError(null);
    try {
      const params = {};
      if (categoryFilter) params.category = categoryFilter;
      if (statusFilter) params.status = statusFilter;
      if (searchQuery) params.search = searchQuery;

      const res = await apiClient.get('/api/v1/facts/', { params });
      setFacts(res.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to fetch approved facts');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchFacts();
    return () => {};
  }, [categoryFilter, statusFilter]);

  const handleSearch = (e) => {
    e.preventDefault();
    fetchFacts();
  };

  const handleApprove = async (id) => {
    try {
      await apiClient.put(`/api/v1/facts/${id}/approve`);
      fetchFacts();
    } catch (err) {
      alert(err.response?.data?.detail || 'Approval failed');
    }
  };

  const handleArchive = async (id) => {
    if (!confirm('Are you sure you want to archive this approved fact?')) return;
    try {
      await apiClient.delete(`/api/v1/facts/${id}`);
      fetchFacts();
    } catch (err) {
      alert(err.response?.data?.detail || 'Archive failed');
    }
  };

  const handleCreateSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    setFormError(null);
    try {
      const payload = {
        ...formData,
        numeric_value: formData.numeric_value ? parseFloat(formData.numeric_value) : null,
        required_qualifiers: formData.required_qualifiers
          ? formData.required_qualifiers.split(',').map((s) => s.trim()).filter(Boolean)
          : [],
      };

      await apiClient.post('/api/v1/facts/', payload);
      setShowCreateModal(false);
      fetchFacts();
    } catch (err) {
      setFormError(err.response?.data?.detail || 'Failed to create fact');
    } finally {
      setSubmitting(false);
    }
  };

  const openSupersede = (fact) => {
    setTargetFact(fact);
    setSupersedeData({
      approved_value: fact.approved_value,
      numeric_value: fact.numeric_value || '',
      numeric_operator: fact.numeric_operator || '<=',
      unit: fact.unit || '',
      source: `Updated: ${fact.source || 'Policy Update'}`,
      scope: fact.scope || 'global',
      required_qualifiers: fact.required_qualifiers ? fact.required_qualifiers.join(', ') : '',
    });
    setShowSupersedeModal(true);
  };

  const handleSupersedeSubmit = async (e) => {
    e.preventDefault();
    if (!targetFact) return;
    setSubmitting(true);
    setFormError(null);
    try {
      const payload = {
        approved_value: supersedeData.approved_value,
        numeric_value: supersedeData.numeric_value ? parseFloat(supersedeData.numeric_value) : null,
        numeric_operator: supersedeData.numeric_operator || null,
        unit: supersedeData.unit || null,
        source: supersedeData.source,
        scope: supersedeData.scope,
        required_qualifiers: supersedeData.required_qualifiers
          ? supersedeData.required_qualifiers.split(',').map((s) => s.trim()).filter(Boolean)
          : [],
      };

      await apiClient.post(`/api/v1/facts/${targetFact.id}/supersede`, payload);
      setShowSupersedeModal(false);
      fetchFacts();
    } catch (err) {
      setFormError(err.response?.data?.detail || 'Failed to supersede fact');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Approved Brand Facts</h1>
          <p className="text-sm text-slate-500 mt-1">
            Grounded factual specifications, numeric limits, scopes, and validity periods for review comparison.
          </p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="inline-flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-sm font-medium transition shadow-xs cursor-pointer self-start sm:self-auto"
        >
          <Plus className="w-4 h-4" />
          Add Fact
        </button>
      </div>

      {/* Filter Bar */}
      <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs flex flex-wrap items-center justify-between gap-4">
        <form onSubmit={handleSearch} className="flex items-center gap-2 flex-1 min-w-[240px]">
          <div className="relative flex-1">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search fact name or approved value..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-9 pr-3 py-1.5 text-sm bg-slate-50 border border-slate-200 rounded-lg focus:outline-none focus:border-indigo-500"
            />
          </div>
          <button
            type="submit"
            className="px-3 py-1.5 text-xs font-medium text-slate-700 bg-slate-100 hover:bg-slate-200 rounded-lg transition"
          >
            Search
          </button>
        </form>

        <div className="flex items-center gap-2">
          <select
            value={categoryFilter}
            onChange={(e) => setCategoryFilter(e.target.value)}
            className="text-xs font-medium text-slate-700 bg-slate-50 border border-slate-200 rounded-lg px-2.5 py-1.5 focus:outline-none"
          >
            <option value="">All Categories</option>
            <option value="performance">Performance</option>
            <option value="warranty">Warranty</option>
            <option value="sustainability">Sustainability</option>
            <option value="security">Security</option>
          </select>

          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="text-xs font-medium text-slate-700 bg-slate-50 border border-slate-200 rounded-lg px-2.5 py-1.5 focus:outline-none"
          >
            <option value="">All Statuses</option>
            <option value="approved">Approved</option>
            <option value="pending_approval">Pending Approval</option>
            <option value="superseded">Superseded (Historical)</option>
            <option value="archived">Archived</option>
          </select>

          <button
            onClick={fetchFacts}
            disabled={loading}
            className="p-1.5 text-slate-500 hover:text-slate-800 rounded-lg border border-slate-200 hover:bg-slate-50"
            title="Refresh list"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Facts List */}
      {loading ? (
        <div className="bg-white rounded-xl border border-slate-200 p-12 text-center text-slate-400">
          <RefreshCw className="w-6 h-6 animate-spin mx-auto mb-2 text-indigo-600" />
          Loading approved brand facts...
        </div>
      ) : error ? (
        <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-sm">
          {error}
        </div>
      ) : facts.length === 0 ? (
        <div className="bg-white rounded-xl border border-dashed border-slate-300 p-12 text-center">
          <p className="text-slate-600 font-medium">No approved facts found matching your criteria.</p>
          <p className="text-xs text-slate-400 mt-1">Add approved brand facts above.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {facts.map((fact) => (
            <div
              key={fact.id}
              className={`bg-white rounded-xl border p-5 shadow-xs transition flex flex-col justify-between ${
                fact.status === 'superseded'
                  ? 'border-slate-200 opacity-70 bg-slate-50/50'
                  : 'border-slate-200 hover:border-slate-300'
              }`}
            >
              <div className="space-y-3">
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <h3 className="font-semibold text-slate-900 leading-snug">{fact.fact_name}</h3>
                    <div className="flex items-center gap-2 mt-1">
                      <span className="text-[11px] font-semibold tracking-wider uppercase px-2 py-0.5 rounded bg-slate-100 text-slate-600">
                        {fact.category}
                      </span>
                      <span className="text-xs text-slate-400 font-mono">v{fact.version}</span>
                    </div>
                  </div>

                  {/* Status Badge */}
                  {fact.status === 'approved' ? (
                    <span className="inline-flex items-center gap-1 text-xs font-medium text-emerald-700 bg-emerald-50 px-2.5 py-0.5 rounded-full border border-emerald-200">
                      <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                      Approved
                    </span>
                  ) : fact.status === 'pending_approval' ? (
                    <span className="inline-flex items-center gap-1 text-xs font-medium text-amber-700 bg-amber-50 px-2.5 py-0.5 rounded-full border border-amber-200">
                      <Clock className="w-3.5 h-3.5 text-amber-600" />
                      Pending Approval
                    </span>
                  ) : fact.status === 'superseded' ? (
                    <span className="inline-flex items-center gap-1 text-xs font-medium text-indigo-700 bg-indigo-50 px-2.5 py-0.5 rounded-full border border-indigo-200">
                      <History className="w-3.5 h-3.5" />
                      Superseded
                    </span>
                  ) : (
                    <span className="inline-flex items-center gap-1 text-xs font-medium text-slate-600 bg-slate-100 px-2.5 py-0.5 rounded-full">
                      <Archive className="w-3.5 h-3.5" />
                      Archived
                    </span>
                  )}
                </div>

                {/* Approved Value Box */}
                <div className="bg-indigo-50/50 border border-indigo-100 p-3 rounded-lg">
                  <span className="text-[10px] uppercase font-bold tracking-wider text-indigo-700 block mb-0.5">
                    Approved Claim
                  </span>
                  <p className="text-base font-semibold text-slate-900">{fact.approved_value}</p>
                </div>

                {/* Technical Bounds & Scope */}
                <div className="grid grid-cols-2 gap-2 text-xs">
                  <div className="p-2 bg-slate-50 rounded border border-slate-100">
                    <span className="text-slate-400 block text-[10px] uppercase">Numeric Bound</span>
                    <span className="font-mono font-medium text-slate-800">
                      {fact.numeric_value !== null ? `${fact.numeric_operator || '=='} ${fact.numeric_value} ${fact.unit || ''}` : 'Non-numeric'}
                    </span>
                  </div>
                  <div className="p-2 bg-slate-50 rounded border border-slate-100">
                    <span className="text-slate-400 block text-[10px] uppercase">Scope</span>
                    <span className="font-medium text-slate-800 capitalize truncate block">
                      {fact.scope || 'global'}
                    </span>
                  </div>
                </div>

                {/* Required Qualifiers */}
                {fact.required_qualifiers && fact.required_qualifiers.length > 0 && (
                  <div className="text-xs flex items-start gap-1.5">
                    <span className="text-indigo-700 font-semibold shrink-0">Mandatory Qualifier:</span>
                    <div className="flex flex-wrap gap-1">
                      {fact.required_qualifiers.map((q, idx) => (
                        <span key={idx} className="bg-indigo-50 text-indigo-800 border border-indigo-100 px-1.5 py-0.5 rounded text-[11px]">
                          "{q}"
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              {/* Card Footer & Actions */}
              <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-xs text-slate-400">
                <span className="truncate max-w-[200px]" title={fact.source}>
                  Source: {fact.source || 'Manual'}
                </span>

                <div className="flex items-center gap-2">
                  {fact.status === 'pending_approval' && role === 'admin' && (
                    <button
                      onClick={() => handleApprove(fact.id)}
                      className="px-2.5 py-1 bg-emerald-600 hover:bg-emerald-700 text-white rounded text-xs font-medium transition cursor-pointer"
                    >
                      Approve
                    </button>
                  )}
                  {fact.status === 'approved' && role === 'admin' && (
                    <button
                      onClick={() => openSupersede(fact)}
                      className="px-2.5 py-1 bg-slate-100 hover:bg-indigo-50 text-slate-700 hover:text-indigo-700 border border-slate-200 rounded text-xs font-medium transition cursor-pointer"
                    >
                      Supersede (v{fact.version + 1})
                    </button>
                  )}
                  {fact.status === 'approved' && role === 'admin' && (
                    <button
                      onClick={() => handleArchive(fact.id)}
                      className="px-2 py-1 text-slate-400 hover:text-rose-600 rounded hover:bg-slate-100 transition cursor-pointer"
                    >
                      Archive
                    </button>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Create Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 backdrop-blur-xs p-4">
          <div className="bg-white rounded-xl shadow-xl border border-slate-200 max-w-lg w-full p-6 space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <h2 className="text-lg font-bold text-slate-900">Add Approved Fact</h2>
              <button onClick={() => setShowCreateModal(false)} className="text-slate-400 hover:text-slate-600 p-1">
                <X className="w-5 h-5" />
              </button>
            </div>

            {formError && (
              <div className="p-3 bg-rose-50 border border-rose-200 text-rose-800 text-xs rounded-lg">
                {formError}
              </div>
            )}

            <form onSubmit={handleCreateSubmit} className="space-y-3">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Fact Name</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Energy savings, Product warranty"
                  value={formData.fact_name}
                  onChange={(e) => setFormData({ ...formData, fact_name: e.target.value })}
                  className="w-full px-3 py-2 text-sm border border-slate-200 rounded-lg focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Approved Value</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Up to 60% in laboratory tests, 3 years"
                  value={formData.approved_value}
                  onChange={(e) => setFormData({ ...formData, approved_value: e.target.value })}
                  className="w-full px-3 py-2 text-sm border border-slate-200 rounded-lg focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div className="grid grid-cols-3 gap-2">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Operator</label>
                  <select
                    value={formData.numeric_operator}
                    onChange={(e) => setFormData({ ...formData, numeric_operator: e.target.value })}
                    className="w-full px-2 py-2 text-sm border border-slate-200 rounded-lg focus:outline-none"
                  >
                    <option value="<=">&lt;= (Max)</option>
                    <option value="==">== (Exact)</option>
                    <option value=">=">&gt;= (Min)</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Number</label>
                  <input
                    type="number"
                    step="any"
                    placeholder="60"
                    value={formData.numeric_value}
                    onChange={(e) => setFormData({ ...formData, numeric_value: e.target.value })}
                    className="w-full px-3 py-2 text-sm border border-slate-200 rounded-lg focus:outline-none"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Unit</label>
                  <input
                    type="text"
                    placeholder="%, years"
                    value={formData.unit}
                    onChange={(e) => setFormData({ ...formData, unit: e.target.value })}
                    className="w-full px-3 py-2 text-sm border border-slate-200 rounded-lg focus:outline-none"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Scope</label>
                  <input
                    type="text"
                    placeholder="e.g. laboratory tests, consumer hardware"
                    value={formData.scope}
                    onChange={(e) => setFormData({ ...formData, scope: e.target.value })}
                    className="w-full px-3 py-2 text-sm border border-slate-200 rounded-lg focus:outline-none"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Source</label>
                  <input
                    type="text"
                    placeholder="e.g. Lab Report Q3"
                    value={formData.source}
                    onChange={(e) => setFormData({ ...formData, source: e.target.value })}
                    className="w-full px-3 py-2 text-sm border border-slate-200 rounded-lg focus:outline-none"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Required Qualifiers (Comma-separated)
                </label>
                <input
                  type="text"
                  placeholder="e.g. in laboratory tests"
                  value={formData.required_qualifiers}
                  onChange={(e) => setFormData({ ...formData, required_qualifiers: e.target.value })}
                  className="w-full px-3 py-2 text-sm border border-slate-200 rounded-lg focus:outline-none"
                />
              </div>

              <div className="pt-2 flex items-center justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="px-3.5 py-2 text-xs font-medium text-slate-600 hover:bg-slate-100 rounded-lg"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="px-4 py-2 text-xs font-medium bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg transition shadow-xs"
                >
                  {submitting ? 'Saving...' : role === 'admin' ? 'Save & Approve' : 'Submit for Review'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Supersede Modal */}
      {showSupersedeModal && targetFact && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 backdrop-blur-xs p-4">
          <div className="bg-white rounded-xl shadow-xl border border-slate-200 max-w-lg w-full p-6 space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <div>
                <h2 className="text-lg font-bold text-slate-900">Supersede Fact (Create v{targetFact.version + 1})</h2>
                <p className="text-xs text-slate-500">Updating fact: {targetFact.fact_name}</p>
              </div>
              <button onClick={() => setShowSupersedeModal(false)} className="text-slate-400 hover:text-slate-600 p-1">
                <X className="w-5 h-5" />
              </button>
            </div>

            {formError && (
              <div className="p-3 bg-rose-50 border border-rose-200 text-rose-800 text-xs rounded-lg">
                {formError}
              </div>
            )}

            <form onSubmit={handleSupersedeSubmit} className="space-y-3">
              <div className="p-2.5 bg-slate-50 rounded-lg border border-slate-200 text-xs text-slate-600">
                <span className="font-semibold block text-slate-700">Current Value (v{targetFact.version}):</span>
                {targetFact.approved_value}
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">New Approved Value</label>
                <input
                  type="text"
                  required
                  value={supersedeData.approved_value}
                  onChange={(e) => setSupersedeData({ ...supersedeData, approved_value: e.target.value })}
                  className="w-full px-3 py-2 text-sm border border-slate-200 rounded-lg focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div className="grid grid-cols-3 gap-2">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Operator</label>
                  <select
                    value={supersedeData.numeric_operator}
                    onChange={(e) => setSupersedeData({ ...supersedeData, numeric_operator: e.target.value })}
                    className="w-full px-2 py-2 text-sm border border-slate-200 rounded-lg focus:outline-none"
                  >
                    <option value="<=">&lt;= (Max)</option>
                    <option value="==">== (Exact)</option>
                    <option value=">=">&gt;= (Min)</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Number</label>
                  <input
                    type="number"
                    step="any"
                    value={supersedeData.numeric_value}
                    onChange={(e) => setSupersedeData({ ...supersedeData, numeric_value: e.target.value })}
                    className="w-full px-3 py-2 text-sm border border-slate-200 rounded-lg focus:outline-none"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Unit</label>
                  <input
                    type="text"
                    value={supersedeData.unit}
                    onChange={(e) => setSupersedeData({ ...supersedeData, unit: e.target.value })}
                    className="w-full px-3 py-2 text-sm border border-slate-200 rounded-lg focus:outline-none"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">New Source Citation</label>
                <input
                  type="text"
                  required
                  value={supersedeData.source}
                  onChange={(e) => setSupersedeData({ ...supersedeData, source: e.target.value })}
                  className="w-full px-3 py-2 text-sm border border-slate-200 rounded-lg focus:outline-none"
                />
              </div>

              <div className="pt-2 flex items-center justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setShowSupersedeModal(false)}
                  className="px-3.5 py-2 text-xs font-medium text-slate-600 hover:bg-slate-100 rounded-lg"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="px-4 py-2 text-xs font-medium bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg transition shadow-xs"
                >
                  {submitting ? 'Superseding...' : 'Supersede & Activate v' + (targetFact.version + 1)}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

