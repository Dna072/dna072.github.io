import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { extractErrorMessage } from '@/api/client'
import { createShare, listShares, revokeShare } from '@/api/shares'
import { useToast } from '@/hooks/useToast'
import { formatDateTime } from '@/lib/format'
import type { SharePermission } from '@/types'

export function ShareManager({ workspaceId, assetId }: { workspaceId: string; assetId: string }) {
  const [permission, setPermission] = useState<SharePermission>('VIEW')
  const queryClient = useQueryClient()
  const { showToast } = useToast()

  const sharesQuery = useQuery({
    queryKey: ['shares', workspaceId, assetId],
    queryFn: () => listShares(workspaceId, assetId),
  })

  const createMutation = useMutation({
    mutationFn: () => createShare(workspaceId, assetId, { permission }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['shares', workspaceId, assetId] })
    },
    onError: (err) => showToast(extractErrorMessage(err, 'Could not create share link'), 'error'),
  })

  const revokeMutation = useMutation({
    mutationFn: (shareId: string) => revokeShare(workspaceId, shareId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['shares', workspaceId, assetId] })
    },
  })

  const copyLink = (token: string) => {
    const url = `${window.location.origin}/share/${token}`
    navigator.clipboard.writeText(url).then(
      () => showToast('Share link copied to clipboard', 'success'),
      () => showToast(url, 'info'),
    )
  }

  return (
    <div>
      <div className="mv-flex mv-gap-2" style={{ marginBottom: 10 }}>
        <select
          className="mv-select"
          value={permission}
          onChange={(e) => setPermission(e.target.value as SharePermission)}
          style={{ flex: 1 }}
        >
          <option value="VIEW">View only</option>
          <option value="DOWNLOAD">Allow download</option>
        </select>
        <button
          className="mv-btn mv-btn-secondary mv-btn-sm"
          onClick={() => createMutation.mutate()}
          disabled={createMutation.isPending}
        >
          {createMutation.isPending ? 'Creating…' : 'Create link'}
        </button>
      </div>

      {sharesQuery.data?.length ? (
        <div className="mv-flex-col mv-gap-2">
          {sharesQuery.data.map((share) => (
            <div
              key={share.id}
              className="mv-card"
              style={{ padding: '8px 10px', display: 'flex', alignItems: 'center', gap: 8 }}
            >
              <div style={{ flex: 1, minWidth: 0 }}>
                <div className="mv-flex mv-items-center mv-gap-2">
                  <span
                    className="mv-badge"
                    style={{
                      background: share.is_active ? 'var(--mv-accent-100)' : 'var(--mv-surface-sunken)',
                      color: share.is_active ? 'var(--mv-accent-800)' : 'var(--mv-text-faint)',
                    }}
                  >
                    {share.is_active ? 'Active' : 'Inactive'}
                  </span>
                  <span className="mv-faint" style={{ fontSize: 11 }}>
                    {share.permission === 'DOWNLOAD' ? 'Can download' : 'View only'}
                  </span>
                </div>
                <div className="mv-faint" style={{ fontSize: 11, marginTop: 2 }}>
                  {share.expires_at ? `Expires ${formatDateTime(share.expires_at)}` : 'Never expires'}
                </div>
              </div>
              {share.is_active && (
                <>
                  <button
                    className="mv-btn mv-btn-ghost mv-btn-sm"
                    onClick={() => copyLink(share.token)}
                  >
                    Copy
                  </button>
                  <button
                    className="mv-btn mv-btn-ghost mv-btn-sm"
                    onClick={() => revokeMutation.mutate(share.id)}
                    disabled={revokeMutation.isPending}
                  >
                    Revoke
                  </button>
                </>
              )}
            </div>
          ))}
        </div>
      ) : (
        <p className="mv-faint" style={{ fontSize: 12 }}>
          No share links yet.
        </p>
      )}
    </div>
  )
}
