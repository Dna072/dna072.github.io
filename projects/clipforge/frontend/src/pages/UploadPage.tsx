import { useQuery } from '@tanstack/react-query';
import { DragEvent, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { apiErrorMessage } from '../api/client';
import { videoApi, workspaceApi } from '../api/endpoints';
import { ProgressBar } from '../components/ProgressBar';
import { formatBytes } from '../utils/format';

export function UploadPage() {
  const navigate = useNavigate();
  const inputRef = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [workspaceId, setWorkspaceId] = useState('');
  const [dragging, setDragging] = useState(false);
  const [progress, setProgress] = useState(0);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState('');

  const { data: workspaces } = useQuery({
    queryKey: ['workspaces'],
    queryFn: workspaceApi.list,
  });

  const activeWorkspace = workspaceId || workspaces?.[0]?.id || '';

  function onDrop(e: DragEvent) {
    e.preventDefault();
    setDragging(false);
    const dropped = e.dataTransfer.files?.[0];
    if (dropped) {
      setFile(dropped);
      if (!title) setTitle(dropped.name.replace(/\.[^.]+$/, ''));
    }
  }

  async function onSubmit() {
    if (!file || !activeWorkspace) {
      setError('Select a workspace and a video file.');
      return;
    }
    setError('');
    setUploading(true);
    setProgress(0);
    try {
      const res = await videoApi.upload(
        activeWorkspace,
        file,
        { title: title || undefined, description: description || undefined },
        setProgress,
      );
      navigate(`/videos/${res.video.id}`);
    } catch (err) {
      setError(apiErrorMessage(err));
      setUploading(false);
    }
  }

  return (
    <>
      <div className="page-head">
        <div>
          <h1 className="page-title">Upload video</h1>
          <p className="page-sub">
            Your video will be queued for AI processing — transcript, summary, chapters & tags.
          </p>
        </div>
      </div>

      <div style={{ maxWidth: 640 }}>
        {error ? <div className="alert alert-error">{error}</div> : null}

        <div
          className={`dropzone${dragging ? ' drag' : ''}`}
          onClick={() => inputRef.current?.click()}
          onDragOver={(e) => {
            e.preventDefault();
            setDragging(true);
          }}
          onDragLeave={() => setDragging(false)}
          onDrop={onDrop}
        >
          <div className="dropzone__icon">{file ? '🎞️' : '⬆️'}</div>
          {file ? (
            <>
              <strong>{file.name}</strong>
              <div style={{ color: 'var(--text-muted)', marginTop: 4 }}>
                {formatBytes(file.size)}
              </div>
            </>
          ) : (
            <>
              <strong>Drop a video here or click to browse</strong>
              <div style={{ color: 'var(--text-muted)', marginTop: 4 }}>
                MP4, MOV, MKV, WEBM, AVI, M4V
              </div>
            </>
          )}
          <input
            ref={inputRef}
            type="file"
            accept="video/*,.mp4,.mov,.mkv,.webm,.avi,.m4v"
            hidden
            onChange={(e) => {
              const selected = e.target.files?.[0] ?? null;
              setFile(selected);
              if (selected && !title) setTitle(selected.name.replace(/\.[^.]+$/, ''));
            }}
          />
        </div>

        <div style={{ marginTop: 22 }}>
          <div className="field">
            <label>Workspace</label>
            <select
              className="select"
              value={activeWorkspace}
              onChange={(e) => setWorkspaceId(e.target.value)}
            >
              {workspaces?.map((w) => (
                <option key={w.id} value={w.id}>
                  {w.name}
                </option>
              ))}
            </select>
          </div>
          <div className="field">
            <label>Title</label>
            <input
              className="input"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Optional — derived from filename"
            />
          </div>
          <div className="field">
            <label>Description</label>
            <textarea
              className="textarea"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Optional notes about this video"
            />
          </div>

          {uploading ? (
            <div style={{ marginBottom: 16 }}>
              <ProgressBar value={progress} />
              <div style={{ color: 'var(--text-muted)', fontSize: '0.82rem', marginTop: 6 }}>
                Uploading… {progress}%
              </div>
            </div>
          ) : null}

          <button
            className="btn btn-primary"
            onClick={onSubmit}
            disabled={uploading || !file}
          >
            {uploading ? 'Uploading…' : 'Upload & process'}
          </button>
        </div>
      </div>
    </>
  );
}
