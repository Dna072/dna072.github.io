import type { WorkspaceRole } from '@/types'

const ROLE_RANK: Record<WorkspaceRole, number> = {
  VIEWER: 0,
  MEMBER: 1,
  ADMIN: 2,
}

export function roleAtLeast(role: WorkspaceRole | null | undefined, minimum: WorkspaceRole): boolean {
  if (!role) return false
  return ROLE_RANK[role] >= ROLE_RANK[minimum]
}

export function canWrite(role: WorkspaceRole | null | undefined): boolean {
  return roleAtLeast(role, 'MEMBER')
}

export function canAdminister(role: WorkspaceRole | null | undefined): boolean {
  return roleAtLeast(role, 'ADMIN')
}

export function roleLabel(role: WorkspaceRole): string {
  switch (role) {
    case 'ADMIN':
      return 'Admin'
    case 'MEMBER':
      return 'Member'
    case 'VIEWER':
      return 'Viewer'
  }
}
