import { api, buildQuery } from "./client";
import type {
  Asset,
  AuthResponse,
  Breadcrumb,
  FolderNode,
  Membership,
  Page,
  Role,
  SearchResult,
  Share,
  SignedUrl,
  Tag,
  User,
  Workspace,
} from "./types";

export const authApi = {
  login: (email: string, password: string) =>
    api<AuthResponse>("/auth/login", { method: "POST", body: { email, password }, auth: false }),
  register: (email: string, password: string, full_name: string) =>
    api<AuthResponse>("/auth/register", {
      method: "POST",
      body: { email, password, full_name },
      auth: false,
    }),
  me: () => api<User>("/auth/me"),
  logout: (refresh_token: string) =>
    api<{ detail: string }>("/auth/logout", { method: "POST", body: { refresh_token } }),
};

export const workspaceApi = {
  list: () => api<Workspace[]>("/workspaces"),
  get: (id: string) => api<Workspace>(`/workspaces/${id}`),
  create: (name: string, description: string) =>
    api<Workspace>("/workspaces", { method: "POST", body: { name, description } }),
  members: (id: string) => api<Membership[]>(`/workspaces/${id}/members`),
  addMember: (id: string, email: string, role: Role) =>
    api<Membership>(`/workspaces/${id}/members`, { method: "POST", body: { email, role } }),
  updateMemberRole: (id: string, membershipId: string, role: Role) =>
    api<Membership>(`/workspaces/${id}/members/${membershipId}`, {
      method: "PATCH",
      body: { role },
    }),
  removeMember: (id: string, membershipId: string) =>
    api<{ detail: string }>(`/workspaces/${id}/members/${membershipId}`, { method: "DELETE" }),
};

export const folderApi = {
  tree: (wsId: string) => api<FolderNode[]>(`/workspaces/${wsId}/folders`),
  create: (wsId: string, name: string, parent_id: string | null) =>
    api<FolderNode>(`/workspaces/${wsId}/folders`, { method: "POST", body: { name, parent_id } }),
  breadcrumbs: (wsId: string, folderId: string) =>
    api<Breadcrumb[]>(`/workspaces/${wsId}/folders/${folderId}/breadcrumbs`),
  remove: (wsId: string, folderId: string) =>
    api<{ detail: string }>(`/workspaces/${wsId}/folders/${folderId}`, { method: "DELETE" }),
};

export const tagApi = {
  list: (wsId: string) => api<Tag[]>(`/workspaces/${wsId}/tags`),
  create: (wsId: string, name: string, color: string) =>
    api<Tag>(`/workspaces/${wsId}/tags`, { method: "POST", body: { name, color } }),
  remove: (wsId: string, tagId: string) =>
    api<{ detail: string }>(`/workspaces/${wsId}/tags/${tagId}`, { method: "DELETE" }),
};

export interface AssetQuery {
  page?: number;
  page_size?: number;
  folder_id?: string | null;
  include_subfolders?: boolean;
  kind?: string;
  tag_ids?: string[];
  q?: string;
  sort_by?: string;
  sort_dir?: string;
}

export const assetApi = {
  list: (wsId: string, query: AssetQuery) =>
    api<Page<Asset>>(`/workspaces/${wsId}/assets${buildQuery({ ...query })}`),
  get: (wsId: string, id: string) => api<Asset>(`/workspaces/${wsId}/assets/${id}`),
  upload: (wsId: string, form: FormData) =>
    api<Asset>(`/workspaces/${wsId}/assets`, { method: "POST", formData: form }),
  update: (wsId: string, id: string, body: Partial<Pick<Asset, "name" | "description" | "folder_id">>) =>
    api<Asset>(`/workspaces/${wsId}/assets/${id}`, { method: "PATCH", body }),
  setTags: (wsId: string, id: string, tag_ids: string[]) =>
    api<Asset>(`/workspaces/${wsId}/assets/${id}/tags`, { method: "PUT", body: { tag_ids } }),
  signedUrl: (wsId: string, id: string) =>
    api<SignedUrl>(`/workspaces/${wsId}/assets/${id}/signed-url`),
  remove: (wsId: string, id: string) =>
    api<{ detail: string }>(`/workspaces/${wsId}/assets/${id}`, { method: "DELETE" }),
};

export const searchApi = {
  search: (wsId: string, query: AssetQuery) =>
    api<SearchResult>(`/workspaces/${wsId}/search${buildQuery({ ...query })}`),
};

export const shareApi = {
  list: (wsId: string, assetId: string) =>
    api<Share[]>(`/workspaces/${wsId}/assets/${assetId}/shares`),
  create: (
    wsId: string,
    assetId: string,
    body: { expires_in_seconds?: number | null; max_downloads?: number | null; allow_download: boolean },
  ) => api<Share>(`/workspaces/${wsId}/assets/${assetId}/shares`, { method: "POST", body }),
  revoke: (wsId: string, assetId: string, shareId: string) =>
    api<{ detail: string }>(`/workspaces/${wsId}/assets/${assetId}/shares/${shareId}`, {
      method: "DELETE",
    }),
};
