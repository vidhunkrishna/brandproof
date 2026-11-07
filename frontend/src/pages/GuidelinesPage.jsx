import React, { useState, useEffect } from 'react';
import apiClient from '../api/client';
import { useAuth } from '../contexts/AuthContext';
import { 
  Plus, 
  Search, 
  Filter, 
  CheckCircle2, 
  Clock, 
  Archive, 
  ShieldAlert, 
  Tag, 
  RefreshCw,
  X
} from 'lucide-react';

export default function GuidelinesPage() {
  const { role } = useAuth();
  const [guidelines, setGuidelines] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [categoryFilter, setCategoryFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [searchQuery, setSearchQuery] = useState('');

  // Modal State
  const [showModal, setShowModal] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [formError, setFormError] = useState(null);
  const [formData, setFormData] = useState({
    title: '',
    category: 'performance',
    rule_text: '',
    prohibited_phrases: '',
    required_phrases: '',
    source: 'Brand Manual 2026',
  });

  const fetchGuidelines = async () => {
    setLoading(true);
    setError(null);
    try {
      const params = {};
      if (categoryFilter) params.category = categoryFilter;
      if (statusFilter) params.status = statusFilter;
      if (searchQuery) params.search = searchQuery;

      const res = await apiClient.get('/api/v1/guidelines/', { params });
      setGuidelines(res.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to fetch brand guidelines');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchGuidelines();
    return () => {};
  }, [categoryFilter, statusFilter]);

  const handleSearch = (e) => {
    e.preventDefault();
    fetchGuidelines();
  };

  const handleApprove = async (id) => {
    try {
      await apiClient.put(`/api/v1/guidelines/${id}/approve`);
      fetchGuidelines();
    } catch (err) {
      alert(err.response?.data?.detail || 'Approval failed');
    }
  };

  const handleArchive = async (id) => {
    if (!confirm('Are you sure you want to archive this brand guideline?')) return;
    try {
      await apiClient.delete(`/api/v1/guidelines/${id}`);
      fetchGuidelines();
    } catch (err) {
      alert(err.response?.data?.detail || 'Archive failed');
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    setFormError(null);
    try {
      const payload = {
        title: formData.title,
        category: formData.category,
        rule_text: formData.rule_text,
        prohibited_phrases: formData.prohibited_phrases
          ? formData.prohibited_phrases.split(',').map((s) => s.trim()).filter(Boolean)
          : [],
        required_phrases: formData.required_phrases
          ? formData.required_phrases.split(',').map((s) => s.trim()).filter(Boolean)
          : [],
        source: formData.source,
      };

      await apiClient.post('/api/v1/guidelines/', payload);
      setShowModal(false);
      setFormData({
        title: '',
        category: 'performance',
        rule_text: '',
        prohibited_phrases: '',
        required_phrases: '',
        source: 'Brand Manual 2026',
      });
      fetchGuidelines();
    } catch (err) {
      setFormError(err.response?.data?.detail || 'Failed to save guideline');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Brand Guidelines</h1>
          <p className="text-sm text-slate-500 mt-1">
            Rules, required phrasing, and prohibited terminology governing marketing claims.
          </p>
        </div>
        <button
          onClick={() => setShowModal(true)}
          className="inline-flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-sm font-medium transition shadow-xs cursor-pointer self-start sm:self-auto"
        >
          <Plus className="w-4 h-4" />
          Add Guideline
        </button>
      </div>

      {/* Filters Bar */}
      <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs flex flex-wrap items-center justify-between gap-4">
        <form onSubmit={handleSearch} className="flex items-center gap-2 flex-1 min-w-[240px]">
          <div className="relative flex-1">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search rule text or title..."
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
          {/* Category Dropdown */}
          <select
            value={categoryFilter}
            onChange={(e) => setCategoryFilter(e.target.value)}
            className="text-xs font-medium text-slate-700 bg-slate-50 border border-slate-200 rounded-lg px-2.5 py-1.5 focus:outline-none"
          >
            <option value="">All Categories</option>
            <option value="performance">Performance</option>
            <option value="warranty">Warranty</option>
            <option value="terminology">Terminology</option>
            <option value="compliance">Compliance</option>
            <option value="pricing">Pricing</option>
          </select>

          {/* Status Dropdown */}
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="text-xs font-medium text-slate-700 bg-slate-50 border border-slate-200 rounded-lg px-2.5 py-1.5 focus:outline-none"
          >
            <option value="">All Statuses</option>
            <option value="active">Active</option>
            <option value="draft">Draft / Candidate</option>
            <option value="archived">Archived</option>
          </select>

          <button
            onClick={fetchGuidelines}
            disabled={loading}
            className="p-1.5 text-slate-500 hover:text-slate-800 rounded-lg border border-slate-200 hover:bg-slate-50"
            title="Refresh list"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Guidelines Grid */}
      {loading ? (
        <div className="bg-white rounded-xl border border-slate-200 p-12 text-center text-slate-400">
          <RefreshCw className="w-6 h-6 animate-spin mx-auto mb-2 text-indigo-600" />
          Loading organization guidelines...
        </div>
      ) : error ? (
        <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-sm">
          {error}
        </div>
      ) : guidelines.length === 0 ? (
        <div className="bg-white rounded-xl border border-dashed border-slate-300 p-12 text-center">
          <p className="text-slate-600 font-medium">No guidelines found matching your filter.</p>
          <p className="text-xs text-slate-400 mt-1">Create a new guideline or import a brand document.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {guidelines.map((g) => (
            <div
              key={g.id}
              className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs hover:border-slate-300 transition flex flex-col justify-between"
            >
              <div className="space-y-3">
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <h3 className="font-semibold text-slate-900 leading-snug">{g.title}</h3>
                    <div className="flex items-center gap-2 mt-1">
                      <span className="text-[11px] font-semibold tracking-wider uppercase px-2 py-0.5 rounded bg-slate-100 text-slate-600">
                        {g.category}
                      </span>
                      <span className="text-xs text-slate-400 font-mono">v{g.version}</span>
                    </div>
                  </div>

                  {/* Status Badge */}
                  {g.status === 'active' ? (
                    <span className="inline-flex items-center gap-1 text-xs font-medium text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-200">
                      <CheckCircle2 className="w-3 h-3 text-emerald-600" />
                      Active
                    </span>
                  ) : g.status === 'draft' ? (
                    <span className="inline-flex items-center gap-1 text-xs font-medium text-amber-700 bg-amber-50 px-2 py-0.5 rounded-full border border-amber-200">
                      <Clock className="w-3 h-3 text-amber-600" />
                      Pending Approval
                    </span>
                  ) : (
                    <span className="inline-flex items-center gap-1 text-xs font-medium text-slate-600 bg-slate-100 px-2 py-0.5 rounded-full">
                      <Archive className="w-3 h-3" />
                      Archived
                    </span>
                  )}
                </div>

                <p className="text-sm text-slate-700 leading-relaxed bg-slate-50 p-3 rounded-lg border border-slate-100">
                  {g.rule_text}
                </p>

                {/* Phrase Constraints */}
                <div className="space-y-1.5 text-xs">
                  {g.required_phrases && g.required_phrases.length > 0 && (
                    <div className="flex items-start gap-1.5">
                      <span className="text-emerald-700 font-semibold shrink-0">Required:</span>
                      <div className="flex flex-wrap gap-1">
                        {g.required_phrases.map((phrase, idx) => (
                          <span
                            key={idx}
                            className="bg-emerald-50 text-emerald-800 border border-emerald-100 px-1.5 py-0.5 rounded text-[11px]"
                          >
                            "{phrase}"
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {g.prohibited_phrases && g.prohibited_phrases.length > 0 && (
                    <div className="flex items-start gap-1.5">
                      <span className="text-rose-700 font-semibold shrink-0">Forbidden:</span>
                      <div className="flex flex-wrap gap-1">
                        {g.prohibited_phrases.map((phrase, idx) => (
                          <span
                            key={idx}
                            className="bg-rose-50 text-rose-800 border border-rose-100 px-1.5 py-0.5 rounded text-[11px]"
                          >
                            "{phrase}"
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>

              {/* Card Footer & Admin Actions */}
              <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-xs text-slate-400">
                <span className="truncate max-w-[200px]" title={g.source}>
                  Source: {g.source || 'Manual'}
                </span>

                <div className="flex items-center gap-2">
                  {g.status === 'draft' && role === 'admin' && (
                    <button
                      onClick={() => handleApprove(g.id)}
                      className="px-2.5 py-1 bg-emerald-600 hover:bg-emerald-700 text-white rounded text-xs font-medium transition cursor-pointer"
                    >
                      Approve Rule
                    </button>
                  )}
                  {g.status === 'active' && role === 'admin' && (
                    <button
                      onClick={() => handleArchive(g.id)}
                      className="px-2 py-1 text-slate-500 hover:text-rose-600 rounded hover:bg-slate-100 transition cursor-pointer"
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
      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 backdrop-blur-xs p-4">
          <div className="bg-white rounded-xl shadow-xl border border-slate-200 max-w-lg w-full p-6 space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <h2 className="text-lg font-bold text-slate-900">Add Brand Guideline</h2>
              <button
                onClick={() => setShowModal(false)}
                className="text-slate-400 hover:text-slate-600 p-1"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {formError && (
              <div className="p-3 bg-rose-50 border border-rose-200 text-rose-800 text-xs rounded-lg">
                {formError}
              </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-3.5">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Rule Title</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Energy Savings Qualification Policy"
                  value={formData.title}
                  onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                  className="w-full px-3 py-2 text-sm border border-slate-200 rounded-lg focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Category</label>
                  <select
                    value={formData.category}
                    onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                    className="w-full px-3 py-2 text-sm border border-slate-200 rounded-lg focus:outline-none"
                  >
                    <option value="performance">Performance</option>
                    <option value="warranty">Warranty</option>
                    <option value="terminology">Terminology</option>
                    <option value="compliance">Compliance</option>
                    <option value="pricing">Pricing</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Source Reference</label>
                  <input
                    type="text"
                    value={formData.source}
                    onChange={(e) => setFormData({ ...formData, source: e.target.value })}
                    className="w-full px-3 py-2 text-sm border border-slate-200 rounded-lg focus:outline-none"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Policy / Rule Text</label>
                <textarea
                  required
                  rows={3}
                  placeholder="State the exact brand constraint or claim rule..."
                  value={formData.rule_text}
                  onChange={(e) => setFormData({ ...formData, rule_text: e.target.value })}
                  className="w-full px-3 py-2 text-sm border border-slate-200 rounded-lg focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Prohibited Phrases (Comma-separated)
                </label>
                <input
                  type="text"
                  placeholder="e.g. 80% energy savings, lifetime warranty"
                  value={formData.prohibited_phrases}
                  onChange={(e) => setFormData({ ...formData, prohibited_phrases: e.target.value })}
                  className="w-full px-3 py-2 text-sm border border-slate-200 rounded-lg focus:outline-none"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Required Phrases (Comma-separated)
                </label>
                <input
                  type="text"
                  placeholder="e.g. in laboratory tests, 3-year warranty"
                  value={formData.required_phrases}
                  onChange={(e) => setFormData({ ...formData, required_phrases: e.target.value })}
                  className="w-full px-3 py-2 text-sm border border-slate-200 rounded-lg focus:outline-none"
                />
              </div>

              <div className="pt-2 flex items-center justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
                  className="px-3.5 py-2 text-xs font-medium text-slate-600 hover:bg-slate-100 rounded-lg transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="px-4 py-2 text-xs font-medium bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg transition shadow-xs"
                >
                  {submitting ? 'Saving...' : role === 'admin' ? 'Save & Activate' : 'Submit for Review'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

