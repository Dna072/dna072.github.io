export type Role = "ADMIN" | "MEMBER" | "VIEWER";
export type AssetKind = "VIDEO" | "IMAGE" | "DOCUMENT" | "OTHER";
export type AssetStatus = "UPLOADING" | "PROCESSING" | "READY" | "FAILED";

export interface User {
  id: string;
  email: string;
  full_name: string;
  is_active: boolean;
  is_superuser: boolean;
  created_at: string;
}

export interface TokenPair {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface AuthResponse {
  user: User;
  tokens: TokenPair;
}

export interface Workspace {
  id: string;
  name: string;
  slug: string;
  description: string;
  owner_id: string;
  created_at: string;
  role: Role;
}

export interface Membership {
  id: string;
  workspace_id: string;
  user: User;
  role: Role;
  created_at: string;
}

export interface Tag {
  id: string;
  workspace_id: string;
  name: string;
  color: string;
  created_at: string;
}

export interface FolderNode {
  id: string;
  workspace_id: string;
  parent_id: string | null;
  name: string;
  path: string;
  created_at: string;
  children: FolderNode[];
  asset_count: number;
}

export interface Asset {
  id: string;
  workspace_id: string;
  folder_id: string | null;
  name: string;
  description: string;
  original_filename: string;
  content_type: string;
  kind: AssetKind;
  size_bytes: number;
  status: AssetStatus;
  width: number | null;
  height: number | null;
  duration_seconds: number | null;
  checksum_sha256: string | null;
  uploaded_by: string | null;
  created_at: string;
  updated_at: string;
  tags: Tag[];
}

export interface Page<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export interface SignedUrl {
  url: string;
  expires_at: number;
  method: string;
}

export interface Share {
  id: string;
  asset_id: string;
  token: string;
  expires_at: string | null;
  max_downloads: number | null;
  download_count: number;
  allow_download: boolean;
  revoked: boolean;
  created_at: string;
}

export interface SearchResult {
  query: string;
  results: Page<Asset>;
  facets: { kinds: Record<string, number>; tags: Record<string, number> };
}

export interface Breadcrumb {
  id: string;
  name: string;
}

export interface ApiError {
  code: string;
  message: string;
  request_id?: string;
}
