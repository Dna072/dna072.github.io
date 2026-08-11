import axios from 'axios'

import { apiClient, API_V1 } from '@/api/client'
import type { Share, SharePermission, SharePublicRead } from '@/types'

export async function createShare(
  workspaceId: string,
  assetId: string,
  payload: { permission: SharePermission; expires_in_hours?: number | null },
): Promise<Share> {
  const { data } = await apiClient.post<Share>(
    `/workspaces/${workspaceId}/assets/${assetId}/shares`,
    payload,
  )
  return data
}

export async function listShares(workspaceId: string, assetId: string): Promise<Share[]> {
  const { data } = await apiClient.get<Share[]>(
    `/workspaces/${workspaceId}/assets/${assetId}/shares`,
  )
  return data
}

export async function revokeShare(workspaceId: string, shareId: string): Promise<void> {
  await apiClient.delete(`/workspaces/${workspaceId}/shares/${shareId}`)
}

export async function getPublicShare(token: string): Promise<SharePublicRead> {
  const { data } = await axios.get<SharePublicRead>(`${API_V1}/shares/public/${token}`)
  return data
}
