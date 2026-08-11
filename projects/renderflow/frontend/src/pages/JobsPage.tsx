import { useCallback, useState } from 'react'
import { api } from '../api/client'
import { JobTable } from '../components/JobTable'
import { usePolling } from '../hooks/usePolling'
import type { JobStatus, JobType } from '../types'

const JOB_TYPES: JobType[] = ['transcode', 'thumbnail', 'audio_extract', 'metadata']
const JOB_STATUSES: JobStatus[] = [
  'pending',
  'queued',
  'processing',
  'retrying',
  'completed',
  'failed',
  'cancelled',
]

export function JobsPage() {
  const [status, setStatus] = useState<JobStatus | ''>('')
  const [jobType, setJobType] = useState<JobType | ''>('')
  const [offset, setOffset] = useState(0)
  const limit = 25

  const fetchJobs = useCallback(
    () =>
      api.listJobs({
        status: status || undefined,
        job_type: jobType || undefined,
        limit,
        offset,
      }),
    [status, jobType, offset],
  )

  const { data, error, refresh } = usePolling(fetchJobs)
  const [actionLoading, setActionLoading] = useState<string | null>(null)

  const handleCancel = async (jobId: string) => {
    setActionLoading(jobId)
    try {
      await api.cancelJob(jobId)
      await refresh()
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Cancel failed')
    } finally {
      setActionLoading(null)
    }
  }

  const totalPages = data ? Math.ceil(data.total / limit) : 0
  const currentPage = Math.floor(offset / limit) + 1

  return (
    <div className="page">
      <header className="page-header">
        <div>
          <h1>Jobs</h1>
          <p className="page-subtitle">Browse and filter the job queue</p>
        </div>
      </header>

      <div className="filters">
        <label>
          Status
          <select
            value={status}
            onChange={(e) => {
              setStatus(e.target.value as JobStatus | '')
              setOffset(0)
            }}
          >
            <option value="">All</option>
            {JOB_STATUSES.map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </select>
        </label>
        <label>
          Type
          <select
            value={jobType}
            onChange={(e) => {
              setJobType(e.target.value as JobType | '')
              setOffset(0)
            }}
          >
            <option value="">All</option>
            {JOB_TYPES.map((t) => (
              <option key={t} value={t}>
                {t}
              </option>
            ))}
          </select>
        </label>
        {data && (
          <span className="filter-meta">
            {data.total} job{data.total === 1 ? '' : 's'}
          </span>
        )}
      </div>

      {error && <div className="alert alert-error">{error}</div>}

      <section className="panel">
        {data && (
          <>
            <JobTable
              jobs={data.items}
              showActions
              onCancel={handleCancel}
              actionLoading={actionLoading}
            />
            {totalPages > 1 && (
              <div className="pagination">
                <button
                  type="button"
                  className="btn btn-ghost"
                  disabled={offset === 0}
                  onClick={() => setOffset((o) => Math.max(0, o - limit))}
                >
                  Previous
                </button>
                <span>
                  Page {currentPage} of {totalPages}
                </span>
                <button
                  type="button"
                  className="btn btn-ghost"
                  disabled={offset + limit >= (data?.total ?? 0)}
                  onClick={() => setOffset((o) => o + limit)}
                >
                  Next
                </button>
              </div>
            )}
          </>
        )}
      </section>
    </div>
  )
}
