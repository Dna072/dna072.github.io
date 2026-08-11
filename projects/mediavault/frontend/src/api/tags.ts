import { apiClient } from '@/api/client'
import type { Tag } from '@/types'

export async function listTags(workspaceId: string): Promise<Tag[]> {
  const { data } = await apiClient.get<Tag[]>(`/workspaces/${workspaceId}/tags`)
  return data
}

export async function createTag(
  workspaceId: string,
  payload: { name: string; color?: string },
): Promise<Tag> {
  const { data } = await apiClient.post<Tag>(`/workspaces/${workspaceId}/tags`, payload)
  return data
}

export async function updateTag(
  workspaceId: string,
  tagId: string,
  payload: { name?: string; color?: string },
): Promise<Tag> {
  const { data } = await apiClient.patch<Tag>(`/workspaces/${workspaceId}/tags/${tagId}`, payload)
  return data
}

export async function deleteTag(workspaceId: string, tagId: string): Promise<void> {
  await apiClient.delete(`/workspaces/${workspaceId}/tags/${tagId}`)
}
