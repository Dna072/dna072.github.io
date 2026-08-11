export type JobType = 'transcode' | 'thumbnail' | 'audio_extract' | 'metadata'

export type JobStatus =
  'pending' | 'queued' | 'processing' | 'retrying' | 'completed' | 'failed' | 'cancelled'

export type WorkerStatus = 'idle' | 'busy' | 'offline'

export interface Job {
  id: string
  job_type: JobType
  status: JobStatus
  priority: number
  input_uri: string
  output_uri: string | null
  params: Record<string, unknown>
  result: Record<string, unknown> | null
  idempotency_key: string | null
  retries: number
  max_retries: number
  error: string | null
  worker_id: string | null
  heartbeat_at: string | null
  next_retry_at: string | null
  created_at: string
  updated_at: string
  queued_at: string | null
  started_at: string | null
  completed_at: string | null
}

export interface JobList {
  items: Job[]
  total: number
  limit: number
  offset: number
}

export interface JobStats {
  by_status: Record<string, number>
  by_type: Record<string, number>
  total: number
}

export interface Worker {
  id: string
  hostname: string
  pid: number
  status: WorkerStatus
  current_job_id: string | null
  jobs_processed: number
  jobs_failed: number
  started_at: string
  last_heartbeat: string
}

export interface WorkerList {
  items: Worker[]
  total: number
}

export interface JobCreate {
  job_type: JobType
  input_uri: string
  params?: Record<string, unknown>
  priority?: number
  max_retries?: number
  idempotency_key?: string
}

export const JOB_TYPES: JobType[] = ['transcode', 'thumbnail', 'audio_extract', 'metadata']

export const JOB_STATUSES: JobStatus[] = [
  'pending',
  'queued',
  'processing',
  'retrying',
  'completed',
  'failed',
  'cancelled',
]
