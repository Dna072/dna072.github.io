import { Link } from 'react-router-dom';
import type { Video } from '../types';
import { formatDuration, timeAgo } from '../utils/format';
import { StatusBadge } from './StatusBadge';

interface Props {
  video: Video;
}

export function VideoCard({ video }: Props) {
  return (
    <Link to={`/videos/${video.id}`} className="card video-card">
      <div className="thumb">
        <span>▶</span>
        <div className="thumb__status">
          <StatusBadge status={video.status} />
        </div>
        {video.duration_seconds ? (
          <div className="thumb__duration">{formatDuration(video.duration_seconds)}</div>
        ) : null}
      </div>
      <div className="video-card__body">
        <div className="video-card__title">{video.title}</div>
        {video.tags && video.tags.length > 0 ? (
          <div className="tag-row">
            {video.tags.slice(0, 3).map((tag) => (
              <span key={tag} className="tag">
                {tag}
              </span>
            ))}
          </div>
        ) : null}
        <div className="video-card__meta">
          <span>{timeAgo(video.created_at)}</span>
        </div>
      </div>
    </Link>
  );
}
