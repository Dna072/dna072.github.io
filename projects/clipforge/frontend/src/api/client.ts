/// <reference types="vite/client" />
import type { TokenPair } from '@/types';

// The API is reached through a relative prefix so the same build works behind
// the Vite dev proxy and a production reverse proxy (see vite.config.ts).
const API_BASE = import.meta.env.VITE_API_URL ?? '/api/v1';

const ACCESS_KEY = 'clipforge_access_token';
const REFRESH_KEY = 'clipforge_refresh_token';

/** Error thrown for non-2xx API responses, carrying the HTTP status. */
export class ApiError extends Error {
  readonly status: number;
  readonly detail: unknown;

  constructor(status: number, message: string, detail?: unknown) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.detail = detail;
  }
}

/** Small localStorage-backed token store used by the auth flow. */
export const tokenStore = {
  get access(): string | null {
    return localStorage.getItem(ACCESS_KEY);
  },
  get refresh(): string | null {
    return localStorage.getItem(REFRESH_KEY);
  },
  set(tokens: TokenPair): void {
    localStorage.setItem(ACCESS_KEY, tokens.access_token);
    localStorage.setItem(REFRESH_KEY, tokens.refresh_token);
  },
  clear(): void {
    localStorage.removeItem(ACCESS_KEY);
    localStorage.removeItem(REFRESH_KEY);
  },
};

/**
 * Resolve a stored media key (e.g. `videos/<id>/thumbnail.jpg`) to a URL the
 * browser can load. Absolute URLs and already-prefixed paths pass through.
 */
export function mediaUrl(key: string | null | undefined): string | undefined {
  if (!key) return undefined;
  if (/^https?:\/\//i.test(key) || key.startsWith('/media/')) return key;
  return `/media/${key.replace(/^\/+/, '')}`;
}

interface RequestOptions {
  method?: string;
  body?: unknown;
  /** Attach the bearer token (default true). */
  auth?: boolean;
  /** Send the body as multipart FormData instead of JSON. */
  isForm?: boolean;
}

function extractDetail(data: unknown, fallback: string): string {
  if (data && typeof data === 'object' && 'detail' in data) {
    const detail = (data as { detail: unknown }).detail;
    if (typeof detail === 'string') return detail;
    if (Array.isArray(detail)) {
      return detail
        .map((d) =>
          d && typeof d === 'object' && 'msg' in d ? String((d as { msg: unknown }).msg) : String(d),
        )
        .join(', ');
    }
  }
  return fallback;
}

let refreshPromise: Promise<boolean> | null = null;

async function tryRefresh(): Promise<boolean> {
  const refresh = tokenStore.refresh;
  if (!refresh) return false;
  if (!refreshPromise) {
    refreshPromise = fetch(`${API_BASE}/auth/refresh`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: refresh }),
    })
      .then(async (res) => {
        if (!res.ok) {
          tokenStore.clear();
          return false;
        }
        tokenStore.set((await res.json()) as TokenPair);
        return true;
      })
      .catch(() => {
        tokenStore.clear();
        return false;
      })
      .finally(() => {
        refreshPromise = null;
      });
  }
  return refreshPromise;
}

/**
 * Typed fetch wrapper. Adds auth headers, JSON/form encoding, transparent
 * 401 refresh-and-retry, and consistent error handling.
 */
export async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { method = 'GET', body, auth = true, isForm = false } = options;

  const doFetch = (): Promise<Response> => {
    const headers: Record<string, string> = {};
    if (auth && tokenStore.access) {
      headers.Authorization = `Bearer ${tokenStore.access}`;
    }
    let payload: BodyInit | undefined;
    if (body !== undefined) {
      if (isForm) {
        payload = body as FormData;
      } else {
        headers['Content-Type'] = 'application/json';
        payload = JSON.stringify(body);
      }
    }
    return fetch(`${API_BASE}${path}`, { method, headers, body: payload });
  };

  let res = await doFetch();
  if (res.status === 401 && auth && path !== '/auth/refresh') {
    if (await tryRefresh()) {
      res = await doFetch();
    }
  }

  if (!res.ok) {
    let data: unknown = null;
    try {
      data = await res.json();
    } catch {
      // no JSON body
    }
    throw new ApiError(res.status, extractDetail(data, res.statusText || 'Request failed'), data);
  }

  if (res.status === 204) return undefined as T;
  const text = await res.text();
  return (text ? JSON.parse(text) : undefined) as T;
}
