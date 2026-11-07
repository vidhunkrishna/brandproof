import React, { useState } from 'react';
import { NavLink, Link, useLocation } from 'react-router-dom';
import { useAuth, DEMO_PRESETS } from '../contexts/AuthContext';
import { 
  ShieldCheck, 
  BookOpen, 
  CheckCircle, 
  FileUp, 
  Send,
  ClipboardList,
  Scale,
  HeartPulse,
  BellRing,
  Image,
  ChartNoAxesCombined,
  AlertCircle,
  LogOut, 
  Building2,
  HelpCircle,
  Menu,
  X
} from 'lucide-react';

export default function Navbar() {
  const { user, role, activeOrganization, error, quickLogin, logout } = useAuth();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const location = useLocation();
  const isHowItWorksActive = location.pathname === '/' || location.pathname === '/how-it-works';

  const linkClass = ({ isActive }) =>
    `flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium transition cursor-pointer shrink-0 ${
      isActive
        ? 'bg-indigo-50 text-indigo-700 font-semibold shadow-xs'
        : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
    }`;

  const mobileLinkClass = ({ isActive }) =>
    `flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition ${
      isActive
        ? 'bg-indigo-50 text-indigo-700 font-semibold'
        : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
    }`;

  // 10 Admin links split into two rows of 5
  const adminTopRow = [
    { to: '/guidelines', label: 'Guidelines', icon: BookOpen },
    { to: '/facts', label: 'Approved Facts', icon: CheckCircle },
    { to: '/import', label: 'Document Import', icon: FileUp },
    { to: '/submit', label: 'Submit Copy', icon: Send },
    { to: '/submissions', label: 'Reviews', icon: ClipboardList },
  ];

  const adminBottomRow = [
    { to: '/disputes', label: 'Disputes', icon: Scale },
    { to: '/guideline-health', label: 'Guideline Health', icon: HeartPulse },
    { to: '/factwatch', label: 'FactWatch', icon: BellRing },
    { to: '/visual', label: 'Visual checks', icon: Image },
    { to: '/analytics', label: 'Analytics', icon: ChartNoAxesCombined },
  ];

  // Creator links (single row)
  const creatorLinks = [
    { to: '/guidelines', label: 'Guidelines', icon: BookOpen },
    { to: '/facts', label: 'Approved Facts', icon: CheckCircle },
    { to: '/import', label: 'Document Import', icon: FileUp },
    { to: '/submit', label: 'Submit Copy', icon: Send },
    { to: '/submissions', label: 'Reviews', icon: ClipboardList },
    { to: '/disputes', label: 'Disputes', icon: Scale },
    { to: '/visual', label: 'Visual checks', icon: Image },
  ];

  // Reviewer / Default links (single row)
  const reviewerLinks = [
    { to: '/guidelines', label: 'Guidelines', icon: BookOpen },
    { to: '/facts', label: 'Approved Facts', icon: CheckCircle },
    { to: '/import', label: 'Document Import', icon: FileUp },
    { to: '/submissions', label: 'Reviews', icon: ClipboardList },
    { to: '/disputes', label: 'Disputes', icon: Scale },
    { to: '/visual', label: 'Visual checks', icon: Image },
  ];

  return (
    <header className="border-b border-slate-200 bg-white sticky top-0 z-40 shadow-xs">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className={`flex items-center justify-between gap-4 ${role === 'admin' ? 'min-h-[72px] py-2' : 'h-16'}`}>
          {/* Logo & Brand */}
          <div className="flex items-center gap-6 xl:gap-8 shrink-0">
            <Link to="/" className="flex items-center gap-2.5 group" title="BrandProof Product Overview">
              <div className="bg-indigo-600 text-white p-2 rounded-lg flex items-center justify-center shadow-xs group-hover:bg-indigo-700 transition">
                <ShieldCheck className="w-5 h-5" />
              </div>
              <div>
                <span className="font-bold text-lg text-slate-900 tracking-tight block leading-tight">
                  BrandProof
                </span>
                <span className="text-[10px] text-slate-400 font-medium tracking-wide block uppercase">
                  Evidence Before Approval
                </span>
              </div>
            </Link>
          </div>

          {/* Center Navigation Container */}
          <nav className="hidden lg:flex flex-col justify-center gap-1.5 my-1 shrink-0" aria-label="Main Navigation">
            {role === 'admin' ? (
              <div className="flex flex-col gap-1">
                {/* Top Row: First 5 existing admin navigation links */}
                <div className="flex items-center gap-1">
                  {adminTopRow.map(({ to, label, icon: Icon }) => (
                    <NavLink key={to} to={to} className={linkClass}>
                      <Icon className="w-3.5 h-3.5" />
                      <span>{label}</span>
                    </NavLink>
                  ))}
                </div>

                {/* Bottom Row: Remaining 5 existing admin navigation links */}
                <div className="flex items-center gap-1 pt-1 border-t border-slate-100">
                  {adminBottomRow.map(({ to, label, icon: Icon }) => (
                    <NavLink key={to} to={to} className={linkClass}>
                      <Icon className="w-3.5 h-3.5" />
                      <span>{label}</span>
                    </NavLink>
                  ))}
                </div>
              </div>
            ) : role === 'creator' ? (
              <div className="flex items-center gap-1">
                {creatorLinks.map(({ to, label, icon: Icon }) => (
                  <NavLink key={to} to={to} className={linkClass}>
                    <Icon className="w-3.5 h-3.5" />
                    <span>{label}</span>
                  </NavLink>
                ))}
              </div>
            ) : (
              <div className="flex items-center gap-1">
                {reviewerLinks.map(({ to, label, icon: Icon }) => (
                  <NavLink key={to} to={to} className={linkClass}>
                    <Icon className="w-3.5 h-3.5" />
                    <span>{label}</span>
                  </NavLink>
                ))}
              </div>
            )}
          </nav>

          {/* Right Header: "How It Works" + Tenant + Role Switcher */}
          <div className="flex items-center gap-2.5 shrink-0">
            {/* Dedicated "How It Works" Guide Link (Shared across all roles & visitors) */}
            <NavLink
              to="/"
              className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition cursor-pointer border ${
                isHowItWorksActive
                  ? 'bg-indigo-600 text-white border-indigo-600 shadow-xs'
                  : 'bg-indigo-50 text-indigo-700 border-indigo-200 hover:bg-indigo-100 hover:border-indigo-300 shadow-2xs'
              }`}
              title="Judge & Product Guide (Home)"
            >
              <HelpCircle className={`w-3.5 h-3.5 ${isHowItWorksActive ? 'text-white' : 'text-indigo-500'}`} />
              <span>How It Works</span>
            </NavLink>

            {!user && error && (
              <div role="alert" className="hidden max-w-56 items-center gap-1.5 rounded-md border border-amber-200 bg-amber-50 px-2.5 py-1 text-xs text-amber-800 xl:flex" title={error}>
                <AlertCircle className="h-3.5 w-3.5 shrink-0" />
                <span className="truncate">{error}</span>
              </div>
            )}

            {activeOrganization && (
              <div className="hidden xl:flex items-center gap-1.5 px-2.5 py-1 bg-slate-100 rounded-md border border-slate-200 text-xs text-slate-700 font-medium">
                <Building2 className="w-3.5 h-3.5 text-slate-500" />
                <span className="max-w-[100px] truncate">{activeOrganization.name}</span>
              </div>
            )}

            {/* Quick Role Switcher for Hackathon Judges */}
            <div className="flex items-center bg-slate-100 p-1 rounded-lg border border-slate-200">
              <span className="text-[11px] font-semibold text-slate-400 px-1.5 uppercase hidden sm:inline">Role:</span>
              {DEMO_PRESETS.map((p) => {
                const isActiveRole = role === p.role;
                return (
                  <button
                    key={p.role}
                    onClick={() => quickLogin(p.role)}
                    className={`px-2.5 py-1 rounded text-xs font-medium capitalize transition cursor-pointer ${
                      isActiveRole
                        ? 'bg-white text-indigo-700 shadow-xs font-semibold'
                        : 'text-slate-600 hover:text-slate-900'
                    }`}
                    title={`Switch active persona to ${p.label}`}
                  >
                    {p.role}
                  </button>
                );
              })}
            </div>

            {/* User profile dropdown / signout */}
            {user && (
              <div className="flex items-center gap-2 pl-1 border-l border-slate-200">
                <button
                  onClick={() => logout()}
                  className="p-1.5 text-slate-400 hover:text-rose-600 rounded-md hover:bg-slate-100 transition cursor-pointer"
                  title="Sign Out"
                >
                  <LogOut className="w-4 h-4" />
                </button>
              </div>
            )}

            {/* Mobile menu toggle */}
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="lg:hidden p-1.5 text-slate-600 hover:text-slate-900 hover:bg-slate-100 rounded-lg transition cursor-pointer"
              aria-label="Toggle navigation menu"
            >
              {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
            </button>
          </div>
        </div>

        {/* Responsive Mobile / Tablet Drawer */}
        {mobileMenuOpen && (
          <div className="lg:hidden py-4 border-t border-slate-200 space-y-3">
            <div className="flex items-center justify-between px-3">
              <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">
                Navigation Menu ({role || 'Guest'})
              </span>
              <NavLink
                to="/"
                onClick={() => setMobileMenuOpen(false)}
                className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-semibold ${
                  isHowItWorksActive
                    ? 'bg-indigo-600 text-white'
                    : 'bg-indigo-50 text-indigo-700'
                }`}
              >
                <HelpCircle className="w-3.5 h-3.5" />
                <span>Product Guide</span>
              </NavLink>
            </div>
            <div className="grid grid-cols-2 gap-1 px-1">
              {role === 'admin' ? (
                <>
                  <div className="col-span-2 text-[10px] font-bold text-indigo-600 uppercase tracking-wider px-2 pt-1">
                    Core Operations (Row 1)
                  </div>
                  {adminTopRow.map(({ to, label, icon: Icon }) => (
                    <NavLink
                      key={to}
                      to={to}
                      onClick={() => setMobileMenuOpen(false)}
                      className={mobileLinkClass}
                    >
                      <Icon className="w-4 h-4" />
                      <span>{label}</span>
                    </NavLink>
                  ))}

                  <div className="col-span-2 text-[10px] font-bold text-indigo-600 uppercase tracking-wider px-2 pt-2 border-t border-slate-100 mt-1">
                    Governance &amp; Analytics (Row 2)
                  </div>
                  {adminBottomRow.map(({ to, label, icon: Icon }) => (
                    <NavLink
                      key={to}
                      to={to}
                      onClick={() => setMobileMenuOpen(false)}
                      className={mobileLinkClass}
                    >
                      <Icon className="w-4 h-4" />
                      <span>{label}</span>
                    </NavLink>
                  ))}
                </>
              ) : role === 'creator' ? (
                creatorLinks.map(({ to, label, icon: Icon }) => (
                  <NavLink
                    key={to}
                    to={to}
                    onClick={() => setMobileMenuOpen(false)}
                    className={mobileLinkClass}
                  >
                    <Icon className="w-4 h-4" />
                    <span>{label}</span>
                  </NavLink>
                ))
              ) : (
                reviewerLinks.map(({ to, label, icon: Icon }) => (
                  <NavLink
                    key={to}
                    to={to}
                    onClick={() => setMobileMenuOpen(false)}
                    className={mobileLinkClass}
                  >
                    <Icon className="w-4 h-4" />
                    <span>{label}</span>
                  </NavLink>
                ))
              )}
            </div>
          </div>
        )}
      </div>
    </header>
  );
}
