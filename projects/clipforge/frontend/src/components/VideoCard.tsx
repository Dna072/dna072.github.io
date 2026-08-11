import { Link } from 'react-router-dom';

import { mediaUrl } from '@/api/client';
import { StatusBadge } from '@/components/StatusBadge';
import { formatDuration, formatRelative } from '@/lib/format';
import type { VideoListItem } from '@/types';

export function VideoCard({ video }: { video: VideoListItem }) {
  const thumb = mediaUrl(video.thumbnail_path);
  return (
    <Link to={`/videos/${video.id}`} className="card card-hover">
      <div className="video-thumb">
        {thumb ? <img src={thumb} alt={video.title} /> : <span>▶</span>}
        {video.duration_seconds ? (
          <span className="video-duration">{formatDuration(video.duration_seconds)}</span>
        ) : null}
      </div>
      <div className="video-title">{video.title}</div>
      <div className="row between">
        <StatusBadge status={video.status} />
        <span className="muted" style={{ fontSize: 12 }}>
          {formatRelative(video.created_at)}
        </span>
      </div>
      {video.tags && video.tags.length > 0 ? (
        <div className="tag-row" style={{ marginTop: 12 }}>
          {video.tags.slice(0, 3).map((t) => (
            <span key={t} className="tag">
              {t}
            </span>
          ))}
        </div>
      ) : null}
    </Link>
  );
}
