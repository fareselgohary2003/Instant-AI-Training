import React, { useEffect, useState } from 'react';
import { RotateCw, Info } from 'lucide-react';
import { api } from '../api/client';
import type { AnalyticsData } from '../api/client';

export const AnalyticsPage: React.FC = () => {
  const [data, setData] = useState<AnalyticsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchAnalytics = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.getAnalytics();
      setData(res);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch platform analytics');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAnalytics();
  }, []);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-slate-900 tracking-tight">Platform Analytics</h2>
          <p className="text-sm text-slate-500 mt-1">
            Audited execution performance, agent utilization, and workflow success rates.
          </p>
        </div>
        <button
          onClick={fetchAnalytics}
          disabled={loading}
          className="flex items-center gap-1.5 px-3 py-1.5 bg-white border border-slate-200 text-slate-700 hover:bg-slate-50 text-xs font-medium rounded-lg shadow-2xs transition-colors cursor-pointer self-start sm:self-auto"
        >
          <RotateCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          <span>Refresh</span>
        </button>
      </div>

      {/* Audit Notice */}
      <div className="p-3 bg-indigo-50/60 border border-indigo-100 rounded-xl text-xs text-indigo-900 flex items-center gap-2">
        <Info className="w-4 h-4 text-indigo-600 shrink-0" />
        <span>
          <strong>Data Integrity Guarantee:</strong> All charts and metrics reflect actual database records from SQLite persistence. No simulated tokens, costs, or mock events.
        </span>
      </div>

      {error && (
        <div className="p-4 bg-rose-50 border border-rose-200 text-rose-800 rounded-xl text-sm">
          {error}
        </div>
      )}

      {loading ? (
        <div className="bg-white p-16 rounded-2xl border border-slate-200 text-center text-slate-400">
          <RotateCw className="w-6 h-6 animate-spin mx-auto text-indigo-500 mb-2" />
          <span>Calculating performance statistics...</span>
        </div>
      ) : data ? (
        <>
          {/* Key Metrics Cards */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-2xs">
              <span className="text-xs font-semibold text-slate-400 block uppercase">
                Success Rate
              </span>
              <div className="text-3xl font-black text-emerald-600 mt-2">
                {data.success_rate_percent}%
              </div>
              <div className="w-full bg-slate-100 rounded-full h-1.5 mt-3">
                <div
                  className="bg-emerald-500 h-1.5 rounded-full"
                  style={{ width: `${data.success_rate_percent}%` }}
                />
              </div>
            </div>

            <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-2xs">
              <span className="text-xs font-semibold text-slate-400 block uppercase">
                Total Executions
              </span>
              <div className="text-3xl font-black text-slate-900 mt-2">
                {data.total_workflows}
              </div>
              <div className="text-[11px] text-slate-500 mt-3">
                {data.completed} completed • {data.failed} failed
              </div>
            </div>

            <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-2xs">
              <span className="text-xs font-semibold text-slate-400 block uppercase">
                Awaiting Approval
              </span>
              <div className="text-3xl font-black text-amber-600 mt-2">
                {data.awaiting_approval}
              </div>
              <div className="text-[11px] text-slate-500 mt-3">Protected side-effect checkpoints</div>
            </div>

            <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-2xs">
              <span className="text-xs font-semibold text-slate-400 block uppercase">
                Average Duration
              </span>
              <div className="text-3xl font-black text-indigo-600 mt-2">
                {data.avg_duration_seconds}s
              </div>
              <div className="text-[11px] text-slate-500 mt-3">Measured execution latency</div>
            </div>
          </div>

          {/* Agent Execution Distribution */}
          <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-2xs space-y-4">
            <div>
              <h3 className="text-sm font-bold text-slate-900">Agent Task Distribution</h3>
              <p className="text-xs text-slate-500 mt-0.5">
                Number of operations completed by each specialized worker
              </p>
            </div>

            <div className="space-y-3 pt-2">
              {data.agent_usage.length > 0 ? (
                data.agent_usage.map((agent) => {
                  const maxCount = Math.max(...data.agent_usage.map((a) => a.count), 1);
                  const percentage = Math.round((agent.count / maxCount) * 100);
                  return (
                    <div key={agent.agent} className="space-y-1">
                      <div className="flex items-center justify-between text-xs">
                        <span className="font-semibold text-slate-700">{agent.agent}</span>
                        <span className="text-slate-500 font-mono">
                          {agent.count} calls
                        </span>
                      </div>
                      <div className="w-full bg-slate-100 rounded-full h-2.5 overflow-hidden">
                        <div
                          className="bg-indigo-600 h-full rounded-full transition-all duration-500"
                          style={{ width: `${percentage}%` }}
                        />
                      </div>
                    </div>
                  );
                })
              ) : (
                <div className="py-8 text-center text-xs text-slate-400">
                  No step executions recorded yet.
                </div>
              )}
            </div>
          </div>

          {/* Daily Volume Breakdown */}
          <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-2xs space-y-4">
            <div>
              <h3 className="text-sm font-bold text-slate-900">Workflow Timeline & Daily Volume</h3>
              <p className="text-xs text-slate-500 mt-0.5">Execution volume aggregated by date</p>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-50 text-slate-500 font-medium border-b border-slate-100">
                  <tr>
                    <th className="px-4 py-2.5">Date</th>
                    <th className="px-4 py-2.5">Total Runs</th>
                    <th className="px-4 py-2.5">Completed</th>
                    <th className="px-4 py-2.5">Failed</th>
                    <th className="px-4 py-2.5">Success Rate</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {data.daily_volume.length > 0 ? (
                    data.daily_volume.map((row) => {
                      const rate =
                        row.count > 0 ? Math.round((row.completed / row.count) * 100) : 0;
                      return (
                        <tr key={row.date} className="hover:bg-slate-50">
                          <td className="px-4 py-3 font-mono text-slate-700">{row.date}</td>
                          <td className="px-4 py-3 font-semibold text-slate-900">{row.count}</td>
                          <td className="px-4 py-3 text-emerald-700 font-medium">
                            {row.completed}
                          </td>
                          <td className="px-4 py-3 text-rose-700 font-medium">{row.failed}</td>
                          <td className="px-4 py-3 font-semibold text-slate-700">{rate}%</td>
                        </tr>
                      );
                    })
                  ) : (
                    <tr>
                      <td colSpan={5} className="px-4 py-6 text-center text-slate-400">
                        No historical daily data available.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </>
      ) : null}
    </div>
  );
};
