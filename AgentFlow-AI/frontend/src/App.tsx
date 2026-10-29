import { useEffect, useState } from 'react';
import { Layout } from './components/Layout';
import type { PageId } from './components/Layout';
import { OverviewPage } from './pages/OverviewPage';
import { WorkspacePage } from './pages/WorkspacePage';
import { WorkflowsPage } from './pages/WorkflowsPage';
import { ApprovalsPage } from './pages/ApprovalsPage';
import { AgentsPage } from './pages/AgentsPage';
import { AnalyticsPage } from './pages/AnalyticsPage';
import { SettingsPage } from './pages/SettingsPage';
import { WorkflowDetailModal } from './pages/WorkflowDetailModal';
import { api } from './api/client';

export function App() {
  const [activePage, setActivePage] = useState<PageId>('overview');
  const [selectedWorkflowId, setSelectedWorkflowId] = useState<number | null>(null);
  const [pendingApprovalsCount, setPendingApprovalsCount] = useState<number>(0);

  const refreshApprovalsCount = async () => {
    try {
      const approvals = await api.getApprovals();
      setPendingApprovalsCount(approvals.length);
    } catch {
      // Ignore background check failure
    }
  };

  useEffect(() => {
    refreshApprovalsCount();
    const interval = setInterval(refreshApprovalsCount, 15000);
    return () => clearInterval(interval);
  }, []);

  const handleNavigate = (page: PageId, workflowId?: number) => {
    setActivePage(page);
    if (workflowId !== undefined) {
      setSelectedWorkflowId(workflowId);
    }
  };

  return (
    <Layout
      activePage={activePage}
      onNavigate={handleNavigate}
      pendingApprovalsCount={pendingApprovalsCount}
    >
      {activePage === 'overview' && (
        <OverviewPage
          onNavigate={handleNavigate}
          onSelectWorkflow={(id) => setSelectedWorkflowId(id)}
        />
      )}

      {activePage === 'workspace' && (
        <WorkspacePage
          onSelectWorkflow={(id) => setSelectedWorkflowId(id)}
          onRefreshApprovals={refreshApprovalsCount}
        />
      )}

      {activePage === 'workflows' && (
        <WorkflowsPage onSelectWorkflow={(id) => setSelectedWorkflowId(id)} />
      )}

      {activePage === 'approvals' && (
        <ApprovalsPage
          onSelectWorkflow={(id) => setSelectedWorkflowId(id)}
          onRefreshApprovals={refreshApprovalsCount}
        />
      )}

      {activePage === 'agents' && <AgentsPage />}

      {activePage === 'analytics' && <AnalyticsPage />}

      {activePage === 'settings' && <SettingsPage />}

      {/* Workflow Inspection Modal */}
      <WorkflowDetailModal
        runId={selectedWorkflowId}
        onClose={() => setSelectedWorkflowId(null)}
      />
    </Layout>
  );
}

export default App;
