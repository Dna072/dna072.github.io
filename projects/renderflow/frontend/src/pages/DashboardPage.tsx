import { api } from '../api/client'
import { StatsCards } from '../components/StatsCards'
import { JobTable } from '../components/JobTable'
import { usePolling } from '../hooks/usePolling'

export function DashboardPage() {
  const statsPoll = usePolling(() => api.getStats())
  const jobsPoll = usePolling(() => api.listJobs({ limit: 10 }))

  return (
    <div className="page">
      <header className="page-header">
        <div>
          <h1>Dashboard</h1>
          <p className="page-subtitle">Queue health and recent activity</p>
        </div>
      </header>

      {statsPoll.error && <div className="alert alert-error">{statsPoll.error}</div>}
      {statsPoll.data && <StatsCards stats={statsPoll.data} />}

      <section className="panel">
        <div className="panel-header">
          <h2>Recent jobs</h2>
        </div>
        {jobsPoll.error && <div className="alert alert-error">{jobsPoll.error}</div>}
        {jobsPoll.data && <JobTable jobs={jobsPoll.data.items} />}
      </section>
    </div>
  )
}
