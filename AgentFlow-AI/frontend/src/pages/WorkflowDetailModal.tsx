import React, { useEffect, useState } from 'react';
import {
  X,
  FileCode2,
  ListOrdered,
  RotateCw,
} from 'lucide-react';
import { api } from '../api/client';
import type { WorkflowRunResponse } from '../api/client';
import { StatusBadge } from '../components/StatusBadge';

interface WorkflowDetailModalProps {
  runId: number | null;
  onClose: () => void;
}

export const WorkflowDetailModal: React.FC<WorkflowDetailModalProps> = ({ runId, onClose }) => {
  const [workflow, setWorkflow] = useState<WorkflowRunResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [viewTab, setViewTab] = useState<'timeline' | 'json'>('timeline');

  useEffect(() => {
    if (!runId) return;
    const fetchDetail = async () => {
      setLoading(true);
      setError(null);
      try {
        const data = await api.getWorkflowDetail(runId);
        setWorkflow(data);
      } catch (err: any) {
        setError(err.message || 'Failed to fetch workflow details');
      } finally {
        setLoading(false);
      }
    };
    fetchDetail();
  }, [runId]);

  if (!runId) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-xs">
      <div className="bg-white rounded-2xl border border-slate-200 shadow-2xl w-full max-w-4xl max-h-[90vh] flex flex-col overflow-hidden animate-fade-in">
        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between bg-slate-50/50">
          <div className="flex items-center gap-3">
            <span className="font-mono text-sm font-bold text-slate-800">Workflow #{runId}</span>
            {workflow && <StatusBadge status={workflow.status} size="sm" />}
          </div>
          <button
            onClick={onClose}
            className="p-1.5 text-slate-400 hover:text-slate-700 rounded-lg hover:bg-slate-100 cursor-pointer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Body */}
        <div className="p-6 overflow-y-auto flex-1 space-y-6">
          {loading ? (
            <div className="py-16 text-center text-slate-400">
              <RotateCw className="w-6 h-6 animate-spin mx-auto text-indigo-500 mb-2" />
              <span>Retrieving execution audit...</span>
            </div>
          ) : error ? (
            <div className="p-4 bg-rose-50 border border-rose-200 text-rose-700 rounded-xl text-xs">
              {error}
            </div>
          ) : workflow ? (
            <>
              {/* Metadata Overview */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <div className="bg-slate-50 p-3 rounded-xl border border-slate-100 text-xs">
                  <span className="text-slate-400 block text-[11px]">Duration</span>
                  <span className="font-bold text-slate-800 text-sm">
                    {workflow.duration_seconds !== null && workflow.duration_seconds !== undefined
                      ? `${workflow.duration_seconds}s`
                      : '-'}
                  </span>
                </div>
                <div className="bg-slate-50 p-3 rounded-xl border border-slate-100 text-xs">
                  <span className="text-slate-400 block text-[11px]">Requires Approval</span>
                  <span className="font-bold text-slate-800 text-sm">
                    {workflow.plan?.requires_approval ? 'Yes (Sensitive)' : 'No'}
                  </span>
                </div>
                <div className="bg-slate-50 p-3 rounded-xl border border-slate-100 text-xs">
                  <span className="text-slate-400 block text-[11px]">Started At</span>
                  <span className="font-bold text-slate-800 text-sm truncate block">
                    {workflow.created_at ? new Date(workflow.created_at).toLocaleTimeString() : '-'}
                  </span>
                </div>
                <div className="bg-slate-50 p-3 rounded-xl border border-slate-100 text-xs">
                  <span className="text-slate-400 block text-[11px]">Completed At</span>
                  <span className="font-bold text-slate-800 text-sm truncate block">
                    {workflow.completed_at ? new Date(workflow.completed_at).toLocaleTimeString() : '-'}
                  </span>
                </div>
              </div>

              {/* Goal */}
              <div className="p-4 bg-slate-50 rounded-xl border border-slate-100 space-y-1">
                <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                  Original User Goal
                </span>
                <p className="text-sm font-semibold text-slate-900">{workflow.goal}</p>
                {workflow.plan?.interpretation && (
                  <p className="text-xs text-slate-600 mt-2 italic">
                    Interpretation: {workflow.plan.interpretation}
                  </p>
                )}
              </div>

              {/* View Switcher Tabs */}
              <div className="flex items-center gap-2 border-b border-slate-200 pb-2">
                <button
                  onClick={() => setViewTab('timeline')}
                  className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-lg cursor-pointer ${
                    viewTab === 'timeline'
                      ? 'bg-indigo-50 text-indigo-700'
                      : 'text-slate-500 hover:text-slate-800'
                  }`}
                >
                  <ListOrdered className="w-3.5 h-3.5" />
                  <span>Execution Timeline</span>
                </button>
                <button
                  onClick={() => setViewTab('json')}
                  className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-lg cursor-pointer ${
                    viewTab === 'json'
                      ? 'bg-indigo-50 text-indigo-700'
                      : 'text-slate-500 hover:text-slate-800'
                  }`}
                >
                  <FileCode2 className="w-3.5 h-3.5" />
                  <span>Audit JSON</span>
                </button>
              </div>

              {viewTab === 'timeline' ? (
                <div className="space-y-3">
                  {workflow.results && workflow.results.length > 0 ? (
                    workflow.results.map((step) => (
                      <div
                        key={step.step_id}
                        className="p-4 rounded-xl border border-slate-200 bg-white shadow-2xs space-y-3"
                      >
                        <div className="flex items-center justify-between text-xs">
                          <div className="flex items-center gap-2">
                            <span className="w-5 h-5 rounded-full bg-slate-100 text-slate-700 font-bold flex items-center justify-center text-[11px]">
                              {step.step_id}
                            </span>
                            <span className="font-semibold text-slate-900">{step.agent}</span>
                          </div>
                          <StatusBadge status={step.status} size="sm" />
                        </div>

                        <p className="text-xs text-slate-600">{step.description}</p>

                        {/* Step Result Output Preview */}
                        {step.result && (
                          <div className="p-3 bg-slate-50 rounded-lg border border-slate-100 text-xs font-mono overflow-x-auto text-slate-700">
                            <pre className="whitespace-pre-wrap">{JSON.stringify(step.result, null, 2)}</pre>
                          </div>
                        )}
                      </div>
                    ))
                  ) : (
                    <div className="py-6 text-center text-xs text-slate-400">
                      No step results recorded.
                    </div>
                  )}
                </div>
              ) : (
                <div className="p-4 bg-slate-900 text-emerald-400 rounded-xl text-xs font-mono overflow-x-auto max-h-96">
                  <pre>{JSON.stringify(workflow, null, 2)}</pre>
                </div>
              )}
            </>
          ) : null}
        </div>
      </div>
    </div>
  );
};
