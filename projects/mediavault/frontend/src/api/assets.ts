import { apiClient, API_BASE_URL } from '@/api/client'
import type { Asset, AssetSearchResult, Page, SearchSort, SignedUrlResponse, SortBy, SortDir } from '@/types'

export interface AssetListParams {
  folder_id?: string | null
  content_type?: string
  status?: string
  tag?: string[]
  owner_id?: string
  sort_by?: SortBy
  sort_dir?: SortDir
  page?: number
  page_size?: number
}

export async function listAssets(
  workspaceId: string,
  params: AssetListParams = {},
): Promise<Page<Asset>> {
  const { data } = await apiClient.get<Page<Asset>>(`/workspaces/${workspaceId}/assets`, {
    params,
  })
  return data
}

export async function getAsset(workspaceId: string, assetId: string): Promise<Asset> {
  const { data } = await apiClient.get<Asset>(`/workspaces/${workspaceId}/assets/${assetId}`)
  return data
}

export async function updateAsset(
  workspaceId: string,
  assetId: string,
  payload: { filename?: string; description?: string; folder_id?: string | null },
): Promise<Asset> {
  const { data } = await apiClient.patch<Asset>(
    `/workspaces/${workspaceId}/assets/${assetId}`,
    payload,
  )
  return data
}

export async function deleteAsset(workspaceId: string, assetId: string): Promise<void> {
  await apiClient.delete(`/workspaces/${workspaceId}/assets/${assetId}`)
}

export async function attachTag(workspaceId: string, assetId: string, tagId: string): Promise<Asset> {
  const { data } = await apiClient.post<Asset>(
    `/workspaces/${workspaceId}/assets/${assetId}/tags/${tagId}`,
  )
  return data
}

export async function detachTag(workspaceId: string, assetId: string, tagId: string): Promise<Asset> {
  const { data } = await apiClient.delete<Asset>(
    `/workspaces/${workspaceId}/assets/${assetId}/tags/${tagId}`,
  )
  return data
}

export async function getDownloadUrl(
  workspaceId: string,
  assetId: string,
): Promise<SignedUrlResponse> {
  const { data } = await apiClient.get<SignedUrlResponse>(
    `/workspaces/${workspaceId}/assets/${assetId}/download-url`,
  )
  return data
}

export function resolveApiUrl(relativeUrl: string): string {
  if (relativeUrl.startsWith('http')) return relativeUrl
  return `${API_BASE_URL}${relativeUrl}`
}

export interface UploadAssetPayload {
  file: File
  folderId?: string | null
  description?: string
  onProgress?: (percent: number) => void
}

export async function uploadAsset(
  workspaceId: string,
  { file, folderId, description, onProgress }: UploadAssetPayload,
): Promise<Asset> {
  const formData = new FormData()
  formData.append('file', file)
  const { data } = await apiClient.post<Asset>(`/workspaces/${workspaceId}/assets`, formData, {
    params: {
      folder_id: folderId ?? undefined,
      description: description ?? undefined,
    },
    headers: { 'Content-Type': 'multipart/form-data' },
    onUploadProgress: (event) => {
      if (onProgress && event.total) {
        onProgress(Math.round((event.loaded / event.total) * 100))
      }
    },
  })
  return data
}

export interface SearchParams {
  q?: string
  folder_id?: string | null
  content_type?: string
  tag?: string[]
  sort?: SearchSort
  page?: number
  page_size?: number
}

export async function searchAssets(
  workspaceId: string,
  params: SearchParams,
): Promise<Page<AssetSearchResult>> {
  const { data } = await apiClient.get<Page<AssetSearchResult>>(
    `/workspaces/${workspaceId}/search`,
    { params },
  )
  return data
}
