import type { ApiError, TokenPair } from "./types";

const API_BASE = (import.meta.env.VITE_API_BASE as string) || "/api/v1";
const ACCESS_KEY = "mv_access_token";
const REFRESH_KEY = "mv_refresh_token";

export class ApiClientError extends Error {
  code: string;
  status: number;
  requestId?: string;
  constructor(status: number, error: ApiError) {
    super(error.message);
    this.code = error.code;
    this.status = status;
    this.requestId = error.request_id;
  }
}

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

let refreshInFlight: Promise<boolean> | null = null;

async function tryRefresh(): Promise<boolean> {
  const refresh = tokenStore.refresh;
  if (!refresh) return false;
  if (!refreshInFlight) {
    refreshInFlight = (async () => {
      try {
        const resp = await fetch(`${API_BASE}/auth/refresh`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ refresh_token: refresh }),
        });
        if (!resp.ok) return false;
        tokenStore.set((await resp.json()) as TokenPair);
        return true;
      } catch {
        return false;
      } finally {
        refreshInFlight = null;
      }
    })();
  }
  return refreshInFlight;
}

interface RequestOptions {
  method?: string;
  body?: unknown;
  formData?: FormData;
  auth?: boolean;
  signal?: AbortSignal;
}

async function raw(path: string, opts: RequestOptions, retry = true): Promise<Response> {
  const headers: Record<string, string> = {};
  if (opts.auth !== false && tokenStore.access) {
    headers.Authorization = `Bearer ${tokenStore.access}`;
  }
  let body: BodyInit | undefined;
  if (opts.formData) {
    body = opts.formData;
  } else if (opts.body !== undefined) {
    headers["Content-Type"] = "application/json";
    body = JSON.stringify(opts.body);
  }

  const resp = await fetch(`${API_BASE}${path}`, {
    method: opts.method ?? "GET",
    headers,
    body,
    signal: opts.signal,
  });

  // Transparent refresh-and-retry on a single 401.
  if (resp.status === 401 && retry && opts.auth !== false && tokenStore.refresh) {
    if (await tryRefresh()) {
      return raw(path, opts, false);
    }
    tokenStore.clear();
  }
  return resp;
}

export async function api<T>(path: string, opts: RequestOptions = {}): Promise<T> {
  const resp = await raw(path, opts);
  if (resp.status === 204) return undefined as T;
  const text = await resp.text();
  const data = text ? JSON.parse(text) : undefined;
  if (!resp.ok) {
    const error: ApiError = data?.error ?? { code: "error", message: resp.statusText };
    throw new ApiClientError(resp.status, error);
  }
  return data as T;
}

export function buildQuery(params: Record<string, unknown>): string {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value === undefined || value === null || value === "") continue;
    if (Array.isArray(value)) {
      value.forEach((v) => search.append(key, String(v)));
    } else {
      search.append(key, String(value));
    }
  }
  const qs = search.toString();
  return qs ? `?${qs}` : "";
}

export { API_BASE };
