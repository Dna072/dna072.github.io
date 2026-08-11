import { useQuery } from '@tanstack/react-query'
import { useParams } from 'react-router-dom'

import { getWorkspace } from '@/api/workspaces'

export function useWorkspaceId(): string {
  const { workspaceId } = useParams<{ workspaceId: string }>()
  if (!workspaceId) throw new Error('useWorkspaceId used outside a workspace route')
  return workspaceId
}

export function useWorkspace() {
  const workspaceId = useWorkspaceId()
  const query = useQuery({
    queryKey: ['workspace', workspaceId],
    queryFn: () => getWorkspace(workspaceId),
  })
  return { workspaceId, ...query }
}
