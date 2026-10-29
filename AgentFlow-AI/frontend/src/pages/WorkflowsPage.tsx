import React, { useEffect, useState } from 'react';
import {
  Search,
  Filter,
  RotateCw,
  AlertCircle,
} from 'lucide-react';
import { api } from '../api/client';
import type { WorkflowRunResponse } from '../api/client';
import { StatusBadge } from '../components/StatusBadge';

interface WorkflowsPageProps {
  onSelectWorkflow: (runId: number) => void;
}

export const WorkflowsPage: React.FC<WorkflowsPageProps> = ({ onSelectWorkflow }) => {
  const [workflows, setWorkflows] = useState<WorkflowRunResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [actionLoading, setActionLoading] = useState<number | null>(null);

  const fetchWorkflows = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getHistory({
        limit: 50,
        status: statusFilter || undefined,
        search: search.trim() || undefined,
      });
      setWorkflows(data.items || []);
    } catch (err: any) {
      setError(err.message || 'Failed to load workflow history');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchWorkflows();
  }, [statusFilter]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    fetchWorkflows();
  };

  const handleCancel = async (runId: number) => {
    setActionLoading(runId);
    try {
      await api.cancelWorkflow(runId);
      fetchWorkflows();
    } catch (err: any) {
      alert(`Could not cancel workflow: ${err.message}`);
    } finally {
      setActionLoading(null);
    }
  };

  const handleRetry = async (runId: number) => {
    setActionLoading(runId);
    try {
      await api.retryWorkflow(runId);
      fetchWorkflows();
    } catch (err: any) {
      alert(`Could not retry workflow: ${err.message}`);
    } finally {
      setActionLoading(null);
    }
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-slate-900 tracking-tight">Workflow Executions</h2>
          <p className="text-sm text-slate-500 mt-1">
            Historical audit log of all multi-agent plans, tool outputs, and execution metrics.
          </p>
        </div>
        <button
          onClick={fetchWorkflows}
          disabled={loading}
          className="flex items-center gap-1.5 px-3 py-1.5 bg-white border border-slate-200 text-slate-700 hover:bg-slate-50 text-xs font-medium rounded-lg shadow-2xs transition-colors cursor-pointer self-start sm:self-auto"
        >
          <RotateCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          <span>Refresh</span>
        </button>
      </div>

      {error && (
        <div className="p-4 bg-rose-50 border border-rose-200 text-rose-800 rounded-xl text-sm flex items-center justify-between">
          <div className="flex items-center gap-2">
            <AlertCircle className="w-4 h-4 text-rose-600" />
            <span>{error}</span>
          </div>
          <button onClick={fetchWorkflows} className="text-xs font-semibold underline hover:text-rose-900">
            Retry
          </button>
        </div>
      )}

      {/* Filter and Search Bar */}
      <div className="bg-white p-4 rounded-xl border border-slate-200/80 shadow-2xs flex flex-col sm:flex-row items-center justify-between gap-3">
        <form onSubmit={handleSearchSubmit} className="relative w-full sm:w-80">
          <Search className="w-4 h-4 absolute left-3 top-3 text-slate-400" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search by task goal..."
            className="w-full pl-9 pr-3 py-1.5 text-xs rounded-lg border border-slate-200 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-600"
          />
        </form>

        <div className="flex items-center gap-2 w-full sm:w-auto">
          <Filter className="w-4 h-4 text-slate-400 shrink-0" />
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="w-full sm:w-auto text-xs bg-white border border-slate-200 rounded-lg px-3 py-1.5 text-slate-700 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-600 cursor-pointer"
          >
            <option value="">All Statuses</option>
            <option value="completed">Completed</option>
            <option value="awaiting_approval">Awaiting Approval</option>
            <option value="running">Running / In Flight</option>
            <option value="failed">Failed</option>
            <option value="cancelled">Cancelled</option>
          </select>
        </div>
      </div>

      {/* Data Table */}
      <div className="bg-white rounded-2xl border border-slate-200/80 shadow-2xs overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50/80 text-slate-500 font-medium border-b border-slate-100">
              <tr>
                <th className="px-6 py-3">Run ID</th>
                <th className="px-6 py-3">Task Goal</th>
                <th className="px-6 py-3">Status</th>
                <th className="px-6 py-3">Steps</th>
                <th className="px-6 py-3">Duration</th>
                <th className="px-6 py-3">Created</th>
                <th className="px-6 py-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {loading ? (
                <tr>
                  <td colSpan={7} className="px-6 py-12 text-center text-slate-400">
                    <RotateCw className="w-5 h-5 animate-spin mx-auto text-indigo-500 mb-2" />
                    <span>Loading workflow records...</span>
                  </td>
                </tr>
              ) : workflows.length > 0 ? (
                workflows.map((run) => (
                  <tr key={run.run_id} className="hover:bg-slate-50/60 transition-colors">
                    <td className="px-6 py-4 font-mono font-semibold text-slate-600">
                      #{run.run_id}
                    </td>
                    <td className="px-6 py-4 max-w-sm truncate font-medium text-slate-900">
                      {run.goal}
                    </td>
                    <td className="px-6 py-4">
                      <StatusBadge status={run.status} size="sm" />
                    </td>
                    <td className="px-6 py-4 text-slate-600 font-medium">
                      {run.results ? run.results.length : (run.plan?.steps?.length || 0)} steps
                    </td>
                    <td className="px-6 py-4 text-slate-600">
                      {run.duration_seconds !== null && run.duration_seconds !== undefined
                        ? `${run.duration_seconds}s`
                        : '-'}
                    </td>
                    <td className="px-6 py-4 text-slate-500">
                      {run.created_at ? new Date(run.created_at).toLocaleString() : '-'}
                    </td>
                    <td className="px-6 py-4 text-right space-x-2">
                      <button
                        onClick={() => onSelectWorkflow(run.run_id)}
                        className="text-indigo-600 hover:text-indigo-800 font-semibold cursor-pointer"
                      >
                        Inspect
                      </button>

                      {/* Cancel action if running or awaiting approval */}
                      {(run.status === 'running' || run.status === 'awaiting_approval') && (
                        <button
                          onClick={() => handleCancel(run.run_id)}
                          disabled={actionLoading === run.run_id}
                          className="text-rose-600 hover:text-rose-800 font-semibold cursor-pointer ml-2"
                        >
                          Cancel
                        </button>
                      )}

                      {/* Retry action if failed */}
                      {(run.status === 'failed' || run.status === 'cancelled') && (
                        <button
                          onClick={() => handleRetry(run.run_id)}
                          disabled={actionLoading === run.run_id}
                          className="text-emerald-600 hover:text-emerald-800 font-semibold cursor-pointer ml-2"
                        >
                          Retry
                        </button>
                      )}
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={7} className="px-6 py-12 text-center text-slate-400">
                    No workflow runs match the criteria.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
