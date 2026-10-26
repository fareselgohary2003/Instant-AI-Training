export interface WorkflowStepResult {
  step_id: number;
  agent: string;
  description: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'awaiting_approval' | 'rejected';
  parameters?: Record<string, any>;
  result?: Record<string, any>;
  duration_seconds?: number;
}

export interface WorkflowPlanStep {
  step_id: number;
  agent: string;
  description: string;
  parameters: Record<string, any>;
  depends_on?: number[];
}

export interface WorkflowPlan {
  goal: string;
  interpretation?: string;
  steps: WorkflowPlanStep[];
  requires_approval: boolean;
}

export interface WorkflowRunResponse {
  run_id: number;
  goal: string;
  status: 'pending' | 'planning' | 'running' | 'completed' | 'failed' | 'awaiting_approval' | 'cancelled';
  plan: WorkflowPlan;
  results: WorkflowStepResult[];
  duration_seconds?: number;
  message: string;
  created_at?: string;
  completed_at?: string;
}

export interface WorkflowHistoryResponse {
  count: number;
  items: WorkflowRunResponse[];
}

export interface ApprovalRequest {
  id: number;
  run_id: number;
  step_id: number;
  action_type: string;
  description: string;
  parameters?: Record<string, any>;
  status: 'pending' | 'approved' | 'rejected';
  requested_at?: string;
  decided_at?: string;
  decision_notes?: string;
}

export interface AgentDefinition {
  id: string;
  name: string;
  description: string;
  capabilities: string[];
  tools: string[];
  requires_approval: boolean;
  is_enabled: boolean;
  disabled_reason?: string;
}

export interface AnalyticsData {
  total_workflows: number;
  completed: number;
  failed: number;
  awaiting_approval: number;
  running: number;
  success_rate_percent: number;
  avg_duration_seconds: number;
  agent_usage: { agent: string; count: number }[];
  daily_volume: { date: string; count: number; completed: number; failed: number }[];
}

export interface SettingsStatus {
  app_name: string;
  app_version: string;
  llm_provider: string;
  llm_model: string;
  groq_configured: boolean;
  smtp_configured: boolean;
  smtp_host: string;
  sender_email: string;
  search_configured: boolean;
  search_provider: string;
  database: string;
  cors_origins: string[];
}

export interface DataAnalysisResult {
  filename: string;
  row_count: number;
  column_count: number;
  numeric_columns: string[];
  categorical_columns: string[];
  columns: {
    name: string;
    type: string;
    missing_count: number;
    missing_percent: number;
    mean?: number;
    median?: number;
    min?: number;
    max?: number;
    std?: number;
    top_values?: Record<string, number>;
  }[];
  chart_data: Record<string, any>[];
  summary: string;
}

// Configurable API Base URL with fallback
const API_BASE = import.meta.env.VITE_API_BASE_URL
  ? import.meta.env.VITE_API_BASE_URL.replace(/\/$/, '')
  : '';

async function request<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const url = `${API_BASE}${endpoint}`;
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options?.headers as Record<string, string> || {}),
  };

  const response = await fetch(url, {
    ...options,
    headers,
  });

  if (!response.ok) {
    let errorMessage = `HTTP ${response.status}: ${response.statusText}`;
    try {
      const data = await response.json();
      if (data.detail) {
        errorMessage = typeof data.detail === 'string' ? data.detail : JSON.stringify(data.detail);
      }
    } catch {
      // Keep default error
    }
    throw new Error(errorMessage);
  }

  return response.json();
}

export const api = {
  // Workflows
  runWorkflow: (goal: string) =>
    request<WorkflowRunResponse>('/api/workflows/run', {
      method: 'POST',
      body: JSON.stringify({ goal }),
    }),

  getHistory: (params?: { limit?: number; offset?: number; status?: string; search?: string }) => {
    const query = new URLSearchParams();
    if (params?.limit) query.set('limit', String(params.limit));
    if (params?.offset) query.set('offset', String(params.offset));
    if (params?.status) query.set('status', params.status);
    if (params?.search) query.set('search', params.search);
    const qs = query.toString() ? `?${query.toString()}` : '';
    return request<WorkflowHistoryResponse>(`/api/workflows/history${qs}`);
  },

  getWorkflowDetail: (runId: number) =>
    request<WorkflowRunResponse>(`/api/workflows/history/${runId}`),

  cancelWorkflow: (runId: number) =>
    request<{ run_id: number; status: string; message: string }>(`/api/workflows/${runId}/cancel`, {
      method: 'POST',
    }),

  retryWorkflow: (runId: number) =>
    request<WorkflowRunResponse>(`/api/workflows/${runId}/retry`, {
      method: 'POST',
    }),

  // Approvals
  getApprovals: () => request<ApprovalRequest[]>('/api/approvals'),

  approveAction: (approvalId: number, notes?: string) =>
    request<{ success: boolean; message: string; run_id: number }>(`/api/approvals/${approvalId}/approve`, {
      method: 'POST',
      body: JSON.stringify({ notes: notes || '' }),
    }),

  rejectAction: (approvalId: number, notes?: string) =>
    request<{ success: boolean; message: string; run_id: number }>(`/api/approvals/${approvalId}/reject`, {
      method: 'POST',
      body: JSON.stringify({ notes: notes || '' }),
    }),

  // Agents
  getAgents: () => request<AgentDefinition[]>('/api/agents'),

  // Analytics
  getAnalytics: () => request<AnalyticsData>('/api/analytics'),

  // Settings
  getSettingsStatus: () => request<SettingsStatus>('/api/settings/status'),

  // Data Analysis
  analyzeData: (csv_content: string, filename = 'data.csv') =>
    request<DataAnalysisResult>('/api/data/analyze', {
      method: 'POST',
      body: JSON.stringify({ csv_content, filename }),
    }),
};
