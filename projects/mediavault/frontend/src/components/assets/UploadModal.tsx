import { useRef, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { extractErrorMessage } from '@/api/client'
import { listFolders } from '@/api/folders'
import { uploadAsset } from '@/api/assets'
import { Modal } from '@/components/common/Modal'
import { useToast } from '@/hooks/useToast'

interface UploadModalProps {
  workspaceId: string
  defaultFolderId: string | null
  onClose: () => void
}

interface QueuedFile {
  file: File
  progress: number
  status: 'pending' | 'uploading' | 'done' | 'error'
  error?: string
}

export function UploadModal({ workspaceId, defaultFolderId, onClose }: UploadModalProps) {
  const [folderId, setFolderId] = useState<string | ''>(defaultFolderId ?? '')
  const [queue, setQueue] = useState<QueuedFile[]>([])
  const [isDragging, setIsDragging] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)
  const queryClient = useQueryClient()
  const { showToast } = useToast()

  const foldersQuery = useQuery({
    queryKey: ['folders', workspaceId, null],
    queryFn: () => listFolders(workspaceId, null),
  })

  const uploadMutation = useMutation({
    mutationFn: async (queuedFile: QueuedFile) => {
      return uploadAsset(workspaceId, {
        file: queuedFile.file,
        folderId: folderId || null,
        onProgress: (percent) => {
          setQueue((prev) =>
            prev.map((q) => (q.file === queuedFile.file ? { ...q, progress: percent } : q)),
          )
        },
      })
    },
  })

  const addFiles = (files: FileList | null) => {
    if (!files) return
    const next = Array.from(files).map<QueuedFile>((file) => ({
      file,
      progress: 0,
      status: 'pending',
    }))
    setQueue((prev) => [...prev, ...next])
  }

  const startUploads = async () => {
    for (const queuedFile of queue) {
      if (queuedFile.status !== 'pending') continue
      setQueue((prev) =>
        prev.map((q) => (q.file === queuedFile.file ? { ...q, status: 'uploading' } : q)),
      )
      try {
        await uploadMutation.mutateAsync(queuedFile)
        setQueue((prev) =>
          prev.map((q) => (q.file === queuedFile.file ? { ...q, status: 'done', progress: 100 } : q)),
        )
      } catch (err) {
        setQueue((prev) =>
          prev.map((q) =>
            q.file === queuedFile.file
              ? { ...q, status: 'error', error: extractErrorMessage(err, 'Upload failed') }
              : q,
          ),
        )
      }
    }
    queryClient.invalidateQueries({ queryKey: ['assets', workspaceId] })
    queryClient.invalidateQueries({ queryKey: ['search', workspaceId] })
    queryClient.invalidateQueries({ queryKey: ['folders', workspaceId] })
    showToast('Upload complete', 'success')
  }

  const allDone = queue.length > 0 && queue.every((q) => q.status === 'done' || q.status === 'error')
  const isUploading = queue.some((q) => q.status === 'uploading')

  return (
    <Modal
      title="Upload media"
      onClose={onClose}
      width={520}
      footer={
        allDone ? (
          <button className="mv-btn mv-btn-primary" onClick={onClose}>
            Done
          </button>
        ) : (
          <>
            <button className="mv-btn mv-btn-secondary" onClick={onClose} disabled={isUploading}>
              Cancel
            </button>
            <button
              className="mv-btn mv-btn-primary"
              onClick={startUploads}
              disabled={queue.length === 0 || isUploading}
            >
              {isUploading ? 'Uploading…' : `Upload ${queue.length || ''}`.trim()}
            </button>
          </>
        )
      }
    >
      <div className="mv-field">
        <label className="mv-label" htmlFor="upload-folder">
          Destination folder
        </label>
        <select
          id="upload-folder"
          className="mv-select"
          value={folderId}
          onChange={(e) => setFolderId(e.target.value)}
        >
          <option value="">No folder (root)</option>
          {foldersQuery.data?.map((folder) => (
            <option key={folder.id} value={folder.id}>
              {folder.name}
            </option>
          ))}
        </select>
      </div>

      <div
        onDragOver={(e) => {
          e.preventDefault()
          setIsDragging(true)
        }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={(e) => {
          e.preventDefault()
          setIsDragging(false)
          addFiles(e.dataTransfer.files)
        }}
        onClick={() => inputRef.current?.click()}
        style={{
          border: `2px dashed ${isDragging ? 'var(--mv-accent-600)' : 'var(--mv-border-strong)'}`,
          borderRadius: 'var(--mv-radius-md)',
          padding: 28,
          textAlign: 'center',
          cursor: 'pointer',
          background: isDragging ? 'var(--mv-accent-50)' : 'var(--mv-surface-alt)',
          marginBottom: 16,
        }}
      >
        <p style={{ margin: 0, fontWeight: 600 }}>Drop video, image, or audio files here</p>
        <p className="mv-faint" style={{ margin: '4px 0 0', fontSize: 12 }}>
          or click to browse
        </p>
        <input
          ref={inputRef}
          type="file"
          multiple
          accept="video/*,image/*,audio/*"
          style={{ display: 'none' }}
          onChange={(e) => addFiles(e.target.files)}
        />
      </div>

      {queue.length > 0 && (
        <div className="mv-flex-col mv-gap-2">
          {queue.map((q, idx) => (
            <div key={idx} className="mv-card" style={{ padding: '10px 12px' }}>
              <div className="mv-flex mv-items-center mv-justify-between" style={{ marginBottom: 6 }}>
                <span className="mv-truncate" style={{ fontSize: 13, maxWidth: 320 }}>
                  {q.file.name}
                </span>
                <span className="mv-faint" style={{ fontSize: 11 }}>
                  {q.status === 'error' ? 'Failed' : q.status === 'done' ? 'Done' : `${q.progress}%`}
                </span>
              </div>
              <div
                style={{
                  height: 5,
                  borderRadius: 999,
                  background: 'var(--mv-surface-sunken)',
                  overflow: 'hidden',
                }}
              >
                <div
                  style={{
                    height: '100%',
                    width: `${q.status === 'done' ? 100 : q.progress}%`,
                    background: q.status === 'error' ? 'var(--mv-red-600)' : 'var(--mv-accent-600)',
                    transition: 'width 150ms ease',
                  }}
                />
              </div>
              {q.error && <p className="mv-error-text" style={{ margin: '6px 0 0' }}>{q.error}</p>}
            </div>
          ))}
        </div>
      )}
    </Modal>
  )
}
