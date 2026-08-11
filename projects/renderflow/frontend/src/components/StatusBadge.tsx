import type { JobStatus, WorkerStatus } from '../types'

const JOB_STATUS_CLASS: Record<JobStatus, string> = {
  pending: 'badge badge-muted',
  queued: 'badge badge-info',
  processing: 'badge badge-active',
  retrying: 'badge badge-warn',
  completed: 'badge badge-success',
  failed: 'badge badge-error',
  cancelled: 'badge badge-muted',
}

const WORKER_STATUS_CLASS: Record<WorkerStatus, string> = {
  idle: 'badge badge-success',
  busy: 'badge badge-active',
  offline: 'badge badge-muted',
}

export function JobStatusBadge({ status }: { status: JobStatus }) {
  return <span className={JOB_STATUS_CLASS[status]}>{status}</span>
}

export function WorkerStatusBadge({ status }: { status: WorkerStatus }) {
  return <span className={WORKER_STATUS_CLASS[status]}>{status}</span>
}
