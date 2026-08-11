import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { dashboardApi } from '../api/endpoints';
import { FullPageSpinner } from '../components/Spinner';
import { VideoCard } from '../components/VideoCard';
import { formatBytes, formatDuration } from '../utils/format';

export function DashboardPage() {
  const { data, isLoading } = useQuery({
    queryKey: ['dashboard'],
    queryFn: dashboardApi.stats,
    refetchInterval: 5000,
  });

  if (isLoading || !data) return <FullPageSpinner />;

  const stats = [
    { label: 'Total videos', value: data.total_videos, cls: '' },
    { label: 'Ready', value: data.status_breakdown.ready, cls: 'teal' },
    { label: 'Active jobs', value: data.active_jobs, cls: 'amber' },
    { label: 'Workspaces', value: data.total_workspaces, cls: '' },
  ];

  return (
    <>
      <div className="page-head">
        <div>
          <h1 className="page-title">Dashboard</h1>
          <p className="page-sub">Overview of your content library and processing pipeline</p>
        </div>
        <Link to="/upload" className="btn btn-primary">
          Upload video
        </Link>
      </div>

      <div className="stat-grid">
        {stats.map((s) => (
          <div key={s.label} className="card stat">
            <div className="stat__label">{s.label}</div>
            <div className={`stat__value ${s.cls}`}>{s.value}</div>
          </div>
        ))}
        <div className="card stat">
          <div className="stat__label">Total duration</div>
          <div className="stat__value">{formatDuration(data.total_duration_seconds)}</div>
        </div>
        <div className="card stat">
          <div className="stat__label">Storage used</div>
          <div className="stat__value">{formatBytes(data.total_storage_bytes)}</div>
        </div>
      </div>

      {data.top_tags.length > 0 ? (
        <div className="card" style={{ padding: '18px 20px', marginBottom: 28 }}>
          <div className="section-title">Top tags</div>
          <div className="tag-row">
            {data.top_tags.map((t) => (
              <span key={t.tag} className="tag">
                {t.tag} · {t.count}
              </span>
            ))}
          </div>
        </div>
      ) : null}

      <div className="section-title">Recent uploads</div>
      {data.recent_videos.length === 0 ? (
        <div className="card empty">
          <div className="empty__icon">🎬</div>
          <p>No videos yet. Upload your first clip to get started.</p>
        </div>
      ) : (
        <div className="video-grid">
          {data.recent_videos.map((v) => (
            <VideoCard key={v.id} video={v} />
          ))}
        </div>
      )}
    </>
  );
}
