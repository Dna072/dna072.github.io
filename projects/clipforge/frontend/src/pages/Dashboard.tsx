import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';

import { dashboardApi } from '@/api';
import { VideoCard } from '@/components/VideoCard';
import { formatBytes, formatDuration } from '@/lib/format';
import type { DashboardStats } from '@/types';

export function Dashboard() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    dashboardApi
      .stats()
      .then(setStats)
      .catch(() => setError('Failed to load dashboard'))
      .finally(() => setLoading(false));
  }, []);

  const cards = stats
    ? [
        { label: 'Videos', value: String(stats.total_videos), icon: '▦' },
        { label: 'Projects', value: String(stats.total_projects), icon: '▤' },
        {
          label: 'Total Duration',
          value: formatDuration(stats.total_duration_seconds),
          icon: '◷',
        },
        { label: 'Storage', value: formatBytes(stats.total_storage_bytes), icon: '⛁' },
      ]
    : [];

  return (
    <>
      <div className="topbar">
        <div>
          <h1 className="page-title">Dashboard</h1>
          <p className="page-subtitle">Overview of your video intelligence workspace</p>
        </div>
        <Link to="/upload" className="btn btn-primary">
          + Upload video
        </Link>
      </div>

      <div className="content">
        {error && <div className="error-banner">{error}</div>}

        {loading ? (
          <div className="center-loader">
            <span className="spinner" />
          </div>
        ) : (
          <>
            <div className="grid grid-stats">
              {cards.map((c) => (
                <div key={c.label} className="card">
                  <div className="row between">
                    <span className="stat-label">{c.label}</span>
                    <span className="stat-icon">{c.icon}</span>
                  </div>
                  <div className="stat-value">{c.value}</div>
                </div>
              ))}
            </div>

            <div className="section">
              <div className="row between" style={{ marginBottom: 12 }}>
                <h2 className="section-title" style={{ margin: 0 }}>
                  Recent videos
                </h2>
                <Link to="/library" className="muted" style={{ fontSize: 13 }}>
                  View all →
                </Link>
              </div>

              {stats && stats.recent_videos.length > 0 ? (
                <div className="grid grid-videos">
                  {stats.recent_videos.map((v) => (
                    <VideoCard key={v.id} video={v} />
                  ))}
                </div>
              ) : (
                <div className="empty-state card">
                  <div className="big">▶</div>
                  <p>No videos yet. Upload your first clip to see AI insights.</p>
                  <Link
                    to="/upload"
                    className="btn btn-primary"
                    style={{ marginTop: 12 }}
                  >
                    Upload a video
                  </Link>
                </div>
              )}
            </div>
          </>
        )}
      </div>
    </>
  );
}
