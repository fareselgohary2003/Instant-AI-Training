import React, { useEffect, useState } from 'react';
import {
  ShieldAlert,
  CheckCircle2,
  XCircle,
  RotateCw,
} from 'lucide-react';
import { api } from '../api/client';
import type { ApprovalRequest } from '../api/client';
import { StatusBadge } from '../components/StatusBadge';

interface ApprovalsPageProps {
  onSelectWorkflow: (runId: number) => void;
  onRefreshApprovals: () => void;
}

export const ApprovalsPage: React.FC<ApprovalsPageProps> = ({
  onSelectWorkflow,
  onRefreshApprovals,
}) => {
  const [approvals, setApprovals] = useState<ApprovalRequest[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionLoading, setActionLoading] = useState<number | null>(null);
  const [decisionNotes, setDecisionNotes] = useState<Record<number, string>>({});
  const [feedback, setFeedback] = useState<string | null>(null);

  const fetchApprovals = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getApprovals();
      setApprovals(data);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch pending approvals');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchApprovals();
  }, []);

  const handleApprove = async (approvalId: number) => {
    setActionLoading(approvalId);
    setFeedback(null);
    try {
      const notes = decisionNotes[approvalId] || 'Approved by operator';
      const res = await api.approveAction(approvalId, notes);
      setFeedback(res.message);
      fetchApprovals();
      onRefreshApprovals();
    } catch (err: any) {
      alert(`Approval failed: ${err.message}`);
    } finally {
      setActionLoading(null);
    }
  };

  const handleReject = async (approvalId: number) => {
    setActionLoading(approvalId);
    setFeedback(null);
    try {
      const notes = decisionNotes[approvalId] || 'Rejected by operator';
      const res = await api.rejectAction(approvalId, notes);
      setFeedback(res.message);
      fetchApprovals();
      onRefreshApprovals();
    } catch (err: any) {
      alert(`Rejection failed: ${err.message}`);
    } finally {
      setActionLoading(null);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-slate-900 tracking-tight">
            Human-in-the-Loop Approvals
          </h2>
          <p className="text-sm text-slate-500 mt-1">
            Protected actions requiring explicit operator confirmation before execution.
          </p>
        </div>
        <button
          onClick={fetchApprovals}
          disabled={loading}
          className="flex items-center gap-1.5 px-3 py-1.5 bg-white border border-slate-200 text-slate-700 hover:bg-slate-50 text-xs font-medium rounded-lg shadow-2xs transition-colors cursor-pointer self-start sm:self-auto"
        >
          <RotateCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          <span>Refresh</span>
        </button>
      </div>

      {feedback && (
        <div className="p-4 bg-emerald-50 border border-emerald-200 text-emerald-800 rounded-xl text-sm flex items-center justify-between">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-600" />
            <span>{feedback}</span>
          </div>
          <button onClick={() => setFeedback(null)} className="text-xs font-semibold underline">
            Dismiss
          </button>
        </div>
      )}

      {error && (
        <div className="p-4 bg-rose-50 border border-rose-200 text-rose-800 rounded-xl text-sm">
          {error}
        </div>
      )}

      {/* Approvals List */}
      <div className="space-y-4">
        {loading ? (
          <div className="bg-white p-12 rounded-2xl border border-slate-200 text-center text-slate-400">
            <RotateCw className="w-6 h-6 animate-spin mx-auto text-indigo-500 mb-2" />
            <span>Checking pending requests...</span>
          </div>
        ) : approvals.length > 0 ? (
          approvals.map((req) => (
            <div
              key={req.id}
              className="bg-white rounded-2xl border border-amber-200/90 shadow-2xs p-6 space-y-4"
            >
              {/* Request Header */}
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 pb-4 border-b border-slate-100">
                <div className="flex items-center gap-3">
                  <div className="w-9 h-9 rounded-xl bg-amber-50 border border-amber-200 flex items-center justify-center text-amber-700">
                    <ShieldAlert className="w-5 h-5" />
                  </div>
                  <div>
                    <div className="font-bold text-sm text-slate-900">
                      Approval Request #{req.id} — {req.action_type}
                    </div>
                    <div className="text-xs text-slate-500">
                      Workflow Run #{req.run_id} • Step {req.step_id} • Requested {req.requested_at ? new Date(req.requested_at).toLocaleTimeString() : 'Recently'}
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <StatusBadge status={req.status} size="sm" />
                  <button
                    onClick={() => onSelectWorkflow(req.run_id)}
                    className="text-xs font-semibold text-indigo-600 hover:text-indigo-800 ml-2 cursor-pointer"
                  >
                    View Run →
                  </button>
                </div>
              </div>

              {/* Action Details & Preview */}
              <div className="space-y-2">
                <div className="text-xs font-semibold text-slate-700">Description:</div>
                <div className="text-xs text-slate-600 bg-slate-50 p-3 rounded-xl border border-slate-100">
                  {req.description}
                </div>

                {/* Specific Email Preview If Email Agent */}
                {req.parameters && (
                  <div className="mt-3 p-4 bg-slate-900 text-slate-200 rounded-xl text-xs space-y-2 font-mono">
                    <div className="text-slate-400 font-sans font-semibold text-[11px] uppercase tracking-wider pb-1 border-b border-slate-800">
                      Payload Preview (Protected Side-Effect)
                    </div>
                    {req.parameters.recipient && (
                      <div>
                        <span className="text-indigo-400">Recipient: </span>
                        <span>{req.parameters.recipient}</span>
                      </div>
                    )}
                    {req.parameters.subject && (
                      <div>
                        <span className="text-indigo-400">Subject: </span>
                        <span>{req.parameters.subject}</span>
                      </div>
                    )}
                    {req.parameters.body_preview && (
                      <div className="pt-1">
                        <span className="text-indigo-400 block mb-1">Body Preview:</span>
                        <div className="p-2 bg-slate-950 rounded text-slate-300 font-sans whitespace-pre-wrap">
                          {req.parameters.body_preview}
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>

              {/* Decision Section */}
              <div className="pt-4 border-t border-slate-100 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                <input
                  type="text"
                  placeholder="Optional decision notes / justification..."
                  value={decisionNotes[req.id] || ''}
                  onChange={(e) =>
                    setDecisionNotes({ ...decisionNotes, [req.id]: e.target.value })
                  }
                  className="text-xs bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 flex-1 max-w-md focus:outline-none focus:ring-2 focus:ring-indigo-500/20"
                />

                <div className="flex items-center gap-3 self-end sm:self-auto">
                  <button
                    onClick={() => handleReject(req.id)}
                    disabled={actionLoading === req.id}
                    className="flex items-center gap-1.5 px-4 py-2 bg-white border border-rose-200 text-rose-700 hover:bg-rose-50 text-xs font-semibold rounded-xl shadow-2xs transition-colors cursor-pointer"
                  >
                    <XCircle className="w-4 h-4" />
                    <span>Reject Action</span>
                  </button>
                  <button
                    onClick={() => handleApprove(req.id)}
                    disabled={actionLoading === req.id}
                    className="flex items-center gap-1.5 px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold rounded-xl shadow-2xs transition-colors cursor-pointer"
                  >
                    <CheckCircle2 className="w-4 h-4" />
                    <span>Approve & Authorize</span>
                  </button>
                </div>
              </div>
            </div>
          ))
        ) : (
          <div className="bg-white rounded-2xl border border-slate-200/80 p-12 text-center shadow-2xs">
            <div className="w-12 h-12 rounded-full bg-emerald-50 text-emerald-600 flex items-center justify-center mx-auto mb-3">
              <CheckCircle2 className="w-6 h-6" />
            </div>
            <h3 className="text-base font-bold text-slate-900">Zero Pending Approvals</h3>
            <p className="text-xs text-slate-500 max-w-sm mx-auto mt-1">
              All multi-agent actions have either executed cleanly or have already been authorized.
            </p>
          </div>
        )}
      </div>
    </div>
  );
};
