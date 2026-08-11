import type { TokenPair } from '@/types';

const API_BASE = '/api/v1';
const ACCESS_KEY = 'clipforge.access';
const REFRESH_KEY = 'clipforge.refresh';

export const tokenStore = {
  get access() {
    return localStorage.getItem(ACCESS_KEY);
  },
  get refresh() {
    return localStorage.getItem(REFRESH_KEY);
  },
  set(tokens: TokenPair) {
    localStorage.setItem(ACCESS_KEY, tokens.access_token);
    localStorage.setItem(REFRESH_KEY, tokens.refresh_token);
  },
  clear() {
    localStorage.removeItem(ACCESS_KEY);
    localStorage.removeItem(REFRESH_KEY);
  },
};

export class ApiError extends Error {
  status: number;
  code?: string;
  constructor(message: string, status: number, code?: string) {
    super(message);
    this.status = status;
    this.code = code;
  }
}

interface RequestOptions {
  method?: string;
  body?: unknown;
  auth?: boolean;
  isForm?: boolean;
  _retry?: boolean;
}

async function refreshTokens(): Promise<boolean> {
  const refresh = tokenStore.refresh;
  if (!refresh) return false;
  const resp = await fetch(`${API_BASE}/auth/refresh`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh_token: refresh }),
  });
  if (!resp.ok) {
    tokenStore.clear();
    return false;
  }
  tokenStore.set((await resp.json()) as TokenPair);
  return true;
}

async function parseError(resp: Response): Promise<ApiError> {
  let detail = resp.statusText;
  let code: string | undefined;
  try {
    const data = await resp.json();
    if (data?.error) {
      detail = data.error.detail ?? detail;
      code = data.error.code;
    } else if (data?.detail) {
      detail =
        typeof data.detail === 'string' ? data.detail : JSON.stringify(data.detail);
    }
  } catch {
    /* non-JSON error body */
  }
  return new ApiError(detail, resp.status, code);
}

export async function request<T>(path: string, opts: RequestOptions = {}): Promise<T> {
  const { method = 'GET', body, auth = true, isForm = false } = opts;
  const headers: Record<string, string> = {};
  if (auth && tokenStore.access) {
    headers.Authorization = `Bearer ${tokenStore.access}`;
  }
  if (body !== undefined && !isForm) {
    headers['Content-Type'] = 'application/json';
  }

  const resp = await fetch(`${API_BASE}${path}`, {
    method,
    headers,
    body: isForm
      ? (body as BodyInit)
      : body !== undefined
        ? JSON.stringify(body)
        : undefined,
  });

  // Transparently refresh once on 401, then retry the original request.
  if (resp.status === 401 && auth && !opts._retry) {
    const refreshed = await refreshTokens();
    if (refreshed) {
      return request<T>(path, { ...opts, _retry: true });
    }
  }

  if (!resp.ok) {
    throw await parseError(resp);
  }
  if (resp.status === 204) {
    return undefined as T;
  }
  return (await resp.json()) as T;
}

export function mediaUrl(path: string | null): string | null {
  if (!path) return null;
  return `/media/${path.replace(/^\/+/, '')}`;
}
