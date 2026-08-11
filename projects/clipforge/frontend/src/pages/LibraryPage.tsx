import { keepPreviousData, useQuery } from '@tanstack/react-query';
import { useEffect, useState } from 'react';
import { videoApi } from '../api/endpoints';
import { Spinner } from '../components/Spinner';
import { VideoCard } from '../components/VideoCard';
import type { VideoStatus } from '../types';

const STATUS_OPTIONS: (VideoStatus | '')[] = [
  '',
  'ready',
  'processing',
  'queued',
  'failed',
];

function useDebounced<T>(value: T, delay = 350): T {
  const [debounced, setDebounced] = useState(value);
  useEffect(() => {
    const t = setTimeout(() => setDebounced(value), delay);
    return () => clearTimeout(t);
  }, [value, delay]);
  return debounced;
}

export function LibraryPage() {
  const [search, setSearch] = useState('');
  const [status, setStatus] = useState<VideoStatus | ''>('');
  const debouncedSearch = useDebounced(search);

  const { data, isFetching } = useQuery({
    queryKey: ['videos', debouncedSearch, status],
    queryFn: () =>
      videoApi.list({
        q: debouncedSearch || undefined,
        status: status || undefined,
        limit: 60,
      }),
    placeholderData: keepPreviousData,
    refetchInterval: 5000,
  });

  const videos = data?.items ?? [];

  return (
    <>
      <div className="page-head">
        <div>
          <h1 className="page-title">Library</h1>
          <p className="page-sub">
            {data ? `${data.total} video${data.total === 1 ? '' : 's'}` : 'Loading…'}
          </p>
        </div>
      </div>

      <div className="toolbar">
        <div className="search-box">
          <span className="icon">⌕</span>
          <input
            className="input"
            placeholder="Search titles, summaries, transcripts…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        <select
          className="select"
          style={{ maxWidth: 180 }}
          value={status}
          onChange={(e) => setStatus(e.target.value as VideoStatus | '')}
        >
          {STATUS_OPTIONS.map((opt) => (
            <option key={opt} value={opt}>
              {opt === '' ? 'All statuses' : opt}
            </option>
          ))}
        </select>
        {isFetching ? <Spinner /> : null}
      </div>

      {videos.length === 0 ? (
        <div className="card empty">
          <div className="empty__icon">🔍</div>
          <p>No videos match your filters.</p>
        </div>
      ) : (
        <div className="video-grid">
          {videos.map((v) => (
            <VideoCard key={v.id} video={v} />
          ))}
        </div>
      )}
    </>
  );
}
