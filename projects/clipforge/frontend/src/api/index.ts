import { request, tokenStore } from './client';
import type {
  DashboardStats,
  Job,
  Page,
  Project,
  TokenPair,
  User,
  Video,
  VideoListItem,
  VideoStatus,
  Workspace,
} from '@/types';

export const authApi = {
  register: (email: string, full_name: string, password: string) =>
    request<User>('/auth/register', {
      method: 'POST',
      auth: false,
      body: { email, full_name, password },
    }),
  login: async (email: string, password: string) => {
    const tokens = await request<TokenPair>('/auth/login', {
      method: 'POST',
      auth: false,
      body: { email, password },
    });
    tokenStore.set(tokens);
    return tokens;
  },
  me: () => request<User>('/auth/me'),
  logout: () => tokenStore.clear(),
};

export const workspaceApi = {
  list: () => request<Workspace[]>('/workspaces'),
  create: (name: string) =>
    request<Workspace>('/workspaces', { method: 'POST', body: { name } }),
  listProjects: (workspaceId: string) =>
    request<Project[]>(`/workspaces/${workspaceId}/projects`),
  createProject: (workspaceId: string, name: string, description?: string) =>
    request<Project>(`/workspaces/${workspaceId}/projects`, {
      method: 'POST',
      body: { name, description },
    }),
};

export interface VideoSearchParams {
  q?: string;
  status?: VideoStatus | '';
  project_id?: string;
  limit?: number;
  offset?: number;
}

export const videoApi = {
  search: (params: VideoSearchParams = {}) => {
    const qs = new URLSearchParams();
    if (params.q) qs.set('q', params.q);
    if (params.status) qs.set('status', params.status);
    if (params.project_id) qs.set('project_id', params.project_id);
    qs.set('limit', String(params.limit ?? 24));
    qs.set('offset', String(params.offset ?? 0));
    return request<Page<VideoListItem>>(`/videos?${qs.toString()}`);
  },
  get: (id: string) => request<Video>(`/videos/${id}`),
  status: (id: string) => request<Job>(`/videos/${id}/status`),
  reprocess: (id: string) => request<Job>(`/videos/${id}/reprocess`, { method: 'POST' }),
  remove: (id: string) => request<void>(`/videos/${id}`, { method: 'DELETE' }),
  upload: (projectId: string, file: File, title?: string) => {
    const form = new FormData();
    form.append('project_id', projectId);
    form.append('file', file);
    if (title) form.append('title', title);
    return request<Video>('/videos', { method: 'POST', body: form, isForm: true });
  },
};

export const dashboardApi = {
  stats: () => request<DashboardStats>('/dashboard/stats'),
};
