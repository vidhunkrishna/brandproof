import React from 'react';
import { BrowserRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import Navbar from './components/Navbar';
import HowItWorksPage from './pages/HowItWorksPage';
import GuidelinesPage from './pages/GuidelinesPage';
import FactsPage from './pages/FactsPage';
import DocumentImportPage from './pages/DocumentImportPage';
import SubmitReviewPage from './pages/SubmitReviewPage';
import ReviewResultPage from './pages/ReviewResultPage';
import SubmissionHistoryPage from './pages/SubmissionHistoryPage';
import DisputesPage from './pages/DisputesPage';
import GuidelineHealthPage from './pages/GuidelineHealthPage';
import FactWatchPage from './pages/FactWatchPage';
import VisualCompliancePage from './pages/VisualCompliancePage';
import AnalyticsPage from './pages/AnalyticsPage';

function AppLayout() {
  const { loading } = useAuth();
  const location = useLocation();
  const isPublicRoute = location.pathname === '/' || location.pathname === '/how-it-works';

  if (loading && !isPublicRoute) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center text-slate-500 font-sans">
        <div className="flex items-center gap-3 bg-white px-6 py-4 rounded-xl border border-slate-200 shadow-sm">
          <div className="w-5 h-5 border-2 border-indigo-600 border-t-transparent rounded-full animate-spin"></div>
          <span className="text-sm font-medium text-slate-700">Connecting to BrandProof...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 flex flex-col font-sans">
      <Navbar />
      <main className="flex-1 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 w-full">
        <Routes>
          <Route path="/" element={<HowItWorksPage />} />
          <Route path="/how-it-works" element={<HowItWorksPage />} />
          <Route path="/guidelines" element={<GuidelinesPage />} />
          <Route path="/facts" element={<FactsPage />} />
          <Route path="/import" element={<DocumentImportPage />} />
          <Route path="/submit" element={<SubmitReviewPage />} />
          <Route path="/submissions" element={<SubmissionHistoryPage />} />
          <Route path="/reviews/:submissionId" element={<ReviewResultPage />} />
          <Route path="/disputes" element={<DisputesPage />} />
          <Route path="/disputes/:disputeId" element={<DisputesPage />} />
          <Route path="/guideline-health" element={<GuidelineHealthPage />} />
          <Route path="/factwatch" element={<FactWatchPage />} />
          <Route path="/visual" element={<VisualCompliancePage />} />
          <Route path="/analytics" element={<AnalyticsPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>
      <footer className="border-t border-slate-200 py-6 bg-white text-center text-xs text-slate-500">
        BrandProof &bull; Evidence Before Approval &bull; CodeNexus India 2026 Hackathon
      </footer>
    </div>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <AppLayout />
      </BrowserRouter>
    </AuthProvider>
  );
}
