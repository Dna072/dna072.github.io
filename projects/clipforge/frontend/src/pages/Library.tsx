import { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';

import { videoApi } from '@/api';
import { VideoCard } from '@/components/VideoCard';
import type { VideoListItem, VideoStatus } from '@/types';

const STATUS_OPTIONS: { value: VideoStatus | ''; label: string }[] = [
  { value: '', label: 'All statuses' },
  { value: 'completed', label: 'Completed' },
  { value: 'processing', label: 'Processing' },
  { value: 'queued', label: 'Queued' },
  { value: 'failed', label: 'Failed' },
];

export function Library() {
  const [videos, setVideos] = useState<VideoListItem[]>([]);
  const [total, setTotal] = useState(0);
  const [query, setQuery] = useState('');
  const [status, setStatus] = useState<VideoStatus | ''>('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const page = await videoApi.search({ q: query, status });
      setVideos(page.items);
      setTotal(page.total);
    } catch {
      setError('Failed to load videos');
    } finally {
      setLoading(false);
    }
  }, [query, status]);

  useEffect(() => {
    const t = setTimeout(load, 250);
    return () => clearTimeout(t);
  }, [load]);

  return (
    <>
      <div className="topbar">
        <div>
          <h1 className="page-title">Library</h1>
          <p className="page-subtitle">
            {total} video{total === 1 ? '' : 's'}
          </p>
        </div>
        <Link to="/upload" className="btn btn-primary">
          + Upload video
        </Link>
      </div>

      <div className="content">
        <div className="toolbar">
          <input
            className="input search-box"
            placeholder="Search by title, summary, or transcript…"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
          <select
            className="select"
            value={status}
            onChange={(e) => setStatus(e.target.value as VideoStatus | '')}
          >
            {STATUS_OPTIONS.map((o) => (
              <option key={o.value} value={o.value}>
                {o.label}
              </option>
            ))}
          </select>
        </div>

        {error && <div className="error-banner">{error}</div>}

        {loading ? (
          <div className="center-loader">
            <span className="spinner" />
          </div>
        ) : videos.length > 0 ? (
          <div className="grid grid-videos">
            {videos.map((v) => (
              <VideoCard key={v.id} video={v} />
            ))}
          </div>
        ) : (
          <div className="empty-state card">
            <div className="big">🔍</div>
            <p>
              {query || status
                ? 'No videos match your filters.'
                : 'Your library is empty. Upload a video to get started.'}
            </p>
          </div>
        )}
      </div>
    </>
  );
}
