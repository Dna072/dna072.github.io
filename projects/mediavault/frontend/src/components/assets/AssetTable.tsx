import { MediaIcon } from '@/components/common/MediaIcon'
import { StatusBadge } from '@/components/common/StatusBadge'
import { TagPill } from '@/components/common/TagPill'
import { formatBytes, formatDate } from '@/lib/format'
import type { Asset } from '@/types'

export function AssetTable({ assets, onOpen }: { assets: Asset[]; onOpen: (asset: Asset) => void }) {
  return (
    <div className="mv-card" style={{ overflow: 'hidden' }}>
      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
        <thead>
          <tr style={{ background: 'var(--mv-surface-alt)', textAlign: 'left' }}>
            {['Name', 'Tags', 'Size', 'Status', 'Uploaded'].map((header) => (
              <th
                key={header}
                style={{
                  padding: '10px 16px',
                  fontSize: 11,
                  fontWeight: 700,
                  textTransform: 'uppercase',
                  letterSpacing: '0.03em',
                  color: 'var(--mv-text-faint)',
                  borderBottom: '1px solid var(--mv-border)',
                }}
              >
                {header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {assets.map((asset) => (
            <tr
              key={asset.id}
              onClick={() => onOpen(asset)}
              style={{ cursor: 'pointer', borderBottom: '1px solid var(--mv-border)' }}
              className="mv-table-row"
            >
              <td style={{ padding: '10px 16px', maxWidth: 320 }}>
                <div className="mv-flex mv-items-center mv-gap-2">
                  <span style={{ color: 'var(--mv-accent-700)', flexShrink: 0 }}>
                    <MediaIcon contentType={asset.content_type} size={18} />
                  </span>
                  <span className="mv-truncate" title={asset.filename}>
                    {asset.filename}
                  </span>
                </div>
              </td>
              <td style={{ padding: '10px 16px' }}>
                <div className="mv-flex mv-gap-1" style={{ flexWrap: 'wrap' }}>
                  {asset.tags.slice(0, 3).map((tag) => (
                    <TagPill key={tag.id} tag={tag} />
                  ))}
                </div>
              </td>
              <td className="mv-muted" style={{ padding: '10px 16px', whiteSpace: 'nowrap' }}>
                {formatBytes(asset.size_bytes)}
              </td>
              <td style={{ padding: '10px 16px' }}>
                <StatusBadge status={asset.status} />
              </td>
              <td className="mv-muted" style={{ padding: '10px 16px', whiteSpace: 'nowrap' }}>
                {formatDate(asset.created_at)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
