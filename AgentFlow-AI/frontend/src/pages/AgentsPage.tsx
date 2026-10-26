import React, { useEffect, useState } from 'react';
import {
  Bot,
  CloudSun,
  FileText,
  Mail,
  Search,
  Database,
  Terminal,
  ShieldCheck,
  ShieldAlert,
  RotateCw,
  AlertCircle,
  Wrench,
} from 'lucide-react';
import { api } from '../api/client';
import type { AgentDefinition } from '../api/client';

export const AgentsPage: React.FC = () => {
  const [agents, setAgents] = useState<AgentDefinition[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchAgents = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getAgents();
      setAgents(data);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch registered agents');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAgents();
  }, []);

  const getAgentIcon = (id: string) => {
    switch (id) {
      case 'weather_agent':
        return CloudSun;
      case 'text_analysis_agent':
        return FileText;
      case 'email_agent':
        return Mail;
      case 'research_agent':
        return Search;
      case 'data_analysis_agent':
        return Database;
      case 'code_execution_agent':
        return Terminal;
      default:
        return Bot;
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-slate-900 tracking-tight">
            Registered Agents & Tools
          </h2>
          <p className="text-sm text-slate-500 mt-1">
            Deterministic registry of AI workers, validated tool integrations, and security policies.
          </p>
        </div>
        <button
          onClick={fetchAgents}
          disabled={loading}
          className="flex items-center gap-1.5 px-3 py-1.5 bg-white border border-slate-200 text-slate-700 hover:bg-slate-50 text-xs font-medium rounded-lg shadow-2xs transition-colors cursor-pointer self-start sm:self-auto"
        >
          <RotateCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          <span>Refresh</span>
        </button>
      </div>

      {error && (
        <div className="p-4 bg-rose-50 border border-rose-200 text-rose-800 rounded-xl text-sm">
          {error}
        </div>
      )}

      {/* Agents Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        {loading ? (
          <div className="col-span-2 bg-white p-16 rounded-2xl border border-slate-200 text-center text-slate-400">
            <RotateCw className="w-6 h-6 animate-spin mx-auto text-indigo-500 mb-2" />
            <span>Discovering registered agents...</span>
          </div>
        ) : (
          agents.map((agent) => {
            const Icon = getAgentIcon(agent.id);
            return (
              <div
                key={agent.id}
                className={`bg-white rounded-2xl border p-6 shadow-2xs flex flex-col justify-between transition-all ${
                  agent.is_enabled
                    ? 'border-slate-200 hover:border-indigo-300'
                    : 'border-slate-200/60 opacity-80 bg-slate-50/40'
                }`}
              >
                <div>
                  {/* Card Header */}
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex items-center gap-3">
                      <div
                        className={`w-10 h-10 rounded-xl flex items-center justify-center ${
                          agent.is_enabled
                            ? 'bg-indigo-50 text-indigo-600 border border-indigo-100'
                            : 'bg-slate-100 text-slate-400 border border-slate-200'
                        }`}
                      >
                        <Icon className="w-5 h-5" />
                      </div>
                      <div>
                        <h3 className="text-sm font-bold text-slate-900">{agent.name}</h3>
                        <span className="font-mono text-[11px] text-slate-400">{agent.id}</span>
                      </div>
                    </div>

                    <div className="flex flex-col items-end gap-1.5">
                      {agent.is_enabled ? (
                        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
                          <ShieldCheck className="w-3 h-3" />
                          <span>Operational</span>
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-slate-100 text-slate-600 border border-slate-200">
                          <span>Disabled</span>
                        </span>
                      )}

                      {agent.requires_approval && (
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold bg-amber-50 text-amber-700 border border-amber-200">
                          <ShieldAlert className="w-3 h-3" />
                          <span>Approval Required</span>
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Description */}
                  <p className="text-xs text-slate-600 mt-3 leading-relaxed">
                    {agent.description}
                  </p>

                  {/* Disabled Reason Callout */}
                  {!agent.is_enabled && agent.disabled_reason && (
                    <div className="mt-3 p-3 bg-amber-50/60 border border-amber-200/60 text-amber-800 rounded-xl text-xs flex items-start gap-2">
                      <AlertCircle className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
                      <div>
                        <strong className="font-semibold">Security Limitation: </strong>
                        <span>{agent.disabled_reason}</span>
                      </div>
                    </div>
                  )}

                  {/* Capabilities */}
                  <div className="mt-4">
                    <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block mb-1.5">
                      Capabilities
                    </span>
                    <div className="flex flex-wrap gap-1.5">
                      {agent.capabilities.map((cap, cIdx) => (
                        <span
                          key={cIdx}
                          className="px-2 py-0.5 bg-slate-100 text-slate-700 rounded-md text-[11px] font-medium"
                        >
                          {cap}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>

                {/* Tools Footer */}
                <div className="mt-5 pt-3 border-t border-slate-100 flex items-center justify-between text-xs text-slate-500">
                  <div className="flex items-center gap-1.5">
                    <Wrench className="w-3.5 h-3.5 text-slate-400" />
                    <span>Tools:</span>
                    <span className="font-mono text-slate-700">{agent.tools.join(', ')}</span>
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};
