import { Outlet } from 'react-router-dom'

import { Sidebar } from '@/components/layout/Sidebar'
import { useWorkspace } from '@/hooks/useWorkspace'

export function AppLayout() {
  const { data: workspace, isLoading, isError } = useWorkspace()

  if (isLoading) {
    return (
      <div className="mv-flex mv-items-center mv-justify-between" style={{ minHeight: '100vh', justifyContent: 'center' }}>
        <div className="mv-spinner" />
      </div>
    )
  }

  if (isError || !workspace) {
    return (
      <div className="mv-empty-state" style={{ minHeight: '100vh' }}>
        <h2>Workspace not found</h2>
        <p>You may not have access to this workspace, or it doesn't exist.</p>
        <a href="/workspaces" className="mv-btn mv-btn-primary">
          Back to workspaces
        </a>
      </div>
    )
  }

  return (
    <div className="mv-app-shell">
      <Sidebar workspace={workspace} />
      <div className="mv-main">
        <Outlet context={workspace} />
      </div>
    </div>
  )
}
