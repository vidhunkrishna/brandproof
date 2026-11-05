import React, { useMemo, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { AlertCircle, FileText, Send, Sparkles } from 'lucide-react';
import apiClient from '../api/client';
import { useAuth } from '../contexts/AuthContext';

const DEMO_COPIES = [
  {
    title: 'Qualified energy savings',
    label: '60% energy savings',
    description: 'A qualified claim backed by the Lumen performance registry.',
    contentType: 'website_copy',
    copy: 'Lumen smart bulbs deliver up to 60% energy savings in laboratory tests.',
  },
  {
    title: 'Unqualified energy savings',
    label: '80% energy savings',
    description: 'A claim that exceeds Lumen’s registered energy limit.',
    contentType: 'website_copy',
    copy: 'Lumen smart bulbs deliver 80% energy savings for every home.',
  },
  {
    title: 'Lifetime warranty promotion',
    label: 'Lifetime warranty',
    description: 'Tests warranty terminology against the active brand guideline.',
    contentType: 'email',
    copy: 'Every Lumen smart bulb includes a lifetime warranty for complete peace of mind.',
  },
  {
    title: 'Unregistered performance claim',
    label: 'Unsupported fact',
    description: 'An empirical product claim with no approved registry evidence.',
    contentType: 'social_media',
    copy: 'Lumen bulbs last 50,000 hours and reduce maintenance costs by 40%.',
  },
  {
    title: 'Vague leadership claim',
    label: 'Unverifiable claim',
    description: 'A subjective claim that needs a verifiable standard.',
    contentType: 'general',
    copy: 'Lumen is the best choice for a brighter future.',
  },
];

function errorMessage(error, fallback) {
  const detail = error.response?.data?.detail;
  if (Array.isArray(detail)) return detail.map((item) => item.msg).join(' ');
  return detail || error.message || fallback;
}

export default function SubmitReviewPage() {
  const { role, quickLogin } = useAuth();
  const navigate = useNavigate();
  const [title, setTitle] = useState('');
  const [contentType, setContentType] = useState('website_copy');
  const [contentText, setContentText] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);

  const remainingCharacters = useMemo(() => 100000 - contentText.length, [contentText]);
  const canSubmit = title.trim() && contentText.trim() && !submitting;

  const loadDemo = (demo) => {
    setTitle(demo.title);
    setContentType(demo.contentType);
    setContentText(demo.copy);
    setError(null);
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      const response = await apiClient.post('/api/v1/submissions/', {
        title: title.trim(),
        content_type: contentType,
        content_text: contentText.trim(),
      });
      navigate(`/reviews/${response.data.id}`, {
        state: { submission: response.data, reviewResult: response.data.review_result },
      });
    } catch (requestError) {
      setError(errorMessage(requestError, 'Unable to submit this copy for review.'));
    } finally {
      setSubmitting(false);
    }
  };

  if (role !== 'admin' && role !== 'creator') {
    const isReviewer = role === 'reviewer';
    return (
      <div className="mx-auto max-w-2xl rounded-xl border border-slate-200 bg-white p-8 text-center shadow-xs">
        <FileText className="mx-auto mb-3 h-8 w-8 text-slate-400" />
        <h1 className="text-xl font-bold text-slate-900">{isReviewer ? 'Reviewers cannot submit marketing copy' : 'Your session is no longer active'}</h1>
        <p className="mt-2 text-sm leading-6 text-slate-600">
          {isReviewer
            ? 'Your role can inspect every organization submission and its evidence-linked results.'
            : 'Reconnect with a demo role before submitting a draft for review.'}
        </p>
        {isReviewer ? (
          <Link to="/submissions" className="mt-5 inline-flex rounded-lg bg-indigo-600 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-700">
            Open submission history
          </Link>
        ) : (
          <button onClick={() => quickLogin('admin')} className="mt-5 inline-flex rounded-lg bg-indigo-600 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-700">
            Reconnect as admin
          </button>
        )}
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-5xl space-y-6">
      <div className="flex flex-col justify-between gap-3 sm:flex-row sm:items-end">
        <div>
          <p className="text-xs font-bold uppercase tracking-[0.16em] text-indigo-600">Governance workspace</p>
          <h1 className="mt-1 text-2xl font-bold tracking-tight text-slate-900">Submit marketing copy</h1>
          <p className="mt-1 text-sm text-slate-500">Run each claim through Lumen’s rules, fact registry, and advisory review.</p>
        </div>
        <Link to="/submissions" className="text-sm font-semibold text-indigo-700 hover:text-indigo-900">
          View submission history
        </Link>
      </div>

      <section className="rounded-xl border border-indigo-100 bg-indigo-50/60 p-4">
        <div className="flex items-center gap-2 text-sm font-semibold text-indigo-950">
          <Sparkles className="h-4 w-4 text-indigo-600" />
          Lumen demo scenarios
        </div>
        <p className="mt-1 text-xs leading-5 text-indigo-800">Load a scenario, then submit it to see the backend’s actual review result.</p>
        <div className="mt-3 grid grid-cols-1 gap-2 sm:grid-cols-2 lg:grid-cols-3">
          {DEMO_COPIES.map((demo) => (
            <button
              key={demo.label}
              type="button"
              onClick={() => loadDemo(demo)}
              className="rounded-lg border border-indigo-100 bg-white px-3 py-2.5 text-left transition hover:border-indigo-300 hover:shadow-sm"
            >
              <span className="block text-xs font-bold text-slate-900">{demo.label}</span>
              <span className="mt-1 block text-[11px] leading-4 text-slate-500">{demo.description}</span>
            </button>
          ))}
          <div className="rounded-lg border border-dashed border-slate-300 bg-slate-50 px-3 py-2.5 text-left">
            <span className="block text-xs font-bold text-slate-600">Expired fact example unavailable</span>
            <span className="mt-1 block text-[11px] leading-4 text-slate-500">The current Lumen seed has no superseded or expired approved fact.</span>
          </div>
        </div>
      </section>

      <form onSubmit={handleSubmit} className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-xs">
        <div className="space-y-5 p-5 sm:p-6">
          {error && (
            <div role="alert" className="flex gap-2 rounded-lg border border-rose-200 bg-rose-50 p-3 text-sm text-rose-800">
              <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <div className="grid gap-4 md:grid-cols-[minmax(0,1fr)_220px]">
            <div>
              <label htmlFor="submission-title" className="mb-1.5 block text-sm font-semibold text-slate-800">Submission title</label>
              <input
                id="submission-title"
                required
                maxLength={255}
                value={title}
                onChange={(event) => setTitle(event.target.value)}
                placeholder="e.g. Winter campaign landing page"
                className="w-full rounded-lg border border-slate-200 px-3 py-2.5 text-sm outline-none transition placeholder:text-slate-400 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100"
              />
            </div>
            <div>
              <label htmlFor="content-type" className="mb-1.5 block text-sm font-semibold text-slate-800">Content type</label>
              <select
                id="content-type"
                value={contentType}
                onChange={(event) => setContentType(event.target.value)}
                className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2.5 text-sm outline-none transition focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100"
              >
                <option value="website_copy">Website</option>
                <option value="email">Email</option>
                <option value="social_media">Social media</option>
                <option value="general">General</option>
              </select>
            </div>
          </div>

          <div>
            <div className="mb-1.5 flex items-center justify-between gap-3">
              <label htmlFor="marketing-copy" className="block text-sm font-semibold text-slate-800">Marketing copy</label>
              <span className={`text-xs ${remainingCharacters < 500 ? 'text-amber-700' : 'text-slate-400'}`}>{contentText.length.toLocaleString()} / 100,000</span>
            </div>
            <textarea
              id="marketing-copy"
              required
              maxLength={100000}
              rows={13}
              value={contentText}
              onChange={(event) => setContentText(event.target.value)}
              placeholder="Paste the customer-facing copy you want to review..."
              className="min-h-72 w-full resize-y rounded-lg border border-slate-200 p-3 font-mono text-sm leading-6 outline-none transition placeholder:font-sans placeholder:text-slate-400 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100"
            />
          </div>
        </div>
        <div className="flex flex-col gap-3 border-t border-slate-100 bg-slate-50 px-5 py-4 sm:flex-row sm:items-center sm:justify-between sm:px-6">
          <p className="text-xs leading-5 text-slate-500">Results retain the exact submitted text, evidence, and immutable revision history.</p>
          <button
            type="submit"
            disabled={!canSubmit}
            className="inline-flex items-center justify-center gap-2 rounded-lg bg-indigo-600 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-indigo-700 disabled:cursor-not-allowed disabled:bg-slate-300"
          >
            <Send className="h-4 w-4" />
            {submitting ? 'Reviewing copy…' : 'Submit for review'}
          </button>
        </div>
      </form>
    </div>
  );
}
