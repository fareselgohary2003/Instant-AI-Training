import React, { useState } from 'react';
import {
  Play,
  RotateCw,
  Sparkles,
  AlertCircle,
  Clock,
  ShieldAlert,
  CloudSun,
  FileText,
  Mail,
  Search,
  Database,
  ExternalLink,
  Info,
} from 'lucide-react';
import { api } from '../api/client';
import type { WorkflowRunResponse } from '../api/client';
import { StatusBadge } from '../components/StatusBadge';

interface WorkspacePageProps {
  onSelectWorkflow: (runId: number) => void;
  onRefreshApprovals: () => void;
}

const EXAMPLE_TASKS = [
  {
    title: 'Multi-Agent Weather & Text Analysis',
    prompt: 'Get the current weather in Cairo and analyze this text: AI agents can plan and execute tasks.',
    icon: CloudSun,
  },
  {
    title: 'Text & Sentiment Analysis',
    prompt: 'Analyze this text for keywords, length, and sentiment: The engineering team delivered high reliability, impressive performance, and clean code.',
    icon: FileText,
  },
  {
    title: 'Web Research with Verified Sources',
    prompt: 'Search the web for latest breakthroughs in multi-agent autonomous AI systems and summarize findings.',
    icon: Search,
  },
  {
    title: 'Protected Email Notification (Approval Required)',
    prompt: 'Send an email to team@company.com with subject Deployment Completed and body Release v1.0 has been deployed to production successfully.',
    icon: Mail,
  },
  {
    title: 'Tabular Data Metric Analysis',
    prompt: 'Parse and analyze this tabular metrics CSV:\nTask,Agent,Duration\nWeather Check,weather_agent,1.2\nText Analysis,text_analysis,0.8\nEmail Notification,email_agent,0.5',
    icon: Database,
  },
];

export const WorkspacePage: React.FC<WorkspacePageProps> = ({
  onSelectWorkflow,
  onRefreshApprovals,
}) => {
  const [goal, setGoal] = useState('');
  const [running, setRunning] = useState(false);
  const [currentRun, setCurrentRun] = useState<WorkflowRunResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [approvalActionPending, setApprovalActionPending] = useState(false);

  const handleRun = async (taskGoal?: string) => {
    const targetGoal = (taskGoal !== undefined ? taskGoal : goal).trim();
    if (!targetGoal) {
      setError('Please enter a task or goal to execute.');
      return;
    }

    setRunning(true);
    setError(null);

    try {
      const response = await api.runWorkflow(targetGoal);
      setCurrentRun(response);
      onRefreshApprovals();
    } catch (err: any) {
      setError(err.message || 'Workflow execution failed');
    } finally {
      setRunning(false);
    }
  };

  const handleApprove = async (approvalId: number) => {
    setApprovalActionPending(true);
    try {
      const res = await api.approveAction(approvalId, 'Approved directly from Task Workspace.');
      // Refresh current run details
      if (res.run_id) {
        const updated = await api.getWorkflowDetail(res.run_id);
        setCurrentRun(updated);
      }
      onRefreshApprovals();
    } catch (err: any) {
      setError(err.message || 'Failed to approve action');
    } finally {
      setApprovalActionPending(false);
    }
  };

  const handleReject = async (approvalId: number) => {
    setApprovalActionPending(true);
    try {
      const res = await api.rejectAction(approvalId, 'Rejected from Task Workspace.');
      if (res.run_id) {
        const updated = await api.getWorkflowDetail(res.run_id);
        setCurrentRun(updated);
      }
      onRefreshApprovals();
    } catch (err: any) {
      setError(err.message || 'Failed to reject action');
    } finally {
      setApprovalActionPending(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-xl font-bold text-slate-900 tracking-tight">Task Workspace</h2>
        <p className="text-sm text-slate-500 mt-1">
          Submit goals in natural language. The AI Supervisor formulates a plan, validates tools, and coordinates multi-agent execution.
        </p>
      </div>

      {/* Input Form Card */}
      <div className="bg-white rounded-2xl border border-slate-200/90 p-5 shadow-2xs">
        <label htmlFor="goal-input" className="block text-xs font-semibold uppercase tracking-wider text-slate-500 mb-2">
          Natural Language Goal / Task
        </label>
        <div className="relative">
          <textarea
            id="goal-input"
            rows={3}
            value={goal}
            onChange={(e) => {
              setGoal(e.target.value);
              if (error) setError(null);
            }}
            placeholder="e.g., Get the current weather in Cairo and analyze this text: AI agents can plan and execute tasks."
            className="w-full rounded-xl border border-slate-300 p-3.5 text-sm text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-600 transition-all resize-none"
            disabled={running}
          />
        </div>

        {error && (
          <div className="mt-3 p-3 bg-rose-50 border border-rose-200 text-rose-700 text-xs rounded-lg flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <div className="mt-3 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
          <div className="text-xs text-slate-400">
            {goal.length > 0 ? `${goal.length} characters` : 'Press Run to execute multi-agent orchestration'}
          </div>
          <button
            onClick={() => handleRun()}
            disabled={running || !goal.trim()}
            className="flex items-center justify-center gap-2 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed text-white text-sm font-semibold px-5 py-2.5 rounded-xl shadow-sm transition-all cursor-pointer"
          >
            {running ? (
              <>
                <RotateCw className="w-4 h-4 animate-spin" />
                <span>Supervising & Executing...</span>
              </>
            ) : (
              <>
                <Play className="w-4 h-4" />
                <span>Execute Workflow</span>
              </>
            )}
          </button>
        </div>

        {/* Example Suggestions */}
        <div className="mt-5 pt-4 border-t border-slate-100">
          <div className="flex items-center gap-1.5 text-xs font-semibold text-slate-600 mb-2.5">
            <Sparkles className="w-3.5 h-3.5 text-indigo-500" />
            <span>Curated Example Tasks:</span>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2">
            {EXAMPLE_TASKS.map((example, idx) => {
              const Icon = example.icon;
              return (
                <button
                  key={idx}
                  onClick={() => {
                    setGoal(example.prompt);
                    handleRun(example.prompt);
                  }}
                  className="text-left p-2.5 bg-slate-50 hover:bg-indigo-50/60 border border-slate-200/70 hover:border-indigo-200 rounded-xl transition-all group cursor-pointer"
                >
                  <div className="flex items-center gap-2">
                    <div className="w-6 h-6 rounded-md bg-white flex items-center justify-center text-indigo-600 border border-slate-200/60 shadow-2xs group-hover:scale-105 transition-transform">
                      <Icon className="w-3.5 h-3.5" />
                    </div>
                    <span className="text-xs font-semibold text-slate-800 group-hover:text-indigo-900 truncate">
                      {example.title}
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-500 line-clamp-1 mt-1 pl-8">
                    {example.prompt}
                  </p>
                </button>
              );
            })}
          </div>
        </div>
      </div>

      {/* Execution Results View */}
      {currentRun && (
        <div className="space-y-6 animate-fade-in">
          {/* Execution Header Card */}
          <div className="bg-white rounded-2xl border border-slate-200/90 p-5 shadow-2xs">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 pb-4 border-b border-slate-100">
              <div className="flex items-center gap-3">
                <div className="font-mono text-xs font-semibold px-2.5 py-1 bg-slate-100 rounded-md text-slate-700">
                  Run #{currentRun.run_id}
                </div>
                <StatusBadge status={currentRun.status} />
                {currentRun.duration_seconds !== null && currentRun.duration_seconds !== undefined && (
                  <span className="text-xs text-slate-500 flex items-center gap-1 font-medium">
                    <Clock className="w-3.5 h-3.5 text-slate-400" />
                    {currentRun.duration_seconds}s
                  </span>
                )}
              </div>
              <button
                onClick={() => onSelectWorkflow(currentRun.run_id)}
                className="flex items-center gap-1 text-xs font-semibold text-indigo-600 hover:text-indigo-800 cursor-pointer"
              >
                <span>Inspect Database Record</span>
                <ExternalLink className="w-3.5 h-3.5" />
              </button>
            </div>

            {/* Goal & Interpretation */}
            <div className="mt-4 space-y-2">
              <div className="text-xs text-slate-400 font-medium">Goal Executed:</div>
              <div className="text-sm font-semibold text-slate-900">{currentRun.goal}</div>
              {currentRun.plan?.interpretation && (
                <div className="text-xs text-slate-600 bg-slate-50 p-3 rounded-xl border border-slate-200/60 flex items-start gap-2">
                  <Info className="w-4 h-4 text-indigo-500 shrink-0 mt-0.5" />
                  <span>{currentRun.plan.interpretation}</span>
                </div>
              )}
            </div>
          </div>

          {/* Planned Steps & Execution Results Timeline */}
          <div className="bg-white rounded-2xl border border-slate-200/90 p-5 shadow-2xs">
            <h3 className="text-sm font-bold text-slate-900 mb-4 flex items-center justify-between">
              <span>Step Execution Pipeline</span>
              <span className="text-xs font-medium text-slate-500">
                {currentRun.results.length} of {currentRun.plan?.steps?.length || currentRun.results.length} steps processed
              </span>
            </h3>

            <div className="space-y-4">
              {currentRun.results.map((step) => (
                <div
                  key={step.step_id}
                  className="rounded-xl border border-slate-200 p-4 bg-slate-50/50 hover:bg-slate-50 transition-colors"
                >
                  {/* Step Header */}
                  <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 pb-3 border-b border-slate-200/60">
                    <div className="flex items-center gap-2.5">
                      <span className="w-6 h-6 rounded-full bg-indigo-100 text-indigo-700 font-bold text-xs flex items-center justify-center">
                        {step.step_id}
                      </span>
                      <span className="font-semibold text-xs text-slate-900">
                        {step.agent}
                      </span>
                      <span className="text-xs text-slate-500 font-normal">
                        — {step.description}
                      </span>
                    </div>
                    <div className="flex items-center gap-3">
                      {step.duration_seconds !== null && step.duration_seconds !== undefined && (
                        <span className="text-[11px] text-slate-400">
                          {step.duration_seconds}s
                        </span>
                      )}
                      <StatusBadge status={step.status} size="sm" />
                    </div>
                  </div>

                  {/* Step Tool Output Formats */}
                  <div className="mt-3">
                    {/* WEATHER AGENT OUTPUT */}
                    {step.agent === 'weather_agent' && step.result && !step.result.error && (
                      <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-2xs">
                        <div className="flex items-center justify-between">
                          <div>
                            <div className="text-base font-bold text-slate-900">
                              {step.result.city}, {step.result.country}
                            </div>
                            <div className="text-xs text-slate-500">
                              Observed: {step.result.observed_at ? new Date(step.result.observed_at).toLocaleString() : 'Live'}
                            </div>
                          </div>
                          <div className="text-right">
                            <div className="text-2xl font-black text-indigo-600">
                              {step.result.temperature_c}°C
                            </div>
                            <div className="text-xs text-slate-500">
                              Feels like {step.result.feels_like_c}°C
                            </div>
                          </div>
                        </div>

                        <div className="mt-3 grid grid-cols-3 gap-2 text-center pt-3 border-t border-slate-100 text-xs">
                          <div>
                            <span className="text-slate-400 block text-[11px]">Conditions</span>
                            <span className="font-semibold text-slate-700">{step.result.conditions}</span>
                          </div>
                          <div>
                            <span className="text-slate-400 block text-[11px]">Humidity</span>
                            <span className="font-semibold text-slate-700">{step.result.humidity_percent}%</span>
                          </div>
                          <div>
                            <span className="text-slate-400 block text-[11px]">Wind Speed</span>
                            <span className="font-semibold text-slate-700">{step.result.wind_speed_kmh} km/h</span>
                          </div>
                        </div>
                      </div>
                    )}

                    {/* TEXT ANALYSIS AGENT OUTPUT */}
                    {step.agent === 'text_analysis_agent' && step.result && !step.result.error && (
                      <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-2xs space-y-3">
                        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-center">
                          <div className="bg-slate-50 p-2 rounded-lg border border-slate-100">
                            <span className="text-[11px] text-slate-400 block">Words</span>
                            <span className="text-base font-bold text-slate-800">{step.result.word_count}</span>
                          </div>
                          <div className="bg-slate-50 p-2 rounded-lg border border-slate-100">
                            <span className="text-[11px] text-slate-400 block">Characters</span>
                            <span className="text-base font-bold text-slate-800">{step.result.character_count}</span>
                          </div>
                          <div className="bg-slate-50 p-2 rounded-lg border border-slate-100">
                            <span className="text-[11px] text-slate-400 block">Sentences</span>
                            <span className="text-base font-bold text-slate-800">{step.result.sentence_count}</span>
                          </div>
                          <div className="bg-slate-50 p-2 rounded-lg border border-slate-100">
                            <span className="text-[11px] text-slate-400 block">Avg Word Length</span>
                            <span className="text-base font-bold text-slate-800">{step.result.average_word_length}</span>
                          </div>
                        </div>

                        {/* Keywords & Sentiment */}
                        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 pt-2">
                          <div className="flex items-center gap-1.5 flex-wrap">
                            <span className="text-xs text-slate-500 font-medium">Top Keywords:</span>
                            {step.result.keywords?.map((k: any) => (
                              <span
                                key={k.word}
                                className="px-2 py-0.5 bg-indigo-50 border border-indigo-100 text-indigo-700 rounded-md text-xs font-medium"
                              >
                                {k.word} ({k.frequency})
                              </span>
                            ))}
                          </div>
                          {step.result.deterministic_sentiment && (
                            <div className="text-xs flex items-center gap-2">
                              <span className="text-slate-500">Sentiment:</span>
                              <span
                                className={`font-semibold capitalize px-2 py-0.5 rounded-full text-xs ${
                                  step.result.deterministic_sentiment.label === 'positive'
                                    ? 'bg-emerald-100 text-emerald-800'
                                    : step.result.deterministic_sentiment.label === 'negative'
                                    ? 'bg-rose-100 text-rose-800'
                                    : 'bg-slate-100 text-slate-700'
                                }`}
                              >
                                {step.result.deterministic_sentiment.label}
                              </span>
                            </div>
                          )}
                        </div>
                      </div>
                    )}

                    {/* EMAIL AGENT OUTPUT & APPROVAL BANNER */}
                    {step.agent === 'email_agent' && (
                      <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-2xs space-y-3">
                        {step.status === 'awaiting_approval' && (
                          <div className="p-3 bg-amber-50 border border-amber-200 rounded-xl flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
                            <div className="flex items-start gap-2.5">
                              <ShieldAlert className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
                              <div>
                                <div className="text-xs font-bold text-amber-900">
                                  Approval Required for Email Transmission
                                </div>
                                <div className="text-xs text-amber-800 mt-0.5">
                                  Sending external email via SMTP is a protected operation. Review the preview below.
                                </div>
                              </div>
                            </div>
                            <div className="flex items-center gap-2 shrink-0">
                              <button
                                onClick={() => handleApprove(1)}
                                disabled={approvalActionPending}
                                className="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold rounded-lg shadow-xs cursor-pointer transition-colors"
                              >
                                Approve & Send
                              </button>
                              <button
                                onClick={() => handleReject(1)}
                                disabled={approvalActionPending}
                                className="px-3 py-1.5 bg-white border border-rose-200 text-rose-700 hover:bg-rose-50 text-xs font-semibold rounded-lg shadow-xs cursor-pointer transition-colors"
                              >
                                Reject
                              </button>
                            </div>
                          </div>
                        )}

                        {/* Email Details Preview */}
                        <div className="text-xs space-y-1.5 bg-slate-50 p-3 rounded-lg border border-slate-200/60 font-mono">
                          <div>
                            <span className="text-slate-400">Recipient: </span>
                            <span className="text-slate-900 font-semibold">{step.result?.preview?.recipient || step.parameters?.recipient}</span>
                          </div>
                          <div>
                            <span className="text-slate-400">Subject: </span>
                            <span className="text-slate-900 font-semibold">{step.result?.preview?.subject || step.parameters?.subject}</span>
                          </div>
                          <div>
                            <span className="text-slate-400">Body Preview: </span>
                            <span className="text-slate-700">{step.result?.preview?.body_preview || 'Prepared text.'}</span>
                          </div>
                        </div>
                      </div>
                    )}

                    {/* RESEARCH AGENT OUTPUT */}
                    {step.agent === 'research_agent' && step.result && (
                      <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-2xs space-y-3">
                        <div className="flex items-center justify-between text-xs text-slate-500">
                          <span>Search Provider: <strong className="text-slate-700">{step.result.provider}</strong></span>
                          <span>{step.result.result_count} Verified Sources Found</span>
                        </div>
                        {step.result.sources?.length > 0 ? (
                          <div className="space-y-2">
                            {step.result.sources.map((src: any, sIdx: number) => (
                              <div key={sIdx} className="p-2.5 bg-slate-50 rounded-lg border border-slate-100 text-xs">
                                <a
                                  href={src.url}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="font-semibold text-indigo-600 hover:underline flex items-center gap-1"
                                >
                                  <span>{src.title}</span>
                                  <ExternalLink className="w-3 h-3" />
                                </a>
                                <p className="text-slate-600 mt-1 line-clamp-2">{src.snippet}</p>
                              </div>
                            ))}
                          </div>
                        ) : (
                          <div className="text-xs text-slate-500 italic bg-slate-50 p-3 rounded-lg">
                            {step.result.note}
                          </div>
                        )}
                      </div>
                    )}

                    {/* GENERAL AGENT OUTPUT */}
                    {step.agent === 'general_agent' && step.result && (
                      <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-2xs text-xs text-slate-800 leading-relaxed whitespace-pre-wrap">
                        {step.result.response}
                      </div>
                    )}

                    {/* DATA ANALYSIS AGENT OUTPUT */}
                    {step.agent === 'data_analysis_agent' && step.result && (
                      <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-2xs space-y-3 text-xs">
                        <div className="font-semibold text-slate-900">{step.result.summary}</div>
                        <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                          {step.result.columns?.map((c: any) => (
                            <div key={c.name} className="p-2 bg-slate-50 rounded-lg border border-slate-100">
                              <div className="font-semibold text-slate-800">{c.name}</div>
                              <div className="text-[11px] text-slate-500">{c.type} • {c.missing_count} missing</div>
                              {c.mean !== undefined && c.mean !== null && (
                                <div className="text-[11px] text-indigo-600 font-medium">Mean: {c.mean}</div>
                              )}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* ERROR OUTPUT */}
                    {step.result?.error && (
                      <div className="p-3 bg-rose-50 border border-rose-200 text-rose-700 text-xs rounded-lg">
                        <strong>Execution Error:</strong> {step.result.error}
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
