import type { ReactNode } from 'react'
import type { Job } from '../types'
import { JobStatusBadge } from './StatusBadge'

interface JobDetailDrawerProps {
  job: Job | null
  onClose: () => void
  onRetry: (job: Job) => void
  onCancel: (job: Job) => void
}

function Row({ label, value }: { label: string; value: ReactNode }) {
  return (
    <div className="detail-row">
      <span className="detail-label">{label}</span>
      <span className="detail-value">{value}</span>
    </div>
  )
}

export function JobDetailDrawer({ job, onClose, onRetry, onCancel }: JobDetailDrawerProps) {
  if (!job) return null

  return (
    <div className="drawer-overlay" onClick={onClose}>
      <div className="drawer" onClick={(e) => e.stopPropagation()}>
        <div className="drawer-header">
          <h2>Job detail</h2>
          <button className="btn-small btn-ghost" onClick={onClose}>
            Close
          </button>
        </div>

        <Row label="ID" value={<span className="mono">{job.id}</span>} />
        <Row label="Type" value={job.job_type} />
        <Row label="Status" value={<JobStatusBadge status={job.status} />} />
        <Row label="Priority" value={job.priority} />
        <Row label="Retries" value={`${job.retries} / ${job.max_retries}`} />
        <Row label="Idempotency key" value={job.idempotency_key ?? '—'} />
        <Row label="Worker" value={job.worker_id ?? '—'} />
        <Row label="Input" value={<span className="mono">{job.input_uri}</span>} />
        <Row label="Output" value={<span className="mono">{job.output_uri ?? '—'}</span>} />
        <Row label="Created" value={new Date(job.created_at).toLocaleString()} />
        <Row
          label="Started"
          value={job.started_at ? new Date(job.started_at).toLocaleString() : '—'}
        />
        <Row
          label="Completed"
          value={job.completed_at ? new Date(job.completed_at).toLocaleString() : '—'}
        />
        <Row
          label="Heartbeat"
          value={job.heartbeat_at ? new Date(job.heartbeat_at).toLocaleString() : '—'}
        />
        <Row
          label="Next retry"
          value={job.next_retry_at ? new Date(job.next_retry_at).toLocaleString() : '—'}
        />

        {job.error && (
          <div className="detail-block detail-error">
            <span className="detail-label">Error</span>
            <pre>{job.error}</pre>
          </div>
        )}

        {Object.keys(job.params ?? {}).length > 0 && (
          <div className="detail-block">
            <span className="detail-label">Params</span>
            <pre>{JSON.stringify(job.params, null, 2)}</pre>
          </div>
        )}

        {job.result && (
          <div className="detail-block">
            <span className="detail-label">Result</span>
            <pre>{JSON.stringify(job.result, null, 2)}</pre>
          </div>
        )}

        <div className="drawer-actions">
          {job.status === 'failed' && (
            <button className="btn btn-primary" onClick={() => onRetry(job)}>
              Retry job
            </button>
          )}
          {(job.status === 'pending' || job.status === 'queued' || job.status === 'retrying') && (
            <button className="btn btn-ghost" onClick={() => onCancel(job)}>
              Cancel job
            </button>
          )}
        </div>
      </div>
    </div>
  )
}
