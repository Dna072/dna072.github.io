import { Link } from 'react-router-dom'
import type { Job } from '../types'
import { JobStatusBadge } from './StatusBadge'

function formatTime(iso: string | null) {
  if (!iso) return '—'
  return new Date(iso).toLocaleString()
}

interface JobTableProps {
  jobs: Job[]
  showActions?: boolean
  onRetry?: (jobId: string) => void
  onCancel?: (jobId: string) => void
  actionLoading?: string | null
}

export function JobTable({
  jobs,
  showActions = false,
  onRetry,
  onCancel,
  actionLoading,
}: JobTableProps) {
  if (jobs.length === 0) {
    return <p className="empty-state">No jobs match the current filters.</p>
  }

  return (
    <div className="table-wrap">
      <table className="data-table">
        <thead>
          <tr>
            <th>ID</th>
            <th>Type</th>
            <th>Status</th>
            <th>Priority</th>
            <th>Retries</th>
            <th>Created</th>
            {showActions && <th>Actions</th>}
          </tr>
        </thead>
        <tbody>
          {jobs.map((job) => (
            <tr key={job.id}>
              <td>
                <Link to={`/jobs/${job.id}`} className="mono-link">
                  {job.id.slice(0, 8)}…
                </Link>
              </td>
              <td>{job.job_type}</td>
              <td>
                <JobStatusBadge status={job.status} />
              </td>
              <td>{job.priority}</td>
              <td>
                {job.retries}/{job.max_retries}
              </td>
              <td className="muted">{formatTime(job.created_at)}</td>
              {showActions && (
                <td className="actions-cell">
                  {job.status === 'failed' && onRetry && (
                    <button
                      type="button"
                      className="btn btn-sm btn-primary"
                      disabled={actionLoading === job.id}
                      onClick={() => onRetry(job.id)}
                    >
                      Retry
                    </button>
                  )}
                  {(job.status === 'queued' || job.status === 'pending') && onCancel && (
                    <button
                      type="button"
                      className="btn btn-sm btn-ghost"
                      disabled={actionLoading === job.id}
                      onClick={() => onCancel(job.id)}
                    >
                      Cancel
                    </button>
                  )}
                </td>
              )}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
