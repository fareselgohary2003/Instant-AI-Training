import React, { useEffect, useState } from 'react';
import {
  CheckCircle2,
  AlertCircle,
  Clock,
  ShieldAlert,
  ArrowRight,
  TrendingUp,
  Cpu,
  Play,
  RotateCw,
} from 'lucide-react';
import { api } from '../api/client';
import type { AnalyticsData, WorkflowRunResponse } from '../api/client';
import { StatusBadge } from '../components/StatusBadge';
import type { PageId } from '../components/Layout';

interface OverviewPageProps {
  onNavigate: (page: PageId, workflowId?: number) => void;
  onSelectWorkflow: (runId: number) => void;
}

export const OverviewPage: React.FC<OverviewPageProps> = ({ onNavigate, onSelectWorkflow }) => {
  const [analytics, setAnalytics] = useState<AnalyticsData | null>(null);
  const [recentRuns, setRecentRuns] = useState<WorkflowRunResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [analyticsData, historyData] = await Promise.all([
        api.getAnalytics(),
        api.getHistory({ limit: 6 }),
      ]);
      setAnalytics(analyticsData);
      setRecentRuns(historyData.items || []);
    } catch (err: any) {
      setError(err.message || 'Failed to load overview data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-slate-900 tracking-tight">System Overview</h2>
          <p className="text-sm text-slate-500 mt-1">
            Real-time status of multi-agent tasks, active workflows, and platform health.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={loadData}
            disabled={loading}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-white border border-slate-200 text-slate-700 hover:bg-slate-50 text-xs font-medium rounded-lg shadow-2xs transition-colors cursor-pointer"
          >
            <RotateCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            <span>Refresh</span>
          </button>
          <button
            onClick={() => onNavigate('workspace')}
            className="flex items-center gap-1.5 px-4 py-1.5 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-medium rounded-lg shadow-sm transition-colors cursor-pointer"
          >
            <Play className="w-3.5 h-3.5" />
            <span>Launch Task</span>
          </button>
        </div>
      </div>

      {error && (
        <div className="p-4 bg-rose-50 border border-rose-200 text-rose-800 rounded-xl text-sm flex items-center justify-between">
          <div className="flex items-center gap-2">
            <AlertCircle className="w-4 h-4 text-rose-600" />
            <span>{error}</span>
          </div>
          <button onClick={loadData} className="text-xs font-semibold underline hover:text-rose-900">
            Try again
          </button>
        </div>
      )}

      {/* KPI Stats Grid */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        {/* Total Workflows */}
        <div className="bg-white p-4 rounded-xl border border-slate-200/80 shadow-2xs">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-500">Total Runs</span>
            <div className="w-7 h-7 rounded-lg bg-slate-100 flex items-center justify-center text-slate-600">
              <Cpu className="w-4 h-4" />
            </div>
          </div>
          <div className="text-2xl font-bold text-slate-900 mt-2">
            {analytics ? analytics.total_workflows : '-'}
          </div>
          <div className="text-[11px] text-slate-400 mt-1">Recorded executions</div>
        </div>

        {/* Completed */}
        <div className="bg-white p-4 rounded-xl border border-slate-200/80 shadow-2xs">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-500">Completed</span>
            <div className="w-7 h-7 rounded-lg bg-emerald-50 flex items-center justify-center text-emerald-600">
              <CheckCircle2 className="w-4 h-4" />
            </div>
          </div>
          <div className="text-2xl font-bold text-emerald-700 mt-2">
            {analytics ? analytics.completed : '-'}
          </div>
          <div className="text-[11px] text-slate-400 mt-1">
            {analytics ? `${analytics.success_rate_percent}% success rate` : ''}
          </div>
        </div>

        {/* Awaiting Approval */}
        <div className="bg-white p-4 rounded-xl border border-slate-200/80 shadow-2xs">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-500">Awaiting Approval</span>
            <div className="w-7 h-7 rounded-lg bg-amber-50 flex items-center justify-center text-amber-600">
              <ShieldAlert className="w-4 h-4" />
            </div>
          </div>
          <div className="text-2xl font-bold text-amber-700 mt-2">
            {analytics ? analytics.awaiting_approval : '-'}
          </div>
          <div className="text-[11px] text-slate-400 mt-1">Protected actions</div>
        </div>

        {/* Failed */}
        <div className="bg-white p-4 rounded-xl border border-slate-200/80 shadow-2xs">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-500">Failed</span>
            <div className="w-7 h-7 rounded-lg bg-rose-50 flex items-center justify-center text-rose-600">
              <AlertCircle className="w-4 h-4" />
            </div>
          </div>
          <div className="text-2xl font-bold text-rose-700 mt-2">
            {analytics ? analytics.failed : '-'}
          </div>
          <div className="text-[11px] text-slate-400 mt-1">Errors captured</div>
        </div>

        {/* Running / In Flight */}
        <div className="bg-white p-4 rounded-xl border border-slate-200/80 shadow-2xs">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-500">In Flight</span>
            <div className="w-7 h-7 rounded-lg bg-blue-50 flex items-center justify-center text-blue-600">
              <Clock className="w-4 h-4" />
            </div>
          </div>
          <div className="text-2xl font-bold text-blue-700 mt-2">
            {analytics ? analytics.running : '-'}
          </div>
          <div className="text-[11px] text-slate-400 mt-1">Active jobs</div>
        </div>

        {/* Average Duration */}
        <div className="bg-white p-4 rounded-xl border border-slate-200/80 shadow-2xs">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-500">Avg Duration</span>
            <div className="w-7 h-7 rounded-lg bg-indigo-50 flex items-center justify-center text-indigo-600">
              <TrendingUp className="w-4 h-4" />
            </div>
          </div>
          <div className="text-2xl font-bold text-slate-900 mt-2">
            {analytics ? `${analytics.avg_duration_seconds}s` : '-'}
          </div>
          <div className="text-[11px] text-slate-400 mt-1">Measured runtime</div>
        </div>
      </div>

      {/* Two Column Layout: Quick Launcher & Agent Breakdown */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Quick Launch Card */}
        <div className="lg:col-span-2 bg-gradient-to-br from-indigo-900 to-slate-900 text-white rounded-2xl p-6 shadow-md relative overflow-hidden flex flex-col justify-between">
          <div className="relative z-10">
            <div className="inline-flex items-center gap-2 px-3 py-1 bg-indigo-800/80 border border-indigo-700/60 rounded-full text-xs font-semibold text-indigo-200 mb-3">
              <span>Enterprise AI Supervisor</span>
            </div>
            <h3 className="text-xl font-bold text-white tracking-tight">
              Orchestrate Intelligent Multi-Agent Workflows
            </h3>
            <p className="text-sm text-slate-300 mt-2 max-w-xl">
              Submit complex goals in plain English. The Supervisor decomposes tasks, validates tools, coordinates specialized agents, and pauses for human verification before sensitive actions.
            </p>
          </div>

          <div className="mt-6 flex flex-wrap items-center gap-3 relative z-10">
            <button
              onClick={() => onNavigate('workspace')}
              className="flex items-center gap-2 bg-indigo-500 hover:bg-indigo-600 text-white text-sm font-semibold px-4 py-2.5 rounded-lg shadow-sm transition-all cursor-pointer"
            >
              <span>Open Task Workspace</span>
              <ArrowRight className="w-4 h-4" />
            </button>
            <button
              onClick={() => onNavigate('agents')}
              className="flex items-center gap-2 bg-white/10 hover:bg-white/15 text-white text-sm font-semibold px-4 py-2.5 rounded-lg border border-white/20 transition-all cursor-pointer"
            >
              <span>View Registered Agents (8)</span>
            </button>
          </div>
        </div>

        {/* Agent Distribution */}
        <div className="bg-white rounded-2xl border border-slate-200/80 p-5 shadow-2xs flex flex-col justify-between">
          <div>
            <h3 className="text-sm font-semibold text-slate-900">Agent Utilization</h3>
            <p className="text-xs text-slate-500 mt-0.5">Execution count per registered agent</p>

            <div className="mt-4 space-y-3">
              {analytics && analytics.agent_usage.length > 0 ? (
                analytics.agent_usage.map((item) => (
                  <div key={item.agent} className="space-y-1">
                    <div className="flex items-center justify-between text-xs">
                      <span className="font-medium text-slate-700">{item.agent}</span>
                      <span className="text-slate-500 font-semibold">{item.count} executions</span>
                    </div>
                    <div className="w-full bg-slate-100 rounded-full h-2">
                      <div
                        className="bg-indigo-600 h-2 rounded-full"
                        style={{
                          width: `${Math.min(100, (item.count / Math.max(1, analytics.total_workflows)) * 100)}%`,
                        }}
                      />
                    </div>
                  </div>
                ))
              ) : (
                <div className="py-8 text-center text-xs text-slate-400">
                  No step executions recorded yet. Launch your first task!
                </div>
              )}
            </div>
          </div>

          <div className="pt-4 border-t border-slate-100 mt-4">
            <button
              onClick={() => onNavigate('analytics')}
              className="w-full text-center text-xs font-semibold text-indigo-600 hover:text-indigo-800 cursor-pointer"
            >
              View Detailed Analytics →
            </button>
          </div>
        </div>
      </div>

      {/* Recent Executions Table */}
      <div className="bg-white rounded-2xl border border-slate-200/80 shadow-2xs overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between">
          <div>
            <h3 className="text-sm font-semibold text-slate-900">Recent Workflow Executions</h3>
            <p className="text-xs text-slate-500 mt-0.5">Direct from persistent SQLite database</p>
          </div>
          <button
            onClick={() => onNavigate('workflows')}
            className="text-xs font-semibold text-indigo-600 hover:text-indigo-800 flex items-center gap-1 cursor-pointer"
          >
            <span>View All History</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50/80 text-slate-500 font-medium border-b border-slate-100">
              <tr>
                <th className="px-6 py-3">ID</th>
                <th className="px-6 py-3">User Goal</th>
                <th className="px-6 py-3">Status</th>
                <th className="px-6 py-3">Steps</th>
                <th className="px-6 py-3">Duration</th>
                <th className="px-6 py-3">Created</th>
                <th className="px-6 py-3 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {recentRuns.length > 0 ? (
                recentRuns.map((run) => (
                  <tr key={run.run_id} className="hover:bg-slate-50/60 transition-colors">
                    <td className="px-6 py-3.5 font-mono text-slate-500">#{run.run_id}</td>
                    <td className="px-6 py-3.5 max-w-md truncate font-medium text-slate-900">
                      {run.goal}
                    </td>
                    <td className="px-6 py-3.5">
                      <StatusBadge status={run.status} size="sm" />
                    </td>
                    <td className="px-6 py-3.5 text-slate-600">
                      {run.results ? run.results.length : (run.plan?.steps?.length || 0)} steps
                    </td>
                    <td className="px-6 py-3.5 text-slate-600">
                      {run.duration_seconds !== null && run.duration_seconds !== undefined
                        ? `${run.duration_seconds}s`
                        : '-'}
                    </td>
                    <td className="px-6 py-3.5 text-slate-500">
                      {run.created_at ? new Date(run.created_at).toLocaleTimeString() : '-'}
                    </td>
                    <td className="px-6 py-3.5 text-right">
                      <button
                        onClick={() => onSelectWorkflow(run.run_id)}
                        className="text-indigo-600 hover:text-indigo-800 font-semibold cursor-pointer"
                      >
                        Inspect
                      </button>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={7} className="px-6 py-8 text-center text-slate-400">
                    No workflow history found. Run a task from the Task Workspace.
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
