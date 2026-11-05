import React, { useState } from 'react';
import apiClient from '../api/client';
import { useAuth } from '../contexts/AuthContext';
import { 
  FileUp, 
  FileText, 
  CheckCircle2, 
  AlertTriangle, 
  Clock, 
  ShieldCheck, 
  RefreshCw,
  ArrowRight,
  ExternalLink
} from 'lucide-react';

export default function DocumentImportPage() {
  const { role } = useAuth();
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState(null);
  const [error, setError] = useState(null);
  const [approvingId, setApprovingId] = useState(null);
  const [approvedIds, setApprovedIds] = useState(new Set());

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      const ext = file.name.substring(file.name.lastIndexOf('.')).toLowerCase();
      if (ext !== '.pdf' && ext !== '.docx') {
        setError('Only .pdf and .docx files are supported.');
        setSelectedFile(null);
        return;
      }
      setError(null);
      setSelectedFile(file);
    }
  };

  const handleUpload = async (e) => {
    e.preventDefault();
    if (!selectedFile) return;

    setUploading(true);
    setError(null);
    setUploadResult(null);

    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
      const res = await apiClient.post('/api/v1/documents/import', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      setUploadResult(res.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Document processing failed.');
    } finally {
      setUploading(false);
    }
  };

  const handleApproveCandidate = async (candidateId) => {
    setApprovingId(candidateId);
    try {
      await apiClient.put(`/api/v1/guidelines/${candidateId}/approve`);
      setApprovedIds((prev) => new Set([...prev, candidateId]));
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to approve candidate rule');
    } finally {
      setApprovingId(null);
    }
  };

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      {/* Page Header */}
      <div>
        <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Brand Guideline Document Import</h1>
        <p className="text-sm text-slate-500 mt-1">
          Upload text-based PDF or Word (.docx) brand manuals to automatically extract and stage candidate governance rules.
        </p>
      </div>

      {/* Upload Dropzone Card */}
      <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-xs space-y-4">
        <form onSubmit={handleUpload} className="space-y-4">
          <div className="border-2 border-dashed border-slate-200 hover:border-indigo-400 rounded-xl p-8 text-center transition bg-slate-50/50">
            <FileUp className="w-10 h-10 text-indigo-600 mx-auto mb-3" />
            <div className="text-sm font-semibold text-slate-800">
              {selectedFile ? (
                <span className="text-indigo-600 font-bold">{selectedFile.name} ({(selectedFile.size / 1024).toFixed(1)} KB)</span>
              ) : (
                <span>Click to select or drag and drop brand guide document</span>
              )}
            </div>
            <p className="text-xs text-slate-400 mt-1">
              Supports text-based .PDF and .DOCX files up to 10 MB. (Scanned image OCR not in MVP)
            </p>

            <input
              type="file"
              accept=".pdf,.docx"
              onChange={handleFileChange}
              className="mt-4 block mx-auto text-xs text-slate-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-xs file:font-semibold file:bg-indigo-50 file:text-indigo-700 hover:file:bg-indigo-100 cursor-pointer"
            />
          </div>

          {error && (
            <div className="p-4 bg-rose-50 border border-rose-200 text-rose-800 rounded-lg text-xs flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-rose-600 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <div className="flex items-center justify-end gap-3">
            <button
              type="submit"
              disabled={!selectedFile || uploading}
              className="inline-flex items-center gap-2 px-5 py-2.5 bg-indigo-600 hover:bg-indigo-700 disabled:bg-slate-300 text-white rounded-lg text-sm font-medium transition shadow-xs cursor-pointer disabled:cursor-not-allowed"
            >
              {uploading ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin" />
                  Parsing & Staging Rules...
                </>
              ) : (
                <>
                  <FileText className="w-4 h-4" />
                  Extract Candidate Rules
                </>
              )}
            </button>
          </div>
        </form>
      </div>

      {/* Extracted Candidates Staging Area */}
      {uploadResult && (
        <div className="bg-white rounded-xl border border-slate-200 shadow-xs overflow-hidden space-y-4 p-6">
          <div className="flex items-center justify-between pb-4 border-b border-slate-100">
            <div>
              <h2 className="text-lg font-bold text-slate-900">Extracted Candidate Rules Staging Queue</h2>
              <p className="text-xs text-slate-500">
                Source: <span className="font-semibold text-slate-700">{uploadResult.filename}</span> &bull; {uploadResult.total_extracted} rule candidates staged in DRAFT status
              </p>
            </div>
            <span className="text-xs px-2.5 py-1 bg-amber-50 text-amber-700 rounded-full border border-amber-200 font-medium">
              Requires Admin Approval
            </span>
          </div>

          {uploadResult.candidate_guidelines.length === 0 ? (
            <div className="py-8 text-center text-slate-500 text-sm">
              No normative policy rules (containing mandatory constraints like "must", "prohibited", etc.) were found in this document.
            </div>
          ) : (
            <div className="divide-y divide-slate-100">
              {uploadResult.candidate_guidelines.map((candidate) => {
                const isApproved = approvedIds.has(candidate.id);
                return (
                  <div key={candidate.id} className="py-4 flex flex-col md:flex-row md:items-start justify-between gap-4">
                    <div className="space-y-1.5 flex-1">
                      <div className="flex items-center gap-2">
                        <span className="font-semibold text-slate-900 text-sm">{candidate.title}</span>
                        <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded bg-slate-100 text-slate-600">
                          {candidate.category}
                        </span>
                        {isApproved ? (
                          <span className="inline-flex items-center gap-1 text-[11px] font-medium text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-200">
                            <CheckCircle2 className="w-3 h-3 text-emerald-600" />
                            Approved & Active
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1 text-[11px] font-medium text-amber-700 bg-amber-50 px-2 py-0.5 rounded-full border border-amber-200">
                            <Clock className="w-3 h-3 text-amber-600" />
                            Candidate Draft
                          </span>
                        )}
                      </div>

                      <p className="text-xs text-slate-700 bg-slate-50 p-3 rounded-lg border border-slate-100 leading-relaxed">
                        {candidate.rule_text}
                      </p>

                      <div className="flex items-center gap-4 text-[11px] text-slate-400">
                        <span>Extracted from: {candidate.source}</span>
                        {candidate.prohibited_phrases && candidate.prohibited_phrases.length > 0 && (
                          <span className="text-rose-600 font-medium">
                            Forbidden: {candidate.prohibited_phrases.join(', ')}
                          </span>
                        )}
                      </div>
                    </div>

                    <div className="shrink-0 flex items-center gap-2 self-start md:self-center">
                      {isApproved ? (
                        <span className="text-xs text-emerald-600 font-semibold px-3 py-1.5 bg-emerald-50 rounded-lg">
                          Activated
                        </span>
                      ) : role === 'admin' ? (
                        <button
                          onClick={() => handleApproveCandidate(candidate.id)}
                          disabled={approvingId === candidate.id}
                          className="px-3.5 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-xs font-semibold transition shadow-xs cursor-pointer flex items-center gap-1"
                        >
                          <CheckCircle2 className="w-3.5 h-3.5" />
                          {approvingId === candidate.id ? 'Approving...' : 'Approve & Activate'}
                        </button>
                      ) : (
                        <span className="text-xs text-slate-400 italic">
                          Switch to Admin role to approve
                        </span>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

