import { useEffect, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import {
  attachTag,
  deleteAsset,
  detachTag,
  getAsset,
  getDownloadUrl,
  resolveApiUrl,
  updateAsset,
} from '@/api/assets'
import { extractErrorMessage } from '@/api/client'
import { listFolders } from '@/api/folders'
import { listTags } from '@/api/tags'
import { ConfirmDialog } from '@/components/common/ConfirmDialog'
import { Drawer } from '@/components/common/Drawer'
import { MediaIcon } from '@/components/common/MediaIcon'
import { StatusBadge } from '@/components/common/StatusBadge'
import { TagPill } from '@/components/common/TagPill'
import { ShareManager } from '@/components/shares/ShareManager'
import { useToast } from '@/hooks/useToast'
import { formatBytes, formatDateTime, mediaKind } from '@/lib/format'
import { canWrite } from '@/lib/rbac'
import type { WorkspaceRole } from '@/types'

interface AssetDetailsDrawerProps {
  workspaceId: string
  assetId: string
  myRole: WorkspaceRole | null
  currentUserId: string | undefined
  onClose: () => void
}

export function AssetDetailsDrawer({
  workspaceId,
  assetId,
  myRole,
  currentUserId,
  onClose,
}: AssetDetailsDrawerProps) {
  const queryClient = useQueryClient()
  const { showToast } = useToast()
  const [filename, setFilename] = useState('')
  const [description, setDescription] = useState('')
  const [previewUrl, setPreviewUrl] = useState<string | null>(null)
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false)

  const assetQuery = useQuery({
    queryKey: ['asset', workspaceId, assetId],
    queryFn: () => getAsset(workspaceId, assetId),
  })
  const asset = assetQuery.data

  const tagsQuery = useQuery({ queryKey: ['tags', workspaceId], queryFn: () => listTags(workspaceId) })
  const foldersQuery = useQuery({
    queryKey: ['folders', workspaceId, null],
    queryFn: () => listFolders(workspaceId, null),
  })

  useEffect(() => {
    if (asset) {
      setFilename(asset.filename)
      setDescription(asset.description ?? '')
    }
  }, [asset])

  useEffect(() => {
    setPreviewUrl(null)
    getDownloadUrl(workspaceId, assetId)
      .then((res) => setPreviewUrl(resolveApiUrl(res.url)))
      .catch(() => setPreviewUrl(null))
  }, [workspaceId, assetId])

  const invalidateAssetLists = () => {
    queryClient.invalidateQueries({ queryKey: ['assets', workspaceId] })
    queryClient.invalidateQueries({ queryKey: ['search', workspaceId] })
    queryClient.invalidateQueries({ queryKey: ['folders', workspaceId] })
  }

  const updateMutation = useMutation({
    mutationFn: (payload: Parameters<typeof updateAsset>[2]) =>
      updateAsset(workspaceId, assetId, payload),
    onSuccess: (updated) => {
      queryClient.setQueryData(['asset', workspaceId, assetId], updated)
      invalidateAssetLists()
      showToast('Saved', 'success')
    },
    onError: (err) => showToast(extractErrorMessage(err, 'Could not save changes'), 'error'),
  })

  const deleteMutation = useMutation({
    mutationFn: () => deleteAsset(workspaceId, assetId),
    onSuccess: () => {
      invalidateAssetLists()
      showToast('Asset deleted', 'success')
      onClose()
    },
    onError: (err) => showToast(extractErrorMessage(err, 'Could not delete asset'), 'error'),
  })

  const attachTagMutation = useMutation({
    mutationFn: (tagId: string) => attachTag(workspaceId, assetId, tagId),
    onSuccess: (updated) => {
      queryClient.setQueryData(['asset', workspaceId, assetId], updated)
      invalidateAssetLists()
    },
  })

  const detachTagMutation = useMutation({
    mutationFn: (tagId: string) => detachTag(workspaceId, assetId, tagId),
    onSuccess: (updated) => {
      queryClient.setQueryData(['asset', workspaceId, assetId], updated)
      invalidateAssetLists()
    },
  })

  const canEdit = asset ? canWrite(myRole) && (myRole === 'ADMIN' || asset.owner_id === currentUserId) : false
  const canDownload = previewUrl !== null

  if (assetQuery.isLoading || !asset) {
    return (
      <Drawer onClose={onClose}>
        <div style={{ padding: 20 }}>
          <div className="mv-spinner" />
        </div>
      </Drawer>
    )
  }

  const kind = mediaKind(asset.content_type)
  const assignedTagIds = new Set(asset.tags.map((t) => t.id))

  return (
    <Drawer onClose={onClose}>
      <div
        className="mv-flex mv-items-center mv-justify-between"
        style={{ padding: '16px 20px', borderBottom: '1px solid var(--mv-border)' }}
      >
        <h2 style={{ fontSize: 15, margin: 0, fontWeight: 700 }}>Asset details</h2>
        <button className="mv-btn mv-btn-ghost mv-btn-icon" onClick={onClose} aria-label="Close">
          ✕
        </button>
      </div>

      <div style={{ padding: 20 }}>
        <div
          style={{
            aspectRatio: '16 / 10',
            background: 'var(--mv-surface-sunken)',
            borderRadius: 'var(--mv-radius-md)',
            marginBottom: 16,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            overflow: 'hidden',
          }}
        >
          {previewUrl && kind === 'image' ? (
            <img src={previewUrl} alt={asset.filename} style={{ width: '100%', height: '100%', objectFit: 'contain' }} />
          ) : previewUrl && kind === 'video' ? (
            <video src={previewUrl} controls style={{ width: '100%', height: '100%' }} />
          ) : previewUrl && kind === 'audio' ? (
            <audio src={previewUrl} controls style={{ width: '90%' }} />
          ) : (
            <div style={{ color: 'var(--mv-accent-700)' }}>
              <MediaIcon contentType={asset.content_type} size={40} />
            </div>
          )}
        </div>

        <div className="mv-flex mv-items-center mv-gap-2" style={{ marginBottom: 16 }}>
          <StatusBadge status={asset.status} />
          <span className="mv-faint" style={{ fontSize: 12 }}>
            {formatBytes(asset.size_bytes)} · {asset.content_type}
          </span>
        </div>

        <div className="mv-field">
          <label className="mv-label" htmlFor="asset-filename">
            Filename
          </label>
          <input
            id="asset-filename"
            className="mv-input"
            value={filename}
            onChange={(e) => setFilename(e.target.value)}
            disabled={!canEdit}
            onBlur={() => {
              if (canEdit && filename !== asset.filename && filename.trim()) {
                updateMutation.mutate({ filename })
              }
            }}
          />
        </div>

        <div className="mv-field">
          <label className="mv-label" htmlFor="asset-description">
            Description
          </label>
          <textarea
            id="asset-description"
            className="mv-textarea"
            rows={3}
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            disabled={!canEdit}
            onBlur={() => {
              if (canEdit && description !== (asset.description ?? '')) {
                updateMutation.mutate({ description })
              }
            }}
          />
        </div>

        <div className="mv-field">
          <label className="mv-label" htmlFor="asset-folder">
            Folder
          </label>
          <select
            id="asset-folder"
            className="mv-select"
            value={asset.folder_id ?? ''}
            disabled={!canEdit}
            onChange={(e) => updateMutation.mutate({ folder_id: e.target.value || null })}
          >
            <option value="">No folder (root)</option>
            {foldersQuery.data?.map((folder) => (
              <option key={folder.id} value={folder.id}>
                {folder.name}
              </option>
            ))}
          </select>
        </div>

        <div className="mv-field">
          <span className="mv-label">Tags</span>
          <div className="mv-flex mv-gap-2" style={{ flexWrap: 'wrap', marginBottom: 8 }}>
            {asset.tags.length === 0 && (
              <span className="mv-faint" style={{ fontSize: 12 }}>
                No tags applied.
              </span>
            )}
            {asset.tags.map((tag) => (
              <TagPill
                key={tag.id}
                tag={tag}
                onRemove={canEdit ? () => detachTagMutation.mutate(tag.id) : undefined}
              />
            ))}
          </div>
          {canEdit && tagsQuery.data && (
            <div className="mv-flex mv-gap-2" style={{ flexWrap: 'wrap' }}>
              {tagsQuery.data
                .filter((tag) => !assignedTagIds.has(tag.id))
                .map((tag) => (
                  <button
                    key={tag.id}
                    className="mv-tag-pill"
                    style={{ cursor: 'pointer', opacity: 0.7 }}
                    onClick={() => attachTagMutation.mutate(tag.id)}
                  >
                    <span className="mv-tag-dot" style={{ background: tag.color }} />+ {tag.name}
                  </button>
                ))}
            </div>
          )}
        </div>

        <div className="mv-card" style={{ padding: 12, marginBottom: 16, fontSize: 12 }}>
          <div className="mv-flex mv-justify-between" style={{ marginBottom: 4 }}>
            <span className="mv-faint">Uploaded</span>
            <span>{formatDateTime(asset.created_at)}</span>
          </div>
          <div className="mv-flex mv-justify-between" style={{ marginBottom: 4 }}>
            <span className="mv-faint">Updated</span>
            <span>{formatDateTime(asset.updated_at)}</span>
          </div>
          {asset.checksum_sha256 && (
            <div className="mv-flex mv-justify-between">
              <span className="mv-faint">SHA-256</span>
              <span className="mv-mono mv-truncate" style={{ maxWidth: 180 }} title={asset.checksum_sha256}>
                {asset.checksum_sha256.slice(0, 16)}…
              </span>
            </div>
          )}
        </div>

        <div className="mv-flex mv-gap-2" style={{ marginBottom: 20 }}>
          <a
            href={previewUrl ?? undefined}
            download={asset.original_filename}
            className="mv-btn mv-btn-secondary"
            style={{ flex: 1, opacity: canDownload ? 1 : 0.5, pointerEvents: canDownload ? 'auto' : 'none' }}
          >
            Download
          </a>
          {canEdit && (
            <button className="mv-btn mv-btn-danger" onClick={() => setShowDeleteConfirm(true)}>
              Delete
            </button>
          )}
        </div>

        {canWrite(myRole) && (
          <div>
            <h3 style={{ fontSize: 13, margin: '0 0 10px' }}>Share links</h3>
            <ShareManager workspaceId={workspaceId} assetId={assetId} />
          </div>
        )}
      </div>

      {showDeleteConfirm && (
        <ConfirmDialog
          title="Delete asset"
          message={`Delete "${asset.filename}"? This cannot be undone.`}
          confirmLabel="Delete"
          danger
          isLoading={deleteMutation.isPending}
          onCancel={() => setShowDeleteConfirm(false)}
          onConfirm={() => deleteMutation.mutate()}
        />
      )}
    </Drawer>
  )
}
