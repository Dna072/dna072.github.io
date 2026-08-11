import type { WorkspaceRole } from '@/types'
import { roleLabel } from '@/lib/rbac'

export function RoleBadge({ role }: { role: WorkspaceRole }) {
  const className =
    role === 'ADMIN' ? 'mv-badge-admin' : role === 'MEMBER' ? 'mv-badge-member' : 'mv-badge-viewer'
  return <span className={`mv-badge ${className}`}>{roleLabel(role)}</span>
}
