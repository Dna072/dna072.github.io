import axios, { type AxiosError, type InternalAxiosRequestConfig } from 'axios';
import type {
  AuthResponse,
  DashboardStats,
  Job,
  Page,
  TokenPair,
  User,
  Video,
  VideoDetail,
  VideoUploadResponse,
  Workspace,
} from './types';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const API_PREFIX = '/api/v1';

export const ACCESS_TOKEN_KEY = 'clipforge_access_token';
export const REFRESH_TOKEN_KEY = 'clipforge_refresh_token';

export const api = axios.create({
  baseURL: `${API_BASE}${API_PREFIX}`,
  headers: { 'Content-Type': 'application/json' },
});

function getAccessToken(): string | null {
  return localStorage.getItem(ACCESS_TOKEN_KEY);
}

function getRefreshToken(): string | null {
  return localStorage.getItem(REFRESH_TOKEN_KEY);
}

export function storeTokens(tokens: TokenPair): void {
  localStorage.setItem(ACCESS_TOKEN_KEY, tokens.access_token);
  localStorage.setItem(REFRESH_TOKEN_KEY, tokens.refresh_token);
}

export function clearTokens(): void {
  localStorage.removeItem(ACCESS_TOKEN_KEY);
  localStorage.removeItem(REFRESH_TOKEN_KEY);
}

api.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = getAccessToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

let refreshPromise: Promise<TokenPair> | null = null;

api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const original = error.config as InternalAxiosRequestConfig & { _retry?: boolean };

    if (error.response?.status === 401 && original && !original._retry) {
      const refresh = getRefreshToken();
      if (!refresh) {
        clearTokens();
        return Promise.reject(error);
      }

      original._retry = true;

      if (!refreshPromise) {
        refreshPromise = axios
          .post<TokenPair>(`${API_BASE}${API_PREFIX}/auth/refresh`, {
            refresh_token: refresh,
          })
          .then((res) => {
            storeTokens(res.data);
            return res.data;
          })
          .finally(() => {
            refreshPromise = null;
          });
      }

      try {
        const tokens = await refreshPromise;
        original.headers.Authorization = `Bearer ${tokens.access_token}`;
        return api(original);
      } catch {
        clearTokens();
        return Promise.reject(error);
      }
    }

    return Promise.reject(error);
  },
);

export function extractErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail;
    if (typeof detail === 'string') return detail;
    if (Array.isArray(detail)) {
      return detail.map((d: { msg: string }) => d.msg).join(', ');
    }
    return error.message;
  }
  if (error instanceof Error) return error.message;
  return 'Something went wrong';
}

export async function register(
  email: string,
  password: string,
  full_name: string,
): Promise<AuthResponse> {
  const { data } = await api.post<AuthResponse>('/auth/register', {
    email,
    password,
    full_name,
  });
  storeTokens(data.tokens);
  return data;
}

export async function login(email: string, password: string): Promise<AuthResponse> {
  const { data } = await api.post<AuthResponse>('/auth/login', { email, password });
  storeTokens(data.tokens);
  return data;
}

export async function fetchMe(): Promise<User> {
  const { data } = await api.get<User>('/auth/me');
  return data;
}

export async function fetchDashboardStats(): Promise<DashboardStats> {
  const { data } = await api.get<DashboardStats>('/dashboard/stats');
  return data;
}

export async function fetchWorkspaces(): Promise<Workspace[]> {
  const { data } = await api.get<Workspace[]>('/workspaces');
  return data;
}

export async function fetchVideos(params?: {
  q?: string;
  limit?: number;
  offset?: number;
}): Promise<Page<Video>> {
  const { data } = await api.get<Page<Video>>('/videos', { params });
  return data;
}

export async function fetchVideo(id: string): Promise<VideoDetail> {
  const { data } = await api.get<VideoDetail>(`/videos/${id}`);
  return data;
}

export async function fetchVideoJob(videoId: string): Promise<Job> {
  const { data } = await api.get<Job>(`/videos/${videoId}/job`);
  return data;
}

export async function uploadVideo(formData: FormData): Promise<VideoUploadResponse> {
  const { data } = await api.post<VideoUploadResponse>('/videos/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return data;
}

export async function fetchThumbnailBlob(videoId: string): Promise<string | null> {
  try {
    const { data } = await api.get<Blob>(`/videos/${videoId}/thumbnail`, {
      responseType: 'blob',
    });
    return URL.createObjectURL(data);
  } catch {
    return null;
  }
}


export function apiErrorMessage(err: unknown): string {
  if (axios.isAxiosError(err)) {
    const detail = err.response?.data?.detail;
    if (typeof detail === 'string') return detail;
    if (Array.isArray(detail)) return detail.map((d) => d.msg || JSON.stringify(d)).join(', ');
    return err.message;
  }
  if (err instanceof Error) return err.message;
  return 'Unexpected error';
}
