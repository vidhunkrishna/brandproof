import React from 'react';
import { NavLink } from 'react-router-dom';
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
  AlertCircle,
  LogOut, 
  Building2 
} from 'lucide-react';

export default function Navbar() {
  const { user, role, activeOrganization, error, quickLogin, logout } = useAuth();

  return (
    <header className="border-b border-slate-200 bg-white sticky top-0 z-40 shadow-xs">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo & Brand */}
          <div className="flex items-center gap-8">
            <div className="flex items-center gap-2.5">
              <div className="bg-indigo-600 text-white p-2 rounded-lg flex items-center justify-center shadow-xs">
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
            </div>

            {/* Navigation Links */}
            <nav className="hidden md:flex items-center gap-1">
              <NavLink
                to="/guidelines"
                className={({ isActive }) =>
                  `flex items-center gap-1.5 px-3 py-2 rounded-md text-sm font-medium transition ${
                    isActive
                      ? 'bg-indigo-50 text-indigo-700'
                      : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
                  }`
                }
              >
                <BookOpen className="w-4 h-4" />
                Guidelines
              </NavLink>

              <NavLink
                to="/facts"
                className={({ isActive }) =>
                  `flex items-center gap-1.5 px-3 py-2 rounded-md text-sm font-medium transition ${
                    isActive
                      ? 'bg-indigo-50 text-indigo-700'
                      : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
                  }`
                }
              >
                <CheckCircle className="w-4 h-4" />
                Approved Facts
              </NavLink>

              <NavLink
                to="/import"
                className={({ isActive }) =>
                  `flex items-center gap-1.5 px-3 py-2 rounded-md text-sm font-medium transition ${
                    isActive
                      ? 'bg-indigo-50 text-indigo-700'
                      : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
                  }`
                }
              >
                <FileUp className="w-4 h-4" />
                Document Import
              </NavLink>

              {(role === 'admin' || role === 'creator') && (
                <NavLink
                  to="/submit"
                  className={({ isActive }) =>
                    `flex items-center gap-1.5 px-3 py-2 rounded-md text-sm font-medium transition ${
                      isActive
                        ? 'bg-indigo-50 text-indigo-700'
                        : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
                    }`
                  }
                >
                  <Send className="w-4 h-4" />
                  Submit Copy
                </NavLink>
              )}

              <NavLink
                to="/submissions"
                className={({ isActive }) =>
                  `flex items-center gap-1.5 px-3 py-2 rounded-md text-sm font-medium transition ${
                    isActive
                      ? 'bg-indigo-50 text-indigo-700'
                      : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
                  }`
                }
              >
                <ClipboardList className="w-4 h-4" />
                Reviews
              </NavLink>
              <NavLink
                to="/disputes"
                className={({ isActive }) => `flex items-center gap-1.5 px-3 py-2 rounded-md text-sm font-medium transition ${isActive ? 'bg-indigo-50 text-indigo-700' : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'}`}
              >
                <Scale className="w-4 h-4" />
                Disputes
              </NavLink>
              {role === 'admin' && <NavLink to="/guideline-health" className={({ isActive }) => `flex items-center gap-1.5 px-3 py-2 rounded-md text-sm font-medium transition ${isActive ? 'bg-indigo-50 text-indigo-700' : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'}`}><HeartPulse className="w-4 h-4" />Guideline Health</NavLink>}
              {role === 'admin' && <NavLink to="/factwatch" className={({ isActive }) => `flex items-center gap-1.5 px-3 py-2 rounded-md text-sm font-medium transition ${isActive ? 'bg-indigo-50 text-indigo-700' : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'}`}><BellRing className="w-4 h-4" />FactWatch</NavLink>}
            </nav>
          </div>

          {/* Right Header: Tenant & Role Switcher */}
          <div className="flex items-center gap-3">
            {!user && error && (
              <div role="alert" className="hidden max-w-64 items-center gap-1.5 rounded-md border border-amber-200 bg-amber-50 px-2.5 py-1 text-xs text-amber-800 xl:flex" title={error}>
                <AlertCircle className="h-3.5 w-3.5 shrink-0" />
                <span className="truncate">{error}</span>
              </div>
            )}
            {activeOrganization && (
              <div className="hidden sm:flex items-center gap-1.5 px-2.5 py-1 bg-slate-100 rounded-md border border-slate-200 text-xs text-slate-700 font-medium">
                <Building2 className="w-3.5 h-3.5 text-slate-500" />
                <span>{activeOrganization.name}</span>
              </div>
            )}

            {/* Quick Role Switcher for Hackathon Judges */}
            <div className="flex items-center bg-slate-100 p-1 rounded-lg border border-slate-200">
              <span className="text-[11px] font-semibold text-slate-400 px-2 uppercase">Role:</span>
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
              <div className="flex items-center gap-2 pl-2 border-l border-slate-200">
                <button
                  onClick={() => logout()}
                  className="p-1.5 text-slate-400 hover:text-rose-600 rounded-md hover:bg-slate-100 transition"
                  title="Sign Out"
                >
                  <LogOut className="w-4 h-4" />
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  );
}

