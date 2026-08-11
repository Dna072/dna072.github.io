import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { videoApi } from '../api/endpoints';
import { FullPageSpinner } from '../components/Spinner';
import { StatusBadge } from '../components/StatusBadge';
import { ProgressBar } from '../components/ProgressBar';
import { formatBytes, formatDate, formatDuration } from '../utils/format';

export function VideoDetailPage() {
  const { id = '' } = useParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const { data: video, isLoading } = useQuery({
    queryKey: ['video', id],
    queryFn: () => videoApi.get(id),
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      return status === 'ready' || status === 'failed' ? false : 2500;
    },
  });

  const isProcessing =
    video && (video.status === 'processing' || video.status === 'queued');

  const { data: job } = useQuery({
    queryKey: ['video-job', id],
    queryFn: () => videoApi.job(id),
    enabled: Boolean(video),
    refetchInterval: isProcessing ? 2000 : false,
  });

  const reprocess = useMutation({
    mutationFn: () => videoApi.reprocess(id),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['video', id] });
      void queryClient.invalidateQueries({ queryKey: ['video-job', id] });
    },
  });

  const remove = useMutation({
    mutationFn: () => videoApi.remove(id),
    onSuccess: () => navigate('/library'),
  });

  if (isLoading || !video) return <FullPageSpinner />;

  return (
    <>
      <div className="page-head">
        <div>
          <Link to="/library" style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
            ← Back to library
          </Link>
          <h1 className="page-title" style={{ marginTop: 6 }}>
            {video.title}
          </h1>
          <div style={{ display: 'flex', gap: 10, alignItems: 'center', marginTop: 8 }}>
            <StatusBadge status={video.status} />
            <span className="page-sub" style={{ margin: 0 }}>
              Uploaded {formatDate(video.created_at)}
            </span>
          </div>
        </div>
        <div style={{ display: 'flex', gap: 10 }}>
          <button
            className="btn btn-ghost"
            onClick={() => reprocess.mutate()}
            disabled={reprocess.isPending}
          >
            Reprocess
          </button>
          <button
            className="btn btn-danger"
            onClick={() => {
              if (confirm('Delete this video permanently?')) remove.mutate();
            }}
          >
            Delete
          </button>
        </div>
      </div>

      {video.status === 'failed' && video.error_message ? (
        <div className="alert alert-error">Processing failed: {video.error_message}</div>
      ) : null}

      {isProcessing && job ? (
        <div className="card" style={{ padding: '18px 20px', marginBottom: 24 }}>
          <div className="section-title">
            ⚙️ Processing — {job.stage} ({job.progress}%)
          </div>
          <ProgressBar value={job.progress} />
        </div>
      ) : null}

      <div className="detail-grid">
        <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
          {video.summary ? (
            <div className="card" style={{ padding: '18px 20px' }}>
              <div className="section-title">✦ AI Summary</div>
              <p style={{ color: 'var(--text-muted)', lineHeight: 1.7 }}>{video.summary}</p>
            </div>
          ) : null}

          {video.chapters && video.chapters.length > 0 ? (
            <div className="card" style={{ padding: '18px 20px' }}>
              <div className="section-title">☰ Chapters</div>
              {video.chapters.map((c, i) => (
                <div className="chapter" key={i}>
                  <span className="chapter__time">{formatDuration(c.start)}</span>
                  <span>{c.title}</span>
                </div>
              ))}
            </div>
          ) : null}

          {video.transcript ? (
            <div className="card" style={{ padding: '18px 20px' }}>
              <div className="section-title">🗎 Transcript</div>
              <div className="transcript">{video.transcript}</div>
            </div>
          ) : null}
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
          <div className="card" style={{ padding: '18px 20px' }}>
            <div className="section-title">Details</div>
            <div className="kv">
              <span className="kv__k">Duration</span>
              <span>{formatDuration(video.duration_seconds)}</span>
            </div>
            <div className="kv">
              <span className="kv__k">Resolution</span>
              <span>
                {video.width && video.height ? `${video.width}×${video.height}` : '—'}
              </span>
            </div>
            <div className="kv">
              <span className="kv__k">Size</span>
              <span>{formatBytes(video.size_bytes)}</span>
            </div>
            <div className="kv">
              <span className="kv__k">Format</span>
              <span>{video.content_type}</span>
            </div>
            <div className="kv">
              <span className="kv__k">Filename</span>
              <span
                style={{
                  maxWidth: 160,
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  whiteSpace: 'nowrap',
                }}
              >
                {video.original_filename}
              </span>
            </div>
          </div>

          {video.tags && video.tags.length > 0 ? (
            <div className="card" style={{ padding: '18px 20px' }}>
              <div className="section-title"># Tags</div>
              <div className="tag-row">
                {video.tags.map((t) => (
                  <span key={t} className="tag">
                    {t}
                  </span>
                ))}
              </div>
            </div>
          ) : null}

          {job?.stage_history && job.stage_history.length > 0 ? (
            <div className="card" style={{ padding: '18px 20px' }}>
              <div className="section-title">Pipeline timeline</div>
              <div className="timeline">
                {job.stage_history.map((entry, i) => (
                  <div className="timeline__item" key={i}>
                    <span className="timeline__stage">{entry.stage}</span>
                    <span className="timeline__note">{entry.note}</span>
                  </div>
                ))}
              </div>
            </div>
          ) : null}
        </div>
      </div>
    </>
  );
}
