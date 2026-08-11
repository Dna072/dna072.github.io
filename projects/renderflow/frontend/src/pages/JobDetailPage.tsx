import { useCallback, useState, type ReactNode } from 'react'
import { Link, useParams } from 'react-router-dom'
import { api } from '../api/client'
import { JobStatusBadge } from '../components/StatusBadge'
import { usePolling } from '../hooks/usePolling'

function formatTime(iso: string | null) {
  if (!iso) return '—'
  return new Date(iso).toLocaleString()
}

function DetailRow({ label, value }: { label: string; value: ReactNode }) {
  return (
    <div className="detail-row">
      <dt>{label}</dt>
      <dd>{value}</dd>
    </div>
  )
}

export function JobDetailPage() {
  const { jobId } = useParams<{ jobId: string }>()
  const fetchJob = useCallback(() => {
    if (!jobId) throw new Error('Missing job ID')
    return api.getJob(jobId)
  }, [jobId])

  const { data: job, error, refresh } = usePolling(fetchJob, 3000, Boolean(jobId))
  const [actionLoading, setActionLoading] = useState(false)
  const [actionError, setActionError] = useState<string | null>(null)

  const runAction = async (action: 'retry' | 'cancel') => {
    if (!jobId) return
    setActionLoading(true)
    setActionError(null)
    try {
      if (action === 'retry') await api.retryJob(jobId)
      else await api.cancelJob(jobId)
      await refresh()
    } catch (err) {
      setActionError(err instanceof Error ? err.message : 'Action failed')
    } finally {
      setActionLoading(false)
    }
  }

  if (!jobId) {
    return <div className="alert alert-error">Invalid job ID</div>
  }

  return (
    <div className="page">
      <header className="page-header">
        <div>
          <Link to="/jobs" className="back-link">
            ← Jobs
          </Link>
          <h1>Job detail</h1>
          <p className="page-subtitle mono">{jobId}</p>
        </div>
        <div className="header-actions">
          {job?.status === 'failed' && (
            <button
              type="button"
              className="btn btn-primary"
              disabled={actionLoading}
              onClick={() => void runAction('retry')}
            >
              Retry
            </button>
          )}
          {(job?.status === 'queued' || job?.status === 'pending') && (
            <button
              type="button"
              className="btn btn-ghost"
              disabled={actionLoading}
              onClick={() => void runAction('cancel')}
            >
              Cancel
            </button>
          )}
        </div>
      </header>

      {error && <div className="alert alert-error">{error}</div>}
      {actionError && <div className="alert alert-error">{actionError}</div>}

      {job && (
        <section className="panel">
          <dl className="detail-grid">
            <DetailRow label="Status" value={<JobStatusBadge status={job.status} />} />
            <DetailRow label="Type" value={job.job_type} />
            <DetailRow label="Priority" value={job.priority} />
            <DetailRow label="Retries" value={`${job.retries} / ${job.max_retries}`} />
            <DetailRow label="Worker" value={job.worker_id ?? '—'} />
            <DetailRow label="Input URI" value={<code>{job.input_uri}</code>} />
            <DetailRow
              label="Output URI"
              value={job.output_uri ? <code>{job.output_uri}</code> : '—'}
            />
            <DetailRow label="Created" value={formatTime(job.created_at)} />
            <DetailRow label="Queued" value={formatTime(job.queued_at)} />
            <DetailRow label="Started" value={formatTime(job.started_at)} />
            <DetailRow label="Completed" value={formatTime(job.completed_at)} />
            <DetailRow label="Next retry" value={formatTime(job.next_retry_at)} />
            <DetailRow label="Heartbeat" value={formatTime(job.heartbeat_at)} />
            {job.idempotency_key && (
              <DetailRow label="Idempotency key" value={<code>{job.idempotency_key}</code>} />
            )}
          </dl>

          {job.error && (
            <div className="alert alert-error">
              <strong>Error</strong>
              <pre>{job.error}</pre>
            </div>
          )}

          {job.params && Object.keys(job.params).length > 0 && (
            <div className="json-block">
              <h3>Params</h3>
              <pre>{JSON.stringify(job.params, null, 2)}</pre>
            </div>
          )}

          {job.result && (
            <div className="json-block">
              <h3>Result</h3>
              <pre>{JSON.stringify(job.result, null, 2)}</pre>
            </div>
          )}
        </section>
      )}
    </div>
  )
}
