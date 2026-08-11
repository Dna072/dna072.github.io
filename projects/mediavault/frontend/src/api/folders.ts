import { apiClient } from '@/api/client'
import type { Folder } from '@/types'

export async function listFolders(workspaceId: string, parentId?: string | null): Promise<Folder[]> {
  const { data } = await apiClient.get<Folder[]>(`/workspaces/${workspaceId}/folders`, {
    params: parentId ? { parent_id: parentId } : undefined,
  })
  return data
}

export async function getFolder(workspaceId: string, folderId: string): Promise<Folder> {
  const { data } = await apiClient.get<Folder>(`/workspaces/${workspaceId}/folders/${folderId}`)
  return data
}

export async function createFolder(
  workspaceId: string,
  payload: { name: string; parent_id?: string | null },
): Promise<Folder> {
  const { data } = await apiClient.post<Folder>(`/workspaces/${workspaceId}/folders`, payload)
  return data
}

export async function updateFolder(
  workspaceId: string,
  folderId: string,
  payload: { name?: string; parent_id?: string | null },
): Promise<Folder> {
  const { data } = await apiClient.patch<Folder>(
    `/workspaces/${workspaceId}/folders/${folderId}`,
    payload,
  )
  return data
}

export async function deleteFolder(workspaceId: string, folderId: string): Promise<void> {
  await apiClient.delete(`/workspaces/${workspaceId}/folders/${folderId}`)
}
