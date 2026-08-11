import { useCallback, useEffect, useRef, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';

import { videoApi } from '@/api';
import { StatusBadge } from '@/components/StatusBadge';
import { formatBytes, formatDate, formatDuration } from '@/lib/format';
import type { Job, JobStep, Video } from '@/types';

const STEP_LABELS: Record<string, string> = {
  metadata: 'Extract metadata',
  thumbnail: 'Generate thumbnail',
  audio: 'Extract audio',
  transcript: 'Transcribe speech',
  ai_insights: 'AI summary, chapters & tags',
};

const STEP_ICON: Record<JobStep['status'], string> = {
  succeeded: '✓',
  running: '●',
  pending: '○',
  failed: '✕',
  skipped: '–',
};

function PipelineSteps({ job }: { job: Job }) {
  return (
    <div className="steps">
      {(job.steps ?? []).map((step) => (
        <div className="step" key={step.name}>
          <span className={`step-icon ${step.status}`}>{STEP_ICON[step.status]}</span>
          <div style={{ flex: 1 }}>
            <div style={{ fontWeight: 500 }}>{STEP_LABELS[step.name] ?? step.name}</div>
            {step.detail && (
              <div className="muted" style={{ fontSize: 12 }}>
                {step.detail}
              </div>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}

export function VideoDetail() {
  const { id = '' } = useParams();
  const navigate = useNavigate();
  const [video, setVideo] = useState<Video | null>(null);
  const [job, setJob] = useState<Job | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const load = useCallback(async () => {
    try {
      const v = await videoApi.get(id);
      setVideo(v);
      try {
        setJob(await videoApi.status(id));
      } catch {
        setJob(null);
      }
      return v;
    } catch {
      setError('Video not found');
      return null;
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    load();
  }, [load]);

  // Poll while the video is still being processed.
  useEffect(() => {
    const active = video?.status === 'queued' || video?.status === 'processing';
    if (active && !pollRef.current) {
      pollRef.current = setInterval(load, 2000);
    }
    if (!active && pollRef.current) {
      clearInterval(pollRef.current);
      pollRef.current = null;
    }
    return () => {
      if (pollRef.current) {
        clearInterval(pollRef.current);
        pollRef.current = null;
      }
    };
  }, [video?.status, load]);

  const handleReprocess = async () => {
    await videoApi.reprocess(id);
    await load();
  };

  const handleDelete = async () => {
    if (!confirm('Delete this video? This cannot be undone.')) return;
    await videoApi.remove(id);
    navigate('/library');
  };

  if (loading) {
    return (
      <div className="center-loader">
        <span className="spinner" />
      </div>
    );
  }

  if (error || !video) {
    return (
      <div className="content">
        <div className="error-banner">{error ?? 'Video not found'}</div>
        <Link to="/library" className="btn btn-ghost">
          ← Back to library
        </Link>
      </div>
    );
  }

  const isProcessing = video.status === 'queued' || video.status === 'processing';

  return (
    <>
      <div className="topbar">
        <div className="row" style={{ gap: 14 }}>
          <Link to="/library" className="btn btn-ghost btn-sm">
            ←
          </Link>
          <div>
            <h1 className="page-title">{video.title}</h1>
            <div className="row" style={{ gap: 10, marginTop: 4 }}>
              <StatusBadge status={video.status} />
              <span className="muted" style={{ fontSize: 13 }}>
                {formatDate(video.created_at)}
              </span>
            </div>
          </div>
        </div>
        <div className="row">
          <button className="btn btn-ghost btn-sm" onClick={handleReprocess}>
            ↻ Reprocess
          </button>
          <button className="btn btn-danger btn-sm" onClick={handleDelete}>
            Delete
          </button>
        </div>
      </div>

      <div className="content">
        {video.status === 'failed' && video.error_message && (
          <div className="error-banner">Processing failed: {video.error_message}</div>
        )}

        <div className="detail-grid">
          <div>
            <div className="player-frame">
              {video.thumbnail_path ? (
                <img
                  src={`/media/${video.thumbnail_path}`}
                  alt={video.title}
                  style={{ maxWidth: '100%', maxHeight: '100%', borderRadius: 12 }}
                />
              ) : (
                <div style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: 46 }}>▶</div>
                  <div className="muted">Player placeholder</div>
                </div>
              )}
            </div>

            {video.summary && (
              <div className="section">
                <h2 className="section-title">AI Summary</h2>
                <div className="card">{video.summary}</div>
              </div>
            )}

            {video.tags && video.tags.length > 0 && (
              <div className="section">
                <h2 className="section-title">Tags</h2>
                <div className="tag-row">
                  {video.tags.map((t) => (
                    <span key={t} className="tag">
                      {t}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {video.transcript && (
              <div className="section">
                <h2 className="section-title">Transcript</h2>
                <div className="card transcript">{video.transcript}</div>
              </div>
            )}
          </div>

          <div>
            {isProcessing && job && (
              <div className="card" style={{ marginBottom: 22 }}>
                <div className="row between" style={{ marginBottom: 14 }}>
                  <h2 className="section-title" style={{ margin: 0 }}>
                    Processing
                  </h2>
                  <span className="spinner" />
                </div>
                <PipelineSteps job={job} />
              </div>
            )}

            <div className="card">
              <h2 className="section-title">Details</h2>
              <div className="meta-row">
                <span className="k">Duration</span>
                <span className="mono">{formatDuration(video.duration_seconds)}</span>
              </div>
              <div className="meta-row">
                <span className="k">Resolution</span>
                <span className="mono">
                  {video.width && video.height ? `${video.width}×${video.height}` : '—'}
                </span>
              </div>
              <div className="meta-row">
                <span className="k">Codec</span>
                <span className="mono">{video.codec ?? '—'}</span>
              </div>
              <div className="meta-row">
                <span className="k">Frame rate</span>
                <span className="mono">
                  {video.frame_rate ? `${video.frame_rate} fps` : '—'}
                </span>
              </div>
              <div className="meta-row">
                <span className="k">File size</span>
                <span className="mono">{formatBytes(video.size_bytes)}</span>
              </div>
              <div className="meta-row" style={{ borderBottom: 'none' }}>
                <span className="k">Filename</span>
                <span className="mono" style={{ fontSize: 12 }}>
                  {video.original_filename}
                </span>
              </div>
            </div>

            {video.chapters && video.chapters.length > 0 && (
              <div className="card" style={{ marginTop: 22 }}>
                <h2 className="section-title">Chapters</h2>
                {video.chapters.map((c, i) => (
                  <div className="chapter" key={i}>
                    <span className="chapter-time">{formatDuration(c.start)}</span>
                    <span>{c.title}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </>
  );
}
