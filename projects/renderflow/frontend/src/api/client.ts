// Typed API client for the RenderFlow backend.
// Uses relative URLs so the same build works behind the Vite dev proxy and the
// production nginx reverse proxy.

const BASE = import.meta.env.VITE_API_BASE ?? "";

export type JobStatus =
  | "pending"
  | "queued"
  | "running"
  | "retrying"
  | "succeeded"
  | "failed"
  | "cancelled";

export type JobType = "transcode" | "thumbnail" | "audio_extract" | "metadata";

export interface Job {
  id: string;
  job_type: JobType;
  status: JobStatus;
  priority: number;
  input_uri: string;
  params: Record<string, unknown>;
  output_uri: string | null;
  result: Record<string, unknown> | null;
  retries: number;
  max_retries: number;
  error_message: string | null;
  idempotency_key: string | null;
  worker_id: string | null;
  next_run_at: string | null;
  created_at: string;
  updated_at: string;
  started_at: string | null;
  completed_at: string | null;
}

export interface JobList {
  items: Job[];
  total: number;
  limit: number;
  offset: number;
}

export interface JobStats {
  counts: Record<string, number>;
  total: number;
}

export interface Worker {
  worker_id: string;
  hostname: string | null;
  status: string;
  current_job_id: string | null;
  jobs_processed: number;
  jobs_failed: number;
  started_at: string;
  last_heartbeat_at: string;
  healthy: boolean;
  seconds_since_heartbeat: number;
}

export interface WorkerList {
  items: Worker[];
  total: number;
  online: number;
}

export interface JobCreate {
  job_type: JobType;
  input_uri: string;
  params?: Record<string, unknown>;
  priority?: number;
  max_retries?: number | null;
  idempotency_key?: string | null;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail ?? JSON.stringify(body);
    } catch {
      /* keep statusText */
    }
    throw new Error(`${res.status}: ${detail}`);
  }
  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

export const api = {
  listJobs: (params: {
    status?: string;
    job_type?: string;
    limit?: number;
    offset?: number;
  }) => {
    const q = new URLSearchParams();
    if (params.status) q.set("status", params.status);
    if (params.job_type) q.set("job_type", params.job_type);
    q.set("limit", String(params.limit ?? 50));
    q.set("offset", String(params.offset ?? 0));
    return request<JobList>(`/api/v1/jobs?${q.toString()}`);
  },
  getJob: (id: string) => request<Job>(`/api/v1/jobs/${id}`),
  submitJob: (body: JobCreate) =>
    request<Job>(`/api/v1/jobs`, { method: "POST", body: JSON.stringify(body) }),
  retryJob: (id: string, resetRetries = false) =>
    request<Job>(`/api/v1/jobs/${id}/retry?reset_retries=${resetRetries}`, {
      method: "POST",
    }),
  cancelJob: (id: string) =>
    request<Job>(`/api/v1/jobs/${id}/cancel`, { method: "POST" }),
  failedJobs: (limit = 50) =>
    request<JobList>(`/api/v1/jobs/failed?limit=${limit}`),
  stats: () => request<JobStats>(`/api/v1/jobs/stats`),
  workers: () => request<WorkerList>(`/api/v1/workers`),
};
