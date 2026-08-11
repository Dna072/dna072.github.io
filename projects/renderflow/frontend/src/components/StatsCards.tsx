import type { JobStats } from '../types'

interface StatsCardsProps {
  stats: JobStats
}

const STATUS_ORDER = [
  'processing',
  'queued',
  'retrying',
  'completed',
  'failed',
  'cancelled',
  'pending',
]

export function StatsCards({ stats }: StatsCardsProps) {
  const statusEntries = STATUS_ORDER.filter((s) => (stats.by_status[s] ?? 0) > 0).map(
    (status) => [status, stats.by_status[status] ?? 0] as const,
  )

  return (
    <div className="stats-grid">
      <div className="stat-card stat-card-highlight">
        <span className="stat-label">Total jobs</span>
        <span className="stat-value">{stats.total}</span>
      </div>
      {statusEntries.map(([status, count]) => (
        <div key={status} className="stat-card">
          <span className="stat-label">{status}</span>
          <span className="stat-value">{count}</span>
        </div>
      ))}
      {Object.entries(stats.by_type).map(([type, count]) => (
        <div key={type} className="stat-card stat-card-type">
          <span className="stat-label">{type}</span>
          <span className="stat-value">{count}</span>
        </div>
      ))}
    </div>
  )
}
