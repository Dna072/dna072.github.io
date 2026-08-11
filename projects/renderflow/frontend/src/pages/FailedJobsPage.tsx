import { useState } from 'react'
import { api } from '../api/client'
import { JobTable } from '../components/JobTable'
import { usePolling } from '../hooks/usePolling'

export function FailedJobsPage() {
  const { data, error, refresh } = usePolling(() => api.listJobs({ status: 'failed', limit: 100 }))
  const [actionLoading, setActionLoading] = useState<string | null>(null)
  const [message, setMessage] = useState<string | null>(null)

  const handleRetry = async (jobId: string) => {
    setActionLoading(jobId)
    setMessage(null)
    try {
      await api.retryJob(jobId)
      setMessage(`Job ${jobId.slice(0, 8)}… re-queued`)
      await refresh()
    } catch (err) {
      setMessage(err instanceof Error ? err.message : 'Retry failed')
    } finally {
      setActionLoading(null)
    }
  }

  const handleRetryAll = async () => {
    if (!data?.items.length) return
    setActionLoading('all')
    setMessage(null)
    let ok = 0
    let failed = 0
    for (const job of data.items) {
      try {
        await api.retryJob(job.id)
        ok += 1
      } catch {
        failed += 1
      }
    }
    setMessage(`Retried ${ok} job(s)${failed ? `, ${failed} failed` : ''}`)
    await refresh()
    setActionLoading(null)
  }

  return (
    <div className="page">
      <header className="page-header">
        <div>
          <h1>Failed jobs</h1>
          <p className="page-subtitle">Dead-letter queue — manual retry</p>
        </div>
        {data && data.total > 0 && (
          <button
            type="button"
            className="btn btn-primary"
            disabled={actionLoading === 'all'}
            onClick={() => void handleRetryAll()}
          >
            Retry all
          </button>
        )}
      </header>

      {error && <div className="alert alert-error">{error}</div>}
      {message && <div className="alert alert-info">{message}</div>}

      <section className="panel">
        {data && (
          <JobTable
            jobs={data.items}
            showActions
            onRetry={handleRetry}
            actionLoading={actionLoading}
          />
        )}
      </section>
    </div>
  )
}
