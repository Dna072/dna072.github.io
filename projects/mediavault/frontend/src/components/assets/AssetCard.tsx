import { MediaIcon } from '@/components/common/MediaIcon'
import { StatusBadge } from '@/components/common/StatusBadge'
import { TagPill } from '@/components/common/TagPill'
import { formatBytes, formatRelativeTime, mediaKind } from '@/lib/format'
import type { Asset } from '@/types'

interface AssetCardProps {
  asset: Asset
  onOpen: () => void
}

export function AssetCard({ asset, onOpen }: AssetCardProps) {
  const kind = mediaKind(asset.content_type)

  return (
    <button
      onClick={onOpen}
      className="mv-card mv-asset-card"
      style={{
        display: 'flex',
        flexDirection: 'column',
        textAlign: 'left',
        cursor: 'pointer',
        overflow: 'hidden',
        padding: 0,
      }}
    >
      <div
        style={{
          aspectRatio: '16 / 10',
          background: 'var(--mv-surface-sunken)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: 'var(--mv-accent-700)',
          position: 'relative',
        }}
      >
        <MediaIcon contentType={asset.content_type} size={32} />
        <span
          style={{
            position: 'absolute',
            top: 8,
            right: 8,
            fontSize: 10,
            fontWeight: 700,
            textTransform: 'uppercase',
            background: 'rgba(16,31,26,0.55)',
            color: '#fff',
            padding: '2px 6px',
            borderRadius: 4,
          }}
        >
          {kind}
        </span>
      </div>
      <div style={{ padding: 12 }}>
        <div className="mv-truncate" style={{ fontWeight: 600, fontSize: 13 }} title={asset.filename}>
          {asset.filename}
        </div>
        <div className="mv-muted mv-flex mv-items-center mv-gap-2" style={{ fontSize: 11, marginTop: 4 }}>
          <span>{formatBytes(asset.size_bytes)}</span>
          <span>·</span>
          <span>{formatRelativeTime(asset.created_at)}</span>
        </div>
        <div className="mv-flex mv-items-center mv-gap-1" style={{ marginTop: 8, flexWrap: 'wrap' }}>
          <StatusBadge status={asset.status} />
          {asset.tags.slice(0, 2).map((tag) => (
            <TagPill key={tag.id} tag={tag} />
          ))}
          {asset.tags.length > 2 && (
            <span className="mv-faint" style={{ fontSize: 11 }}>
              +{asset.tags.length - 2}
            </span>
          )}
        </div>
      </div>
    </button>
  )
}
