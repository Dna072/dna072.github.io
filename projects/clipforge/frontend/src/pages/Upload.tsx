import { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { workspaceApi } from '@/api';
import { tokenStore } from '@/api/client';
import { formatBytes } from '@/lib/format';
import type { Project, Workspace } from '@/types';

function uploadWithProgress(
  projectId: string,
  file: File,
  title: string,
  onProgress: (pct: number) => void,
): Promise<{ id: string }> {
  return new Promise((resolve, reject) => {
    const form = new FormData();
    form.append('project_id', projectId);
    form.append('file', file);
    if (title) form.append('title', title);

    const xhr = new XMLHttpRequest();
    xhr.open('POST', '/api/v1/videos');
    if (tokenStore.access) {
      xhr.setRequestHeader('Authorization', `Bearer ${tokenStore.access}`);
    }
    xhr.upload.onprogress = (e) => {
      if (e.lengthComputable) onProgress(Math.round((e.loaded / e.total) * 100));
    };
    xhr.onload = () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        resolve(JSON.parse(xhr.responseText));
      } else {
        try {
          const body = JSON.parse(xhr.responseText);
          reject(new Error(body?.error?.detail ?? body?.detail ?? 'Upload failed'));
        } catch {
          reject(new Error('Upload failed'));
        }
      }
    };
    xhr.onerror = () => reject(new Error('Network error during upload'));
    xhr.send(form);
  });
}

export function Upload() {
  const navigate = useNavigate();
  const fileInput = useRef<HTMLInputElement>(null);
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [projectId, setProjectId] = useState('');
  const [file, setFile] = useState<File | null>(null);
  const [title, setTitle] = useState('');
  const [dragging, setDragging] = useState(false);
  const [progress, setProgress] = useState(0);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function bootstrap() {
      try {
        const ws = await workspaceApi.list();
        setWorkspaces(ws);
        if (ws.length === 0) return;
        let projs = await workspaceApi.listProjects(ws[0].id);
        if (projs.length === 0) {
          const created = await workspaceApi.createProject(ws[0].id, 'My First Project');
          projs = [created];
        }
        setProjects(projs);
        setProjectId(projs[0].id);
      } catch {
        setError('Failed to load workspaces');
      }
    }
    bootstrap();
  }, []);

  const pickFile = (f: File | null) => {
    setError(null);
    if (!f) return;
    setFile(f);
    if (!title) setTitle(f.name.replace(/\.[^.]+$/, ''));
  };

  const submit = async () => {
    if (!file || !projectId) return;
    setUploading(true);
    setError(null);
    setProgress(0);
    try {
      const video = await uploadWithProgress(projectId, file, title, setProgress);
      navigate(`/videos/${video.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Upload failed');
      setUploading(false);
    }
  };

  return (
    <>
      <div className="topbar">
        <div>
          <h1 className="page-title">Upload video</h1>
          <p className="page-subtitle">
            We&apos;ll extract metadata, thumbnails, a transcript, and AI insights
            automatically
          </p>
        </div>
      </div>

      <div className="content" style={{ maxWidth: 720 }}>
        {error && <div className="error-banner">{error}</div>}
        {workspaces.length === 0 && !error && (
          <div className="center-loader">
            <span className="spinner" />
          </div>
        )}

        {workspaces.length > 0 && (
          <div className="card">
            <div className="field">
              <label htmlFor="project">Project</label>
              <select
                id="project"
                className="select"
                value={projectId}
                onChange={(e) => setProjectId(e.target.value)}
              >
                {projects.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.name}
                  </option>
                ))}
              </select>
            </div>

            <div
              className={`dropzone ${dragging ? 'drag' : ''}`}
              onClick={() => fileInput.current?.click()}
              onDragOver={(e) => {
                e.preventDefault();
                setDragging(true);
              }}
              onDragLeave={() => setDragging(false)}
              onDrop={(e) => {
                e.preventDefault();
                setDragging(false);
                pickFile(e.dataTransfer.files[0] ?? null);
              }}
            >
              {file ? (
                <div>
                  <div style={{ fontSize: 32 }}>🎬</div>
                  <div style={{ fontWeight: 600, marginTop: 8 }}>{file.name}</div>
                  <div className="muted" style={{ fontSize: 13 }}>
                    {formatBytes(file.size)}
                  </div>
                </div>
              ) : (
                <div>
                  <div style={{ fontSize: 32 }}>↑</div>
                  <div style={{ fontWeight: 600, marginTop: 8 }}>
                    Drag &amp; drop a video, or click to browse
                  </div>
                  <div className="muted" style={{ fontSize: 13, marginTop: 4 }}>
                    MP4, MOV, MKV, WEBM, AVI, M4V · up to 500 MB
                  </div>
                </div>
              )}
              <input
                ref={fileInput}
                type="file"
                accept="video/*"
                hidden
                onChange={(e) => pickFile(e.target.files?.[0] ?? null)}
              />
            </div>

            <div className="field" style={{ marginTop: 18 }}>
              <label htmlFor="title">Title</label>
              <input
                id="title"
                className="input"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="Video title"
              />
            </div>

            {uploading && (
              <div style={{ margin: '8px 0 16px' }}>
                <div className="row between" style={{ marginBottom: 6, fontSize: 13 }}>
                  <span className="muted">Uploading…</span>
                  <span className="mono">{progress}%</span>
                </div>
                <div className="progress">
                  <div className="progress-bar" style={{ width: `${progress}%` }} />
                </div>
              </div>
            )}

            <button
              className="btn btn-primary btn-block"
              disabled={!file || !projectId || uploading}
              onClick={submit}
            >
              {uploading ? <span className="spinner" /> : 'Upload & process'}
            </button>
          </div>
        )}
      </div>
    </>
  );
}
