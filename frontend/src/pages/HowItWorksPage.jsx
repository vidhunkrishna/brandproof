import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import apiClient from '../api/client';
import { useAuth, DEMO_PRESETS } from '../contexts/AuthContext';
import {
  ShieldCheck,
  CheckCircle2,
  AlertTriangle,
  Layers,
  Workflow,
  History,
  UserCheck,
  Compass,
  Send,
  ClipboardList,
  Scale,
  HeartPulse,
  BellRing,
  Image as ImageIcon,
  Sparkles,
  Target,
  FileCheck2,
  Zap,
  Lightbulb,
  Building2
} from 'lucide-react';

export default function HowItWorksPage() {
  const { role, quickLogin } = useAuth();
  const [seeding, setSeeding] = useState(false);
  const [seedStatus, setSeedStatus] = useState(null);

  const handleSeed = async () => {
    setSeeding(true);
    setSeedStatus(null);
    try {
      const res = await apiClient.post('/api/v1/auth/seed-demo');
      setSeedStatus({ type: 'success', message: res.data?.message || 'Synthetic demo data successfully initialized!' });
    } catch (err) {
      setSeedStatus({ type: 'error', message: err.response?.data?.detail || 'Failed to initialize demo data.' });
    } finally {
      setSeeding(false);
    }
  };


  return (
    <div className="space-y-12 max-w-6xl mx-auto pb-16 font-sans">
      {/* Hero Section */}
      <section className="bg-gradient-to-br from-indigo-900 via-indigo-800 to-slate-900 text-white rounded-3xl p-8 sm:p-12 shadow-xl border border-indigo-700/30 relative overflow-hidden">
        <div className="absolute -right-16 -bottom-16 w-80 h-80 bg-indigo-500/10 rounded-full blur-3xl pointer-events-none"></div>
        <div className="absolute right-12 top-10 w-48 h-48 bg-purple-500/10 rounded-full blur-2xl pointer-events-none"></div>

        <div className="relative z-10 max-w-3xl space-y-4">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-500/20 border border-indigo-400/30 text-indigo-200 text-xs font-semibold uppercase tracking-wider">
            <Sparkles className="w-3.5 h-3.5 text-indigo-300" />
            Judge &amp; Evaluator Product Guide
          </div>
          <h1 className="text-3xl sm:text-4xl lg:text-5xl font-extrabold tracking-tight text-white leading-tight">
            BrandProof: <span className="text-indigo-300">Evidence Before Approval</span>
          </h1>
          <p className="text-base sm:text-lg text-indigo-100/90 leading-relaxed">
            An explainable, AI-assisted brand governance platform that validates marketing copy against human-approved brand rules and a versioned facts registry before publication.
          </p>

          <div className="flex flex-wrap items-center gap-3 pt-4">
            <Link
              to="/submit"
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-white text-indigo-900 font-bold text-sm hover:bg-indigo-50 transition shadow-sm"
            >
              <Send className="w-4 h-4 text-indigo-600" />
              Try Review Engine
            </Link>
            <a
              href="#quick-start"
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-indigo-700/60 hover:bg-indigo-700 border border-indigo-400/30 text-white font-medium text-sm transition"
            >
              <Compass className="w-4 h-4 text-indigo-300" />
              Judge Quick-Start
            </a>
            <a
              href="#verdicts"
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-indigo-700/60 hover:bg-indigo-700 border border-indigo-400/30 text-white font-medium text-sm transition"
            >
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
              Review Verdicts
            </a>
          </div>
        </div>

        {/* Quick Navigation Anchor Bar */}
        <div className="mt-8 pt-6 border-t border-indigo-700/40 flex flex-wrap items-center gap-y-2 gap-x-6 text-xs text-indigo-200">
          <span className="font-semibold text-white uppercase tracking-wider">Jump to:</span>
          <a href="#what-is-brandproof" className="hover:text-white transition">A. What is BrandProof</a>
          <a href="#roles" className="hover:text-white transition">B. Three Roles</a>
          <a href="#workflow" className="hover:text-white transition">C. End-to-End Workflow</a>
          <a href="#verdicts" className="hover:text-white transition">D. Review Verdicts</a>
          <a href="#outputs" className="hover:text-white transition">E. Expected Outputs</a>
          <a href="#quick-start" className="hover:text-white transition">F. Quick-Start Walkthrough</a>
          <a href="#lumen-demo" className="hover:text-white transition">G. Synthetic Lumen Brand</a>
        </div>
      </section>

      {/* Section A: What is BrandProof? */}
      <section id="what-is-brandproof" className="space-y-6">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-xl bg-indigo-100 text-indigo-700">
            <ShieldCheck className="w-6 h-6" />
          </div>
          <div>
            <span className="text-xs font-bold text-indigo-600 uppercase tracking-widest">Section A</span>
            <h2 className="text-2xl font-bold text-slate-900 tracking-tight">What is BrandProof?</h2>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-xs space-y-3">
            <div className="w-10 h-10 rounded-xl bg-indigo-50 border border-indigo-100 flex items-center justify-center text-indigo-600 font-bold">
              1
            </div>
            <h3 className="font-bold text-slate-900 text-base">The Core Problem</h3>
            <p className="text-sm text-slate-600 leading-relaxed">
              Generative AI tools produce persuasive marketing copy that frequently hallucinates empirical numbers, violates internal brand rules, or promises unauthorized warranties. Legal and brand teams are overwhelmed by manual reviews.
            </p>
          </div>

          <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-xs space-y-3">
            <div className="w-10 h-10 rounded-xl bg-purple-50 border border-purple-100 flex items-center justify-center text-purple-600 font-bold">
              2
            </div>
            <h3 className="font-bold text-slate-900 text-base">The BrandProof Solution</h3>
            <p className="text-sm text-slate-600 leading-relaxed">
              BrandProof operates as an evidence-first governance firewall. Rather than generating text blindly, it enforces a human-approved brand rulebook and a versioned approved-facts registry before content goes live.
            </p>
          </div>

          <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-xs space-y-3">
            <div className="w-10 h-10 rounded-xl bg-emerald-50 border border-emerald-100 flex items-center justify-center text-emerald-600 font-bold">
              3
            </div>
            <h3 className="font-bold text-slate-900 text-base">Our Key Differentiator</h3>
            <p className="text-sm text-slate-600 leading-relaxed">
              Every single finding is <span className="font-semibold text-slate-900">explainable and evidence-linked</span>. Claims highlight exact character offsets, calculate numeric deviations, cite registry entries, and record immutable audit revisions.
            </p>
          </div>
        </div>
      </section>

      {/* Section B: Understand the Three Roles */}
      <section id="roles" className="space-y-6">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-xl bg-indigo-100 text-indigo-700">
            <UserCheck className="w-6 h-6" />
          </div>
          <div>
            <span className="text-xs font-bold text-indigo-600 uppercase tracking-widest">Section B</span>
            <h2 className="text-2xl font-bold text-slate-900 tracking-tight">Understand the Three Roles</h2>
          </div>
        </div>

        <p className="text-sm text-slate-600 max-w-3xl">
          BrandProof implements strict role-based access control (RBAC). Judges can seamlessly test all three personas using the role switcher in the top navigation bar.
        </p>

        {/* Role Cards Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Admin */}
          <div className="bg-white rounded-2xl border-2 border-indigo-200 p-6 shadow-xs flex flex-col justify-between relative overflow-hidden">
            <div className="absolute top-0 right-0 w-24 h-24 bg-indigo-50 rounded-bl-full -z-0"></div>
            <div className="relative z-10 space-y-4">
              <div className="flex items-center justify-between">
                <span className="px-2.5 py-1 rounded-full text-xs font-bold bg-indigo-100 text-indigo-800">
                  Role: Admin
                </span>
                <span className="text-xs text-slate-400 font-mono">admin@lumen.demo</span>
              </div>
              <h3 className="text-lg font-bold text-slate-900">Governance &amp; Authority</h3>
              <ul className="space-y-2 text-xs text-slate-600">
                <li className="flex items-start gap-2">
                  <CheckCircle2 className="w-4 h-4 text-indigo-600 shrink-0 mt-0.5" />
                  <span><strong>Manage Brand Guidelines:</strong> Create, approve, activate, and archive versioned rulebooks.</span>
                </li>
                <li className="flex items-start gap-2">
                  <CheckCircle2 className="w-4 h-4 text-indigo-600 shrink-0 mt-0.5" />
                  <span><strong>Manage Approved Facts:</strong> Register empirical metrics with numeric bounds and expirations.</span>
                </li>
                <li className="flex items-start gap-2">
                  <CheckCircle2 className="w-4 h-4 text-indigo-600 shrink-0 mt-0.5" />
                  <span><strong>Document Import:</strong> Ingest .PDF &amp; .DOCX manuals to stage candidate rules.</span>
                </li>
                <li className="flex items-start gap-2">
                  <CheckCircle2 className="w-4 h-4 text-indigo-600 shrink-0 mt-0.5" />
                  <span><strong>Guideline Health &amp; FactWatch:</strong> Monitor rule conflicts, expiration risks, and affected submissions.</span>
                </li>
                <li className="flex items-start gap-2">
                  <CheckCircle2 className="w-4 h-4 text-indigo-600 shrink-0 mt-0.5" />
                  <span><strong>Visual Compliance:</strong> Verify image dimensions, color contrast, and logo ratios.</span>
                </li>
              </ul>
            </div>
            <div className="pt-4 mt-4 border-t border-slate-100 relative z-10">
              <button
                onClick={() => quickLogin('admin')}
                className="w-full py-2 px-3 rounded-lg text-xs font-semibold bg-indigo-50 text-indigo-700 hover:bg-indigo-100 transition cursor-pointer"
              >
                Switch to Admin Persona
              </button>
            </div>
          </div>

          {/* Creator */}
          <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs flex flex-col justify-between relative overflow-hidden">
            <div className="relative z-10 space-y-4">
              <div className="flex items-center justify-between">
                <span className="px-2.5 py-1 rounded-full text-xs font-bold bg-emerald-100 text-emerald-800">
                  Role: Creator
                </span>
                <span className="text-xs text-slate-400 font-mono">creator@lumen.demo</span>
              </div>
              <h3 className="text-lg font-bold text-slate-900">Authoring &amp; Remediation</h3>
              <ul className="space-y-2 text-xs text-slate-600">
                <li className="flex items-start gap-2">
                  <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
                  <span><strong>Submit Marketing Content:</strong> Website copy, email campaigns, social posts, and ads.</span>
                </li>
                <li className="flex items-start gap-2">
                  <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
                  <span><strong>Inspect Evidence Spans:</strong> Real-time visual feedback on compliant and non-compliant claims.</span>
                </li>
                <li className="flex items-start gap-2">
                  <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
                  <span><strong>Edit &amp; Recheck:</strong> Revise text directly and trigger new revisions preserving revision history.</span>
                </li>
                <li className="flex items-start gap-2">
                  <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
                  <span><strong>Raise Disputes:</strong> Contest unjustified findings with contextual justifications for human review.</span>
                </li>
              </ul>
            </div>
            <div className="pt-4 mt-4 border-t border-slate-100 relative z-10">
              <button
                onClick={() => quickLogin('creator')}
                className="w-full py-2 px-3 rounded-lg text-xs font-semibold bg-emerald-50 text-emerald-700 hover:bg-emerald-100 transition cursor-pointer"
              >
                Switch to Creator Persona
              </button>
            </div>
          </div>

          {/* Reviewer */}
          <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs flex flex-col justify-between relative overflow-hidden">
            <div className="relative z-10 space-y-4">
              <div className="flex items-center justify-between">
                <span className="px-2.5 py-1 rounded-full text-xs font-bold bg-amber-100 text-amber-800">
                  Role: Reviewer
                </span>
                <span className="text-xs text-slate-400 font-mono">reviewer@lumen.demo</span>
              </div>
              <h3 className="text-lg font-bold text-slate-900">Arbitration &amp; Auditing</h3>
              <ul className="space-y-2 text-xs text-slate-600">
                <li className="flex items-start gap-2">
                  <CheckCircle2 className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
                  <span><strong>Review Disputed Findings:</strong> Inspect disputes submitted by creators across the organization.</span>
                </li>
                <li className="flex items-start gap-2">
                  <CheckCircle2 className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
                  <span><strong>Examine Supporting Evidence:</strong> Evaluate the claimed text against approved facts and rules.</span>
                </li>
                <li className="flex items-start gap-2">
                  <CheckCircle2 className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
                  <span><strong>Uphold or Override:</strong> Confirm the automated finding or override with an explicit verdict.</span>
                </li>
                <li className="flex items-start gap-2">
                  <CheckCircle2 className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
                  <span><strong>Maintain Audit Log:</strong> Record binding resolution notes permanently attached to the submission.</span>
                </li>
              </ul>
            </div>
            <div className="pt-4 mt-4 border-t border-slate-100 relative z-10">
              <button
                onClick={() => quickLogin('reviewer')}
                className="w-full py-2 px-3 rounded-lg text-xs font-semibold bg-amber-50 text-amber-700 hover:bg-amber-100 transition cursor-pointer"
              >
                Switch to Reviewer Persona
              </button>
            </div>
          </div>
        </div>
      </section>

      {/* Section C: Complete End-to-End Workflow */}
      <section id="workflow" className="space-y-6">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-xl bg-indigo-100 text-indigo-700">
            <Workflow className="w-6 h-6" />
          </div>
          <div>
            <span className="text-xs font-bold text-indigo-600 uppercase tracking-widest">Section C</span>
            <h2 className="text-2xl font-bold text-slate-900 tracking-tight">Complete End-to-End Workflow</h2>
          </div>
        </div>

        <p className="text-sm text-slate-600 max-w-3xl">
          BrandProof processes content through a nine-step verifiable governance lifecycle:
        </p>

        {/* 9 Step Visual Roadmap */}
        <div className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs flex items-start gap-3">
              <span className="flex items-center justify-center w-7 h-7 rounded-full bg-indigo-600 text-white font-bold text-xs shrink-0">1</span>
              <div>
                <h4 className="font-bold text-slate-900 text-sm">Establish Rulebook</h4>
                <p className="text-xs text-slate-500 mt-1">Admin registers guidelines (required/forbidden phrasing) and approved facts (empirical limits).</p>
              </div>
            </div>

            <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs flex items-start gap-3">
              <span className="flex items-center justify-center w-7 h-7 rounded-full bg-indigo-600 text-white font-bold text-xs shrink-0">2</span>
              <div>
                <h4 className="font-bold text-slate-900 text-sm">Import &amp; Stage Rules</h4>
                <p className="text-xs text-slate-500 mt-1">Admin extracts candidate guidelines from PDF/Word manuals and approves them into active status.</p>
              </div>
            </div>

            <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs flex items-start gap-3">
              <span className="flex items-center justify-center w-7 h-7 rounded-full bg-indigo-600 text-white font-bold text-xs shrink-0">3</span>
              <div>
                <h4 className="font-bold text-slate-900 text-sm">Submit Marketing Copy</h4>
                <p className="text-xs text-slate-500 mt-1">Creator drafts copy or selects pre-built demo scenarios in the interactive submission editor.</p>
              </div>
            </div>
          </div>

          {/* Three Review Lanes Spotlight Box */}
          <div className="bg-gradient-to-r from-slate-900 to-indigo-950 text-white p-6 rounded-2xl border border-indigo-500/20 shadow-md space-y-4">
            <div className="flex items-center gap-2 text-indigo-300 text-xs font-bold uppercase tracking-wider">
              <Layers className="w-4 h-4" />
              Step 4: The Three Review Lanes
            </div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
              <div className="bg-white/5 border border-white/10 p-4 rounded-xl space-y-2">
                <span className="inline-block px-2 py-0.5 rounded bg-indigo-500/30 text-indigo-200 font-semibold">Lane 1</span>
                <h5 className="font-bold text-white text-sm">Deterministic Rule Check</h5>
                <p className="text-indigo-200/80">Exact &amp; regex scanning for prohibited terms, missing mandatory qualifiers, and categorization rules.</p>
              </div>
              <div className="bg-white/5 border border-white/10 p-4 rounded-xl space-y-2">
                <span className="inline-block px-2 py-0.5 rounded bg-purple-500/30 text-purple-200 font-semibold">Lane 2</span>
                <h5 className="font-bold text-white text-sm">Grounded Fact Comparison</h5>
                <p className="text-indigo-200/80">Numeric extraction, tolerance comparison, qualifier verification, and active-date validity against registry facts.</p>
              </div>
              <div className="bg-white/5 border border-white/10 p-4 rounded-xl space-y-2">
                <span className="inline-block px-2 py-0.5 rounded bg-emerald-500/30 text-emerald-200 font-semibold">Lane 3</span>
                <h5 className="font-bold text-white text-sm">Advisory AI Analysis</h5>
                <p className="text-indigo-200/80">Contextual evaluation detecting subjective hyperbole, subtle tone shifts, or unverifiable claims. Non-blocking.</p>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs flex items-start gap-3">
              <span className="flex items-center justify-center w-7 h-7 rounded-full bg-indigo-600 text-white font-bold text-xs shrink-0">5</span>
              <div>
                <h4 className="font-bold text-slate-900 text-sm">Evidence-Linked Findings</h4>
                <p className="text-xs text-slate-500 mt-1">Review engine marks exact UTF-16 character offsets and outputs verdict badges with evidence references.</p>
              </div>
            </div>

            <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs flex items-start gap-3">
              <span className="flex items-center justify-center w-7 h-7 rounded-full bg-indigo-600 text-white font-bold text-xs shrink-0">6</span>
              <div>
                <h4 className="font-bold text-slate-900 text-sm">Remediation &amp; Recheck</h4>
                <p className="text-xs text-slate-500 mt-1">Creator revises copy in-line and submits Revision 2 without overwriting historical audit findings.</p>
              </div>
            </div>

            <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs flex items-start gap-3">
              <span className="flex items-center justify-center w-7 h-7 rounded-full bg-indigo-600 text-white font-bold text-xs shrink-0">7</span>
              <div>
                <h4 className="font-bold text-slate-900 text-sm">Dispute &amp; Resolution</h4>
                <p className="text-xs text-slate-500 mt-1">Creators can contest findings. Reviewers inspect justifications and uphold or override verdicts.</p>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs flex items-start gap-3">
              <span className="flex items-center justify-center w-7 h-7 rounded-full bg-indigo-600 text-white font-bold text-xs shrink-0">8</span>
              <div>
                <h4 className="font-bold text-slate-900 text-sm">Lifecycle Monitoring (FactWatch)</h4>
                <p className="text-xs text-slate-500 mt-1">Tracks expiring facts and automatically flags submissions linked to superseded evidence.</p>
              </div>
            </div>

            <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs flex items-start gap-3">
              <span className="flex items-center justify-center w-7 h-7 rounded-full bg-indigo-600 text-white font-bold text-xs shrink-0">9</span>
              <div>
                <h4 className="font-bold text-slate-900 text-sm">Governance Analytics</h4>
                <p className="text-xs text-slate-500 mt-1">Aggregates organization-wide compliance trends, frequently violated policies, and dispute velocity.</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Section D: Explain Review Verdicts */}
      <section id="verdicts" className="space-y-6">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-xl bg-indigo-100 text-indigo-700">
            <CheckCircle2 className="w-6 h-6" />
          </div>
          <div>
            <span className="text-xs font-bold text-indigo-600 uppercase tracking-widest">Section D</span>
            <h2 className="text-2xl font-bold text-slate-900 tracking-tight">Explain Review Verdicts</h2>
          </div>
        </div>

        <p className="text-sm text-slate-600 max-w-3xl">
          BrandProof uses five standardized claim-level verdicts. Understanding these distinctions is critical for evaluating compliance outputs:
        </p>

        {/* Verdicts Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {/* CORRECT */}
          <div className="bg-white rounded-2xl border border-emerald-200 p-5 shadow-xs space-y-3">
            <div className="flex items-center justify-between">
              <span className="inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold bg-emerald-50 text-emerald-800 border-emerald-200">
                CORRECT
              </span>
              <span className="text-xs text-emerald-600 font-semibold">Fully Approved</span>
            </div>
            <h4 className="font-bold text-slate-900 text-sm">Supported by Active Evidence</h4>
            <p className="text-xs text-slate-600 leading-relaxed">
              The claim matches an approved registry fact, respects configured numeric limits, and includes all required qualifiers (such as lab-test references).
            </p>
            <div className="bg-emerald-50/50 p-3 rounded-lg border border-emerald-100 text-xs">
              <span className="font-semibold text-emerald-900 block">Lumen Demo Example:</span>
              <span className="italic text-slate-700">"Lumen smart bulbs deliver up to 60% energy savings in laboratory tests."</span>
            </div>
          </div>

          {/* CONTRADICTED */}
          <div className="bg-white rounded-2xl border border-rose-200 p-5 shadow-xs space-y-3">
            <div className="flex items-center justify-between">
              <span className="inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold bg-rose-50 text-rose-800 border-rose-200">
                CONTRADICTED
              </span>
              <span className="text-xs text-rose-600 font-semibold">Direct Conflict</span>
            </div>
            <h4 className="font-bold text-slate-900 text-sm">Exceeds Limits or Prohibited</h4>
            <p className="text-xs text-slate-600 leading-relaxed">
              The claim contradicts verified evidence (e.g. claiming 80% when maximum is 60%) or uses forbidden brand phrases (e.g. "lifetime warranty").
            </p>
            <div className="bg-rose-50/50 p-3 rounded-lg border border-rose-100 text-xs">
              <span className="font-semibold text-rose-900 block">Lumen Demo Example:</span>
              <span className="italic text-slate-700">"Lumen smart bulbs deliver 80% energy savings for every home."</span>
            </div>
          </div>

          {/* OUTDATED */}
          <div className="bg-white rounded-2xl border border-amber-200 p-5 shadow-xs space-y-3">
            <div className="flex items-center justify-between">
              <span className="inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold bg-amber-50 text-amber-800 border-amber-200">
                OUTDATED
              </span>
              <span className="text-xs text-amber-600 font-semibold">Expired Evidence</span>
            </div>
            <h4 className="font-bold text-slate-900 text-sm">Superseded or Stale Fact</h4>
            <p className="text-xs text-slate-600 leading-relaxed">
              The claim references an approved fact that was once valid, but has passed its expiration date or been superseded by a newer registry version.
            </p>
            <div className="bg-amber-50/50 p-3 rounded-lg border border-amber-100 text-xs">
              <span className="font-semibold text-amber-900 block">Lumen Demo Example:</span>
              <span className="italic text-slate-700">Citing 2024 test metrics after a 2026 version has superseded them.</span>
            </div>
          </div>

          {/* UNSUPPORTED */}
          <div className="bg-white rounded-2xl border border-purple-200 p-5 shadow-xs space-y-3">
            <div className="flex items-center justify-between">
              <span className="inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold bg-purple-50 text-purple-800 border-purple-200">
                UNSUPPORTED
              </span>
              <span className="text-xs text-purple-600 font-semibold">Missing Evidence</span>
            </div>
            <h4 className="font-bold text-slate-900 text-sm">Empirical Claim Without Proof</h4>
            <p className="text-xs text-slate-600 leading-relaxed">
              A clearly identifiable factual or performance statement that lacks any approved evidence in the registry. <em>Important: Unsupported does not mean false—it means unevidenced.</em>
            </p>
            <div className="bg-purple-50/50 p-3 rounded-lg border border-purple-100 text-xs">
              <span className="font-semibold text-purple-900 block">Lumen Demo Example:</span>
              <span className="italic text-slate-700">"Lumen bulbs last 50,000 hours and reduce maintenance costs by 40%."</span>
            </div>
          </div>

          {/* UNVERIFIABLE */}
          <div className="bg-white rounded-2xl border border-slate-300 p-5 shadow-xs space-y-3">
            <div className="flex items-center justify-between">
              <span className="inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold bg-slate-100 text-slate-700 border-slate-200">
                UNVERIFIABLE
              </span>
              <span className="text-xs text-slate-500 font-semibold">Vague / Subjective</span>
            </div>
            <h4 className="font-bold text-slate-900 text-sm">Ambiguous Marketing Hyperbole</h4>
            <p className="text-xs text-slate-600 leading-relaxed">
              Subjective or aspirational statements that cannot be mapped to an empirical standard. <em>Important: Unverifiable does not mean contradicted—it means objectively untestable.</em>
            </p>
            <div className="bg-slate-50 p-3 rounded-lg border border-slate-200 text-xs">
              <span className="font-semibold text-slate-900 block">Lumen Demo Example:</span>
              <span className="italic text-slate-700">"Lumen is the best choice for a brighter future."</span>
            </div>
          </div>

          {/* Summary / Revision-Level Card */}
          <div className="bg-indigo-50/60 rounded-2xl border border-indigo-200 p-5 shadow-xs space-y-3">
            <div className="flex items-center justify-between">
              <span className="inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold bg-indigo-100 text-indigo-800 border-indigo-200">
                REVISION VERDICT
              </span>
              <span className="text-xs text-indigo-600 font-semibold">Rollup Status</span>
            </div>
            <h4 className="font-bold text-slate-900 text-sm">Overall Revision Evaluation</h4>
            <p className="text-xs text-slate-600 leading-relaxed">
              The revision verdict consolidates all lane findings:
            </p>
            <ul className="text-xs text-slate-700 space-y-1">
              <li>• <strong className="text-emerald-700">CORRECT:</strong> All claims verified with no violations.</li>
              <li>• <strong className="text-rose-700">NEEDS_REVIEW:</strong> Any contradicted or outdated claims.</li>
              <li>• <strong className="text-indigo-700">MIXED:</strong> Partially verified claims requiring revision.</li>
            </ul>
          </div>
        </div>
      </section>

      {/* Section E: Explain What Output Judges Should Expect */}
      <section id="outputs" className="space-y-6">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-xl bg-indigo-100 text-indigo-700">
            <ClipboardList className="w-6 h-6" />
          </div>
          <div>
            <span className="text-xs font-bold text-indigo-600 uppercase tracking-widest">Section E</span>
            <h2 className="text-2xl font-bold text-slate-900 tracking-tight">Expected Review Outputs</h2>
          </div>
        </div>

        <p className="text-sm text-slate-600 max-w-3xl">
          When submitting copy to BrandProof, judges will observe concrete, structured governance outputs across the application:
        </p>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
          <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs space-y-2">
            <h4 className="font-bold text-slate-900 flex items-center gap-2">
              <Target className="w-4 h-4 text-indigo-600" />
              1. Highlighted Claim Spans
            </h4>
            <p className="text-xs text-slate-600 leading-relaxed">
              Every identified claim is outlined with color-coded underlines directly on the text (green for Correct, red for Contradicted, purple for Unsupported, slate for Unverifiable).
            </p>
          </div>

          <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs space-y-2">
            <h4 className="font-bold text-slate-900 flex items-center gap-2">
              <FileCheck2 className="w-4 h-4 text-indigo-600" />
              2. Evidence Comparison Cards
            </h4>
            <p className="text-xs text-slate-600 leading-relaxed">
              Displays the exact submitted claim side-by-side with the registered approved fact, showing measured values, authorized limits, and required qualifiers.
            </p>
          </div>

          <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs space-y-2">
            <h4 className="font-bold text-slate-900 flex items-center gap-2">
              <Lightbulb className="w-4 h-4 text-indigo-600" />
              3. Actionable Remediations
            </h4>
            <p className="text-xs text-slate-600 leading-relaxed">
              Provides plain-language guidance explaining the failure reason and suggested phrasing replacements that comply with active brand rules.
            </p>
          </div>

          <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs space-y-2">
            <h4 className="font-bold text-slate-900 flex items-center gap-2">
              <History className="w-4 h-4 text-indigo-600" />
              4. Multi-Revision Audit Trail
            </h4>
            <p className="text-xs text-slate-600 leading-relaxed">
              Revision dropdown tracks every editorial cycle (Revision 1 &rarr; Revision 2), recording author timestamps and verdict progression without data loss.
            </p>
          </div>

          <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs space-y-2">
            <h4 className="font-bold text-slate-900 flex items-center gap-2">
              <Scale className="w-4 h-4 text-indigo-600" />
              5. Dispute &amp; Resolution Decisions
            </h4>
            <p className="text-xs text-slate-600 leading-relaxed">
              Formal audit records showing creator justification notes and reviewer binding decisions (Uphold / Override) with immutable timestamps.
            </p>
          </div>

          <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs space-y-2">
            <h4 className="font-bold text-slate-900 flex items-center gap-2">
              <HeartPulse className="w-4 h-4 text-indigo-600" />
              6. Guideline Health Intelligence
            </h4>
            <p className="text-xs text-slate-600 leading-relaxed">
              Proactive alerts highlighting conflicting policy rules, circular phrase constraints, or guidelines with disproportionately high dispute rates.
            </p>
          </div>

          <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs space-y-2">
            <h4 className="font-bold text-slate-900 flex items-center gap-2">
              <BellRing className="w-4 h-4 text-indigo-600" />
              7. FactWatch Expiration Trackers
            </h4>
            <p className="text-xs text-slate-600 leading-relaxed">
              Derived lists of expiring, expired, and superseded facts with direct counts of published marketing assets that may now contain stale information.
            </p>
          </div>

          <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs space-y-2">
            <h4 className="font-bold text-slate-900 flex items-center gap-2">
              <ImageIcon className="w-4 h-4 text-indigo-600" />
              8. Visual Asset Compliance
            </h4>
            <p className="text-xs text-slate-600 leading-relaxed">
              Deterministic inspections of marketing imagery: color extraction, WCAG contrast ratio checks, image dimensions, format validation, and logo aspect ratio.
            </p>
          </div>
        </div>
      </section>

      {/* Section F: Judge Quick-Start Walkthrough */}
      <section id="quick-start" className="space-y-6">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-xl bg-indigo-100 text-indigo-700">
            <Zap className="w-6 h-6" />
          </div>
          <div>
            <span className="text-xs font-bold text-indigo-600 uppercase tracking-widest">Section F</span>
            <h2 className="text-2xl font-bold text-slate-900 tracking-tight">Judge Quick-Start Walkthrough</h2>
          </div>
        </div>

        <p className="text-sm text-slate-600 max-w-3xl">
          Follow this 5-minute recommended evaluation sequence to experience all major features:
        </p>

        {/* Step-by-Step Flow Cards */}
        <div className="space-y-4">
          {/* Step 1 */}
          <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
            <div className="flex items-start gap-4">
              <div className="w-8 h-8 rounded-full bg-indigo-600 text-white font-bold flex items-center justify-center shrink-0 text-sm">
                1
              </div>
              <div>
                <h4 className="font-bold text-slate-900 text-base">Select Your Persona</h4>
                <p className="text-xs text-slate-500 mt-1">
                  Click the <strong>Role Switcher</strong> in the top-right navbar. Switch between <strong>Admin</strong>, <strong>Creator</strong>, and <strong>Reviewer</strong>.
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2 shrink-0">
              {DEMO_PRESETS.map((p) => (
                <button
                  key={p.role}
                  onClick={() => quickLogin(p.role)}
                  className={`px-3 py-1.5 rounded-lg text-xs font-semibold capitalize transition cursor-pointer ${
                    role === p.role ? 'bg-indigo-600 text-white shadow-xs' : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
                  }`}
                >
                  {p.role}
                </button>
              ))}
            </div>
          </div>

          {/* Step 2 */}
          <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
            <div className="flex items-start gap-4">
              <div className="w-8 h-8 rounded-full bg-indigo-600 text-white font-bold flex items-center justify-center shrink-0 text-sm">
                2
              </div>
              <div>
                <h4 className="font-bold text-slate-900 text-base">Inspect the Knowledge Base</h4>
                <p className="text-xs text-slate-500 mt-1">
                  View the active brand guidelines and registered approved facts for our synthetic brand, <strong>Lumen Smart Lighting</strong>.
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2 shrink-0">
              <Link to="/guidelines" className="px-3 py-1.5 rounded-lg text-xs font-semibold bg-indigo-50 text-indigo-700 hover:bg-indigo-100">
                Guidelines &rarr;
              </Link>
              <Link to="/facts" className="px-3 py-1.5 rounded-lg text-xs font-semibold bg-indigo-50 text-indigo-700 hover:bg-indigo-100">
                Approved Facts &rarr;
              </Link>
            </div>
          </div>

          {/* Step 3 */}
          <div className="bg-white rounded-2xl border-2 border-indigo-500/30 bg-indigo-50/20 p-6 shadow-xs flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
            <div className="flex items-start gap-4">
              <div className="w-8 h-8 rounded-full bg-indigo-600 text-white font-bold flex items-center justify-center shrink-0 text-sm">
                3
              </div>
              <div>
                <h4 className="font-bold text-slate-900 text-base">Test the Review Engine (6 Preloaded Scenarios)</h4>
                <p className="text-xs text-slate-600 mt-1">
                  Go to <strong>Submit Copy</strong>. Use the 6 quick-scenario buttons (e.g. <em>60% energy savings</em> vs <em>80% contradictory claim</em>) and click <strong>Submit Copy for Review</strong>.
                </p>
              </div>
            </div>
            <Link
              to="/submit"
              className="px-4 py-2 rounded-xl text-xs font-bold bg-indigo-600 text-white hover:bg-indigo-700 shadow-xs shrink-0"
            >
              Open Copy Editor &rarr;
            </Link>
          </div>

          {/* Step 4 */}
          <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
            <div className="flex items-start gap-4">
              <div className="w-8 h-8 rounded-full bg-indigo-600 text-white font-bold flex items-center justify-center shrink-0 text-sm">
                4
              </div>
              <div>
                <h4 className="font-bold text-slate-900 text-base">Test Recheck &amp; Revision Loop</h4>
                <p className="text-xs text-slate-500 mt-1">
                  On the review result page, click <strong>Edit &amp; Recheck Copy</strong>. Adjust the text to compliant phrasing and verify that <strong>Revision 2</strong> is generated while preserving <strong>Revision 1</strong>.
                </p>
              </div>
            </div>
            <Link to="/submissions" className="px-3 py-1.5 rounded-lg text-xs font-semibold bg-slate-100 text-slate-700 hover:bg-slate-200 shrink-0">
              Submissions History &rarr;
            </Link>
          </div>

          {/* Step 5 */}
          <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
            <div className="flex items-start gap-4">
              <div className="w-8 h-8 rounded-full bg-indigo-600 text-white font-bold flex items-center justify-center shrink-0 text-sm">
                5
              </div>
              <div>
                <h4 className="font-bold text-slate-900 text-base">Raise &amp; Resolve a Dispute</h4>
                <p className="text-xs text-slate-500 mt-1">
                  As <strong>Creator</strong>, dispute a finding on a submission. Then switch to <strong>Reviewer</strong> and visit <strong>Disputes</strong> to uphold or override it.
                </p>
              </div>
            </div>
            <Link to="/disputes" className="px-3 py-1.5 rounded-lg text-xs font-semibold bg-slate-100 text-slate-700 hover:bg-slate-200 shrink-0">
              Disputes Queue &rarr;
            </Link>
          </div>

          {/* Step 6 */}
          <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
            <div className="flex items-start gap-4">
              <div className="w-8 h-8 rounded-full bg-indigo-600 text-white font-bold flex items-center justify-center shrink-0 text-sm">
                6
              </div>
              <div>
                <h4 className="font-bold text-slate-900 text-base">Explore Admin Intelligence</h4>
                <p className="text-xs text-slate-500 mt-1">
                  Switch to <strong>Admin</strong> to test <strong>Guideline Health</strong>, <strong>FactWatch</strong>, <strong>Visual Compliance</strong>, and <strong>Governance Analytics</strong>.
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2 shrink-0">
              <Link to="/guideline-health" className="px-2.5 py-1.5 rounded-lg text-xs font-semibold bg-slate-100 text-slate-700 hover:bg-slate-200">
                Health
              </Link>
              <Link to="/factwatch" className="px-2.5 py-1.5 rounded-lg text-xs font-semibold bg-slate-100 text-slate-700 hover:bg-slate-200">
                FactWatch
              </Link>
              <Link to="/visual" className="px-2.5 py-1.5 rounded-lg text-xs font-semibold bg-slate-100 text-slate-700 hover:bg-slate-200">
                Visual
              </Link>
              <Link to="/analytics" className="px-2.5 py-1.5 rounded-lg text-xs font-semibold bg-slate-100 text-slate-700 hover:bg-slate-200">
                Analytics
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Section G: Lumen Demo Brand Explanation */}
      <section id="lumen-demo" className="space-y-6">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-xl bg-indigo-100 text-indigo-700">
            <Building2 className="w-6 h-6" />
          </div>
          <div>
            <span className="text-xs font-bold text-indigo-600 uppercase tracking-widest">Section G</span>
            <h2 className="text-2xl font-bold text-slate-900 tracking-tight">The Synthetic Lumen Demo Brand</h2>
          </div>
        </div>

        <div className="bg-amber-50/70 border border-amber-200 rounded-2xl p-6 space-y-4">
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
            <div className="flex items-center gap-2 text-amber-800 font-bold text-sm">
              <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0" />
              Synthetic Demo Data Notice
            </div>
            <button
              type="button"
              onClick={handleSeed}
              disabled={seeding}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-amber-600 hover:bg-amber-700 disabled:bg-slate-300 text-white text-xs font-semibold shadow-xs transition cursor-pointer self-start sm:self-auto"
            >
              <Sparkles className="w-3.5 h-3.5" />
              {seeding ? 'Seeding Demo Data...' : 'Reset / Re-Seed Demo Data'}
            </button>
          </div>

          {seedStatus && (
            <div className={`p-3 rounded-lg text-xs font-medium flex items-center gap-2 ${
              seedStatus.type === 'success'
                ? 'bg-emerald-50 border border-emerald-200 text-emerald-800'
                : 'bg-rose-50 border border-rose-200 text-rose-800'
            }`}>
              {seedStatus.type === 'success' ? (
                <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
              ) : (
                <AlertTriangle className="w-4 h-4 text-rose-600 shrink-0" />
              )}
              <span>{seedStatus.message}</span>
            </div>
          )}

          <p className="text-xs text-amber-900/90 leading-relaxed">
            <strong>Lumen Smart Lighting</strong> is a synthetic demonstration brand pre-populated in the BrandProof database for the <strong>CodeNexus India 2026 Hackathon</strong>. All guidelines, facts, review submissions, and open dispute records are synthetic sample data designed to stress-test the three-lane governance engine.
          </p>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 pt-2">
            <div className="bg-white p-3.5 rounded-xl border border-amber-200/60 shadow-2xs space-y-1">
              <span className="text-[10px] font-bold uppercase tracking-wider text-amber-700">Approved Fact #1</span>
              <h5 className="font-bold text-slate-900 text-xs">Energy Savings Spec</h5>
              <p className="text-[11px] text-slate-600 leading-snug">
                <strong>Value:</strong> Up to 60% in laboratory tests.<br />
                <strong>Constraint:</strong> Requires qualifier <em>&quot;in laboratory tests&quot;</em>.
              </p>
            </div>

            <div className="bg-white p-3.5 rounded-xl border border-amber-200/60 shadow-2xs space-y-1">
              <span className="text-[10px] font-bold uppercase tracking-wider text-amber-700">Approved Fact #2</span>
              <h5 className="font-bold text-slate-900 text-xs">Bulb Lifespan Spec</h5>
              <p className="text-[11px] text-slate-600 leading-snug">
                <strong>Value:</strong> 25,000 hours under standard residential usage.<br />
                <strong>Operator:</strong> &gt;= 25000 hours.
              </p>
            </div>

            <div className="bg-white p-3.5 rounded-xl border border-amber-200/60 shadow-2xs space-y-1">
              <span className="text-[10px] font-bold uppercase tracking-wider text-amber-700">Approved Guideline #1</span>
              <h5 className="font-bold text-slate-900 text-xs">Warranty Terminology</h5>
              <p className="text-[11px] text-slate-600 leading-snug">
                <strong>Value:</strong> 3-year standard limited warranty.<br />
                <strong>Prohibited:</strong> <em>&quot;lifetime warranty&quot;</em>.
              </p>
            </div>

            <div className="bg-white p-3.5 rounded-xl border border-amber-200/60 shadow-2xs space-y-1">
              <span className="text-[10px] font-bold uppercase tracking-wider text-amber-700">Human Review Dispute #1</span>
              <h5 className="font-bold text-slate-900 text-xs">Quantum Mesh Claim</h5>
              <p className="text-[11px] text-slate-600 leading-snug">
                <strong>Status:</strong> Active Open in <Link to="/disputes" className="text-indigo-600 font-bold underline">/disputes</Link>.<br />
                <strong>Creator Reason:</strong> Thread radio architecture IEEE exception.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Bottom Banner */}
      <section className="bg-white rounded-3xl p-8 border border-slate-200 shadow-sm text-center space-y-4">
        <h3 className="text-2xl font-bold text-slate-900">Ready to Explore the Platform?</h3>
        <p className="text-sm text-slate-600 max-w-xl mx-auto">
          Start by submitting a sample marketing copy or exploring the approved guidelines and empirical facts.
        </p>
        <div className="flex flex-wrap items-center justify-center gap-3 pt-2">
          <Link
            to="/submit"
            className="px-6 py-2.5 rounded-xl bg-indigo-600 text-white font-bold text-sm hover:bg-indigo-700 transition shadow-xs"
          >
            Open Review Engine
          </Link>
          <Link
            to="/guidelines"
            className="px-6 py-2.5 rounded-xl bg-slate-100 text-slate-700 font-semibold text-sm hover:bg-slate-200 transition"
          >
            View Brand Guidelines
          </Link>
        </div>
      </section>
    </div>
  );
}
