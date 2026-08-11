import type {
  AudienceResponse,
  AuthResponse,
  DeviceResponse,
  FunnelResponse,
  GeoResponse,
  OverviewResponse,
  TimeSeriesResponse,
  User,
  VideoDetailResponse,
  VideoPerformanceResponse,
  VideoSummary,
} from "../types";

const API_BASE = import.meta.env.VITE_API_URL ?? "";
const TOKEN_STORAGE_KEY = "streampulse_token";

export class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.status = status;
    this.name = "ApiError";
  }
}

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_STORAGE_KEY);
}

export function setToken(token: string | null): void {
  if (token) localStorage.setItem(TOKEN_STORAGE_KEY, token);
  else localStorage.removeItem(TOKEN_STORAGE_KEY);
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = getToken();
  const headers = new Headers(options.headers);
  headers.set("Content-Type", "application/json");
  if (token) headers.set("Authorization", `Bearer ${token}`);

  const response = await fetch(`${API_BASE}${path}`, { ...options, headers });

  if (!response.ok) {
    let detail = response.statusText;
    try {
      const body = await response.json();
      detail = body.detail ?? detail;
    } catch {
      // response wasn't JSON — keep statusText
    }
    throw new ApiError(detail || "Request failed", response.status);
  }

  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}

function toQuery(params: Record<string, string | number | boolean | null | undefined>): string {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== null && value !== undefined && value !== "") {
      search.set(key, String(value));
    }
  }
  const qs = search.toString();
  return qs ? `?${qs}` : "";
}

export interface RangeParams {
  start: string;
  end: string;
  videoId?: number | null;
  compare?: boolean;
}

function rangeQuery({ start, end, videoId, compare }: RangeParams): string {
  return toQuery({ start, end, video_id: videoId ?? null, compare: compare ?? false });
}

export const authApi = {
  login: (email: string, password: string) =>
    request<AuthResponse>("/api/auth/login", { method: "POST", body: JSON.stringify({ email, password }) }),
  register: (email: string, password: string, fullName: string) =>
    request<AuthResponse>("/api/auth/register", {
      method: "POST",
      body: JSON.stringify({ email, password, full_name: fullName }),
    }),
  me: () => request<User>("/api/auth/me"),
};

export const metricsApi = {
  overview: (params: RangeParams) => request<OverviewResponse>(`/api/metrics/overview${rangeQuery(params)}`),
  timeseries: (params: RangeParams) => request<TimeSeriesResponse>(`/api/metrics/timeseries${rangeQuery(params)}`),
};

export const videosApi = {
  list: () => request<VideoSummary[]>("/api/videos"),
  performance: (
    params: RangeParams & { sort?: string; order?: "asc" | "desc"; limit?: number; offset?: number }
  ) =>
    request<VideoPerformanceResponse>(
      `/api/videos/performance${toQuery({
        start: params.start,
        end: params.end,
        video_id: params.videoId ?? null,
        sort: params.sort ?? "views",
        order: params.order ?? "desc",
        limit: params.limit ?? 10,
        offset: params.offset ?? 0,
      })}`
    ),
  detail: (id: number, params: { start: string; end: string }) =>
    request<VideoDetailResponse>(`/api/videos/${id}${toQuery({ start: params.start, end: params.end })}`),
};

export const audienceApi = {
  funnel: (params: RangeParams) => request<FunnelResponse>(`/api/audience/funnel${rangeQuery(params)}`),
  breakdown: (params: RangeParams) => request<AudienceResponse>(`/api/audience${rangeQuery(params)}`),
};

export const geoApi = {
  breakdown: (params: RangeParams) => request<GeoResponse>(`/api/geo${rangeQuery(params)}`),
};

export const deviceApi = {
  breakdown: (params: RangeParams) => request<DeviceResponse>(`/api/device${rangeQuery(params)}`),
};

export const systemApi = {
  health: () => request<{ status: string }>("/health"),
};
