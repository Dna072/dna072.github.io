export type WorkspaceRole = 'ADMIN' | 'MEMBER' | 'VIEWER'
export type AssetStatus = 'UPLOADING' | 'PROCESSING' | 'READY' | 'FAILED'
export type SharePermission = 'VIEW' | 'DOWNLOAD'
export type SortDir = 'asc' | 'desc'
export type SortBy = 'created_at' | 'updated_at' | 'filename' | 'size_bytes'
export type SearchSort = 'relevance' | 'newest' | 'oldest' | 'name'

export interface User {
  id: string
  email: string
  full_name: string
  is_active: boolean
  is_superuser: boolean
  created_at: string
}

export interface TokenPair {
  access_token: string
  refresh_token: string
  token_type: string
}

export interface AuthResponse extends TokenPair {
  user: User
}

export interface Workspace {
  id: string
  name: string
  slug: string
  owner_id: string
  created_at: string
  my_role: WorkspaceRole | null
  member_count: number
  asset_count: number
}

export interface Membership {
  id: string
  workspace_id: string
  user_id: string
  role: WorkspaceRole
  created_at: string
  user_email: string
  user_full_name: string
}

export interface Folder {
  id: string
  workspace_id: string
  parent_id: string | null
  name: string
  path: string
  created_by: string
  created_at: string
  updated_at: string
  asset_count: number
  subfolder_count: number
}

export interface Tag {
  id: string
  workspace_id: string
  name: string
  color: string
  created_at: string
  asset_count: number
}

export interface Asset {
  id: string
  workspace_id: string
  folder_id: string | null
  owner_id: string | null
  filename: string
  original_filename: string
  description: string | null
  content_type: string
  size_bytes: number
  status: AssetStatus
  duration_seconds: number | null
  width: number | null
  height: number | null
  checksum_sha256: string | null
  created_at: string
  updated_at: string
  tags: Tag[]
}

export interface AssetSearchResult extends Asset {
  rank: number | null
}

export interface Page<T> {
  items: T[]
  total: number
  page: number
  page_size: number
  pages: number
}

export interface SignedUrlResponse {
  url: string
  expires_at: string
}

export interface Share {
  id: string
  asset_id: string
  created_by: string
  token: string
  permission: SharePermission
  expires_at: string | null
  revoked_at: string | null
  created_at: string
  is_active: boolean
}

export interface SharePublicRead {
  asset: Asset
  permission: SharePermission
  download_url: string | null
}

export interface ApiErrorBody {
  detail: string | { msg: string; loc: (string | number)[] }[]
}
