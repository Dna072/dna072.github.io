import { useQuery } from '@tanstack/react-query';
import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { fetchThumbnailBlob, fetchVideos } from '../api/client';
import { EmptyState, ErrorState, LoadingState } from '../components/EmptyState';
import { StatusBadge } from '../components/StatusBadge';
import { formatBytes, formatDuration, formatRelativeTime } from '../utils/format';

function VideoThumbnail({ videoId }: { videoId: string }) {
  const [src, setSrc] = useState<string | null>(null);

  useEffect(() => {
    let objectUrl: string | null = null;
    fetchThumbnailBlob(videoId).then((url) => {
      if (url) {
        objectUrl = url;
        setSrc(url);
      }
    });
    return () => {
      if (objectUrl) URL.revokeObjectURL(objectUrl);
    };
  }, [videoId]);

  if (!src) {
    return (
      <div className="video-card__thumb video-card__thumb--placeholder" aria-hidden="true">
        ▶
      </div>
    );
  }

  return <img src={src} alt="" className="video-card__thumb" />;
}

export function VideosPage() {
  const [query, setQuery] = useState('');
  const [debouncedQuery, setDebouncedQuery] = useState('');

  useEffect(() => {
    const timer = setTimeout(() => setDebouncedQuery(query.trim()), 300);
    return () => clearTimeout(timer);
  }, [query]);

  const { data, isLoading, error, refetch, isFetching } = useQuery({
    queryKey: ['videos', debouncedQuery],
    queryFn: () => fetchVideos({ q: debouncedQuery || undefined, limit: 50 }),
  });

  return (
    <div className="videos-page">
      <header className="page-header">
        <div>
          <h2>Video library</h2>
          <p className="page-header__subtitle">
            Search and browse processed media across your workspaces.
          </p>
        </div>
        <Link to="/videos/upload" className="btn btn-primary">
          Upload
        </Link>
      </header>

      <div className="search-bar">
        <input
          type="search"
          placeholder="Search by title, filename, or transcript…"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          aria-label="Search videos"
        />
        {isFetching && !isLoading && <span className="search-bar__hint">Searching…</span>}
      </div>

      {isLoading && <LoadingState message="Loading videos…" />}
      {error && <ErrorState message={(error as Error).message} onRetry={() => refetch()} />}

      {data && data.items.length === 0 && (
        <EmptyState
          title={debouncedQuery ? 'No matches found' : 'Your library is empty'}
          description={
            debouncedQuery
              ? 'Try a different search term or clear the filter.'
              : 'Upload a video to start building your library.'
          }
          action={
            !debouncedQuery ? (
              <Link to="/videos/upload" className="btn btn-primary">
                Upload video
              </Link>
            ) : undefined
          }
        />
      )}

      {data && data.items.length > 0 && (
        <>
          <p className="results-meta">
            {data.total} video{data.total !== 1 ? 's' : ''}
            {debouncedQuery ? ` matching “${debouncedQuery}”` : ''}
          </p>
          <div className="video-grid">
            {data.items.map((video) => (
              <Link key={video.id} to={`/videos/${video.id}`} className="video-card">
                <VideoThumbnail videoId={video.id} />
                <div className="video-card__body">
                  <h3 className="video-card__title">{video.title}</h3>
                  <p className="video-card__filename">{video.original_filename}</p>
                  <div className="video-card__meta">
                    <StatusBadge status={video.status} />
                    <span className="mono">{formatDuration(video.duration_seconds)}</span>
                    <span>{formatBytes(video.size_bytes)}</span>
                  </div>
                  <time className="video-card__time">{formatRelativeTime(video.created_at)}</time>
                </div>
              </Link>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
