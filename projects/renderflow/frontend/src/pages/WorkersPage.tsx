import { Link } from 'react-router-dom'
import { api } from '../api/client'
import { WorkerStatusBadge } from '../components/StatusBadge'
import { usePolling } from '../hooks/usePolling'

function formatTime(iso: string) {
  return new Date(iso).toLocaleString()
}

function heartbeatAge(iso: string) {
  const seconds = Math.floor((Date.now() - new Date(iso).getTime()) / 1000)
  if (seconds < 60) return `${seconds}s ago`
  return `${Math.floor(seconds / 60)}m ago`
}

export function WorkersPage() {
  const { data, error } = usePolling(() => api.listWorkers())

  return (
    <div className="page">
      <header className="page-header">
        <div>
          <h1>Workers</h1>
          <p className="page-subtitle">Live worker registry from heartbeats</p>
        </div>
        {data && (
          <span className="filter-meta">
            {data.total} worker{data.total === 1 ? '' : 's'}
          </span>
        )}
      </header>

      {error && <div className="alert alert-error">{error}</div>}

      <section className="panel">
        {!data?.items.length ? (
          <p className="empty-state">No workers registered. Scale up worker replicas.</p>
        ) : (
          <div className="table-wrap">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Worker ID</th>
                  <th>Host</th>
                  <th>Status</th>
                  <th>Current job</th>
                  <th>Processed</th>
                  <th>Failed</th>
                  <th>Last heartbeat</th>
                </tr>
              </thead>
              <tbody>
                {data.items.map((w) => (
                  <tr key={w.id}>
                    <td className="mono">{w.id}</td>
                    <td>
                      {w.hostname}
                      <span className="muted">:{w.pid}</span>
                    </td>
                    <td>
                      <WorkerStatusBadge status={w.status} />
                    </td>
                    <td>
                      {w.current_job_id ? (
                        <Link to={`/jobs/${w.current_job_id}`} className="mono-link">
                          {w.current_job_id.slice(0, 8)}…
                        </Link>
                      ) : (
                        '—'
                      )}
                    </td>
                    <td>{w.jobs_processed}</td>
                    <td>{w.jobs_failed}</td>
                    <td className="muted" title={formatTime(w.last_heartbeat)}>
                      {heartbeatAge(w.last_heartbeat)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  )
}
