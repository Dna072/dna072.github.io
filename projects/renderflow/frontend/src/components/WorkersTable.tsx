import type { Worker } from '../types'
import { WorkerStatusBadge } from './StatusBadge'

function secondsAgo(value: string): number {
  return Math.max(0, Math.round((Date.now() - new Date(value).getTime()) / 1000))
}

export function WorkersTable({ workers }: { workers: Worker[] }) {
  if (workers.length === 0) {
    return (
      <p className="empty-state">
        No workers registered yet. Start one with <code>docker compose up worker</code>.
      </p>
    )
  }

  return (
    <div className="table-wrap">
      <table className="data-table">
        <thead>
          <tr>
            <th>Worker</th>
            <th>Host</th>
            <th>Status</th>
            <th>Current job</th>
            <th>Processed</th>
            <th>Failed</th>
            <th>Last heartbeat</th>
          </tr>
        </thead>
        <tbody>
          {workers.map((worker) => {
            const stale = secondsAgo(worker.last_heartbeat) > 60 && worker.status !== 'offline'
            return (
              <tr key={worker.id}>
                <td className="mono">{worker.id}</td>
                <td className="muted">
                  {worker.hostname} (pid {worker.pid})
                </td>
                <td>
                  <WorkerStatusBadge status={worker.status} />
                  {stale && <span className="badge badge-warning">stale</span>}
                </td>
                <td className="mono muted">{worker.current_job_id ?? '—'}</td>
                <td>{worker.jobs_processed}</td>
                <td>{worker.jobs_failed}</td>
                <td className="muted">{secondsAgo(worker.last_heartbeat)}s ago</td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}
