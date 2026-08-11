import type { Job, JobCreate, JobList, JobStats, WorkerList } from '../types'

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? ''

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...init,
  })
  if (!res.ok) {
    let detail = res.statusText
    try {
      const body = (await res.json()) as { detail?: string }
      detail = body.detail ?? JSON.stringify(body)
    } catch {
      // response body wasn't JSON; fall back to statusText
    }
    throw new Error(detail)
  }
  if (res.status === 204) return undefined as T
  return (await res.json()) as T
}

export type ListJobsParams = {
  status?: string
  job_type?: string
  limit?: number
  offset?: number
}

export const api = {
  listJobs(params: ListJobsParams = {}): Promise<JobList> {
    const query = new URLSearchParams()
    if (params.status) query.set('status', params.status)
    if (params.job_type) query.set('job_type', params.job_type)
    query.set('limit', String(params.limit ?? 50))
    query.set('offset', String(params.offset ?? 0))
    return request<JobList>(`/api/v1/jobs?${query.toString()}`)
  },

  getJob(id: string): Promise<Job> {
    return request<Job>(`/api/v1/jobs/${id}`)
  },

  createJob(payload: JobCreate): Promise<Job> {
    return request<Job>('/api/v1/jobs', { method: 'POST', body: JSON.stringify(payload) })
  },

  retryJob(id: string): Promise<Job> {
    return request<Job>(`/api/v1/jobs/${id}/retry`, { method: 'POST' })
  },

  cancelJob(id: string): Promise<Job> {
    return request<Job>(`/api/v1/jobs/${id}/cancel`, { method: 'POST' })
  },

  getStats(): Promise<JobStats> {
    return request<JobStats>('/api/v1/jobs/stats')
  },

  listWorkers(): Promise<WorkerList> {
    return request<WorkerList>('/api/v1/workers')
  },
}
