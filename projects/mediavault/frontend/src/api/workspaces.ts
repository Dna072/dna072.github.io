import { apiClient } from '@/api/client'
import type { Membership, Workspace, WorkspaceRole } from '@/types'

export async function listWorkspaces(): Promise<Workspace[]> {
  const { data } = await apiClient.get<Workspace[]>('/workspaces')
  return data
}

export async function getWorkspace(workspaceId: string): Promise<Workspace> {
  const { data } = await apiClient.get<Workspace>(`/workspaces/${workspaceId}`)
  return data
}

export async function createWorkspace(payload: { name: string; slug: string }): Promise<Workspace> {
  const { data } = await apiClient.post<Workspace>('/workspaces', payload)
  return data
}

export async function updateWorkspace(
  workspaceId: string,
  payload: { name: string },
): Promise<Workspace> {
  const { data } = await apiClient.patch<Workspace>(`/workspaces/${workspaceId}`, payload)
  return data
}

export async function deleteWorkspace(workspaceId: string): Promise<void> {
  await apiClient.delete(`/workspaces/${workspaceId}`)
}

export async function listMembers(workspaceId: string): Promise<Membership[]> {
  const { data } = await apiClient.get<Membership[]>(`/workspaces/${workspaceId}/members`)
  return data
}

export async function inviteMember(
  workspaceId: string,
  payload: { email: string; role: WorkspaceRole },
): Promise<Membership> {
  const { data } = await apiClient.post<Membership>(`/workspaces/${workspaceId}/members`, payload)
  return data
}

export async function updateMemberRole(
  workspaceId: string,
  membershipId: string,
  role: WorkspaceRole,
): Promise<Membership> {
  const { data } = await apiClient.patch<Membership>(
    `/workspaces/${workspaceId}/members/${membershipId}`,
    { role },
  )
  return data
}

export async function removeMember(workspaceId: string, membershipId: string): Promise<void> {
  await apiClient.delete(`/workspaces/${workspaceId}/members/${membershipId}`)
}
