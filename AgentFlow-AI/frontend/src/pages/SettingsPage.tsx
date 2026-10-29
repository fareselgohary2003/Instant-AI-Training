import React, { useEffect, useState } from 'react';
import {
  Shield,
  Key,
  Database,
  Mail,
  Search,
  Globe,
  RotateCw,
  CheckCircle2,
  AlertTriangle,
  Server,
  Lock,
} from 'lucide-react';
import { api } from '../api/client';
import type { SettingsStatus } from '../api/client';

export const SettingsPage: React.FC = () => {
  const [settings, setSettings] = useState<SettingsStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchSettings = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.getSettingsStatus();
      setSettings(res);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch settings status');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSettings();
  }, []);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-slate-900 tracking-tight">System Configuration</h2>
          <p className="text-sm text-slate-500 mt-1">
            Safe inspection of runtime integrations, security guardrails, and environment status.
          </p>
        </div>
        <button
          onClick={fetchSettings}
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

      {loading ? (
        <div className="bg-white p-16 rounded-2xl border border-slate-200 text-center text-slate-400">
          <RotateCw className="w-6 h-6 animate-spin mx-auto text-indigo-500 mb-2" />
          <span>Verifying platform configuration...</span>
        </div>
      ) : settings ? (
        <div className="space-y-6">
          {/* Integration Status Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            {/* LLM Provider Card */}
            <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-2xs space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-xl bg-indigo-50 border border-indigo-100 flex items-center justify-center text-indigo-600">
                    <Key className="w-5 h-5" />
                  </div>
                  <div>
                    <h3 className="text-sm font-bold text-slate-900">LLM Provider (Groq)</h3>
                    <p className="text-xs text-slate-500">Inference engine for Supervisor & Synthesis</p>
                  </div>
                </div>
                {settings.groq_configured ? (
                  <span className="flex items-center gap-1 text-xs font-semibold text-emerald-700 bg-emerald-50 border border-emerald-200 px-2.5 py-1 rounded-full">
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    <span>Configured</span>
                  </span>
                ) : (
                  <span className="flex items-center gap-1 text-xs font-semibold text-rose-700 bg-rose-50 border border-rose-200 px-2.5 py-1 rounded-full">
                    <AlertTriangle className="w-3.5 h-3.5" />
                    <span>Missing Key</span>
                  </span>
                )}
              </div>
              <div className="pt-2 text-xs text-slate-600 space-y-1 font-mono bg-slate-50 p-3 rounded-xl border border-slate-100">
                <div>Model: <strong className="text-slate-800">{settings.llm_model}</strong></div>
                <div>Status: <span className="text-emerald-600">Active</span></div>
                <div>Credentials: <span className="text-slate-400">[Masked via .env]</span></div>
              </div>
            </div>

            {/* SMTP Email Service Card */}
            <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-2xs space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-xl bg-blue-50 border border-blue-100 flex items-center justify-center text-blue-600">
                    <Mail className="w-5 h-5" />
                  </div>
                  <div>
                    <h3 className="text-sm font-bold text-slate-900">SMTP Email Provider</h3>
                    <p className="text-xs text-slate-500">Protected external email transmission</p>
                  </div>
                </div>
                {settings.smtp_configured ? (
                  <span className="flex items-center gap-1 text-xs font-semibold text-emerald-700 bg-emerald-50 border border-emerald-200 px-2.5 py-1 rounded-full">
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    <span>Configured</span>
                  </span>
                ) : (
                  <span className="flex items-center gap-1 text-xs font-semibold text-amber-700 bg-amber-50 border border-amber-200 px-2.5 py-1 rounded-full">
                    <AlertTriangle className="w-3.5 h-3.5" />
                    <span>Unconfigured</span>
                  </span>
                )}
              </div>
              <div className="pt-2 text-xs text-slate-600 space-y-1 font-mono bg-slate-50 p-3 rounded-xl border border-slate-100">
                <div>Host: <strong className="text-slate-800">{settings.smtp_host}</strong></div>
                <div>Sender: <span className="text-slate-800">{settings.sender_email}</span></div>
                <div>Policy: <span className="text-amber-700 font-semibold">Strict Human Approval Enforced</span></div>
              </div>
            </div>

            {/* Web Search Integration */}
            <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-2xs space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-xl bg-teal-50 border border-teal-100 flex items-center justify-center text-teal-600">
                    <Search className="w-5 h-5" />
                  </div>
                  <div>
                    <h3 className="text-sm font-bold text-slate-900">Search Integration</h3>
                    <p className="text-xs text-slate-500">Real-time information retrieval</p>
                  </div>
                </div>
                <span className="flex items-center gap-1 text-xs font-semibold text-slate-700 bg-slate-100 border border-slate-200 px-2.5 py-1 rounded-full">
                  <span>{settings.search_provider}</span>
                </span>
              </div>
              <div className="pt-2 text-xs text-slate-600 space-y-1 font-mono bg-slate-50 p-3 rounded-xl border border-slate-100">
                <div>Primary API: <strong>Tavily</strong> (TAVILY_API_KEY)</div>
                <div>Active Mode: <span className="text-indigo-600 font-semibold">{settings.search_provider}</span></div>
                <div>Rate Limits: Guarded with timeouts</div>
              </div>
            </div>

            {/* Database Persistence */}
            <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-2xs space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-xl bg-purple-50 border border-purple-100 flex items-center justify-center text-purple-600">
                    <Database className="w-5 h-5" />
                  </div>
                  <div>
                    <h3 className="text-sm font-bold text-slate-900">Database & Persistence</h3>
                    <p className="text-xs text-slate-500">Audit logs, runs, and approval records</p>
                  </div>
                </div>
                <span className="flex items-center gap-1 text-xs font-semibold text-emerald-700 bg-emerald-50 border border-emerald-200 px-2.5 py-1 rounded-full">
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  <span>Online</span>
                </span>
              </div>
              <div className="pt-2 text-xs text-slate-600 space-y-1 font-mono bg-slate-50 p-3 rounded-xl border border-slate-100">
                <div>Engine: <strong>{settings.database}</strong></div>
                <div>Schema: Safe multi-table migrations enabled</div>
                <div>Integrity: Zero simulated entries</div>
              </div>
            </div>
          </div>

          {/* Security Guardrails Card */}
          <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-2xs space-y-4">
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-xl bg-slate-100 flex items-center justify-center text-slate-700">
                <Shield className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-sm font-bold text-slate-900">Enterprise Security Architecture</h3>
                <p className="text-xs text-slate-500">Core safety principles and guardrails</p>
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs pt-1">
              <div className="p-3.5 bg-slate-50 rounded-xl border border-slate-200/70 space-y-1">
                <div className="font-semibold text-slate-800 flex items-center gap-1.5">
                  <Lock className="w-3.5 h-3.5 text-indigo-600" />
                  <span>Human-in-the-Loop</span>
                </div>
                <p className="text-slate-500">
                  Side-effects (e.g. SMTP email delivery) are intercepted at the server level. Hiding a frontend button is never considered authorization.
                </p>
              </div>

              <div className="p-3.5 bg-slate-50 rounded-xl border border-slate-200/70 space-y-1">
                <div className="font-semibold text-slate-800 flex items-center gap-1.5">
                  <Server className="w-3.5 h-3.5 text-indigo-600" />
                  <span>Untrusted LLM Outputs</span>
                </div>
                <p className="text-slate-500">
                  All LLM-generated plans are strictly parsed and validated against the deterministic agent registry before any execution begins.
                </p>
              </div>

              <div className="p-3.5 bg-slate-50 rounded-xl border border-slate-200/70 space-y-1">
                <div className="font-semibold text-slate-800 flex items-center gap-1.5">
                  <Globe className="w-3.5 h-3.5 text-indigo-600" />
                  <span>CORS & Origin Isolation</span>
                </div>
                <p className="text-slate-500">
                  Strict origin whitelisting: only designated local development ports (5173, 8000, 8001) are permitted cross-origin requests.
                </p>
              </div>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
};
