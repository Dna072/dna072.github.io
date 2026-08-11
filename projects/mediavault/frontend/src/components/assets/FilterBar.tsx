import { useQuery } from '@tanstack/react-query'

import { listTags } from '@/api/tags'
import type { SearchSort } from '@/types'

interface FilterBarProps {
  workspaceId: string
  query: string
  onQueryChange: (value: string) => void
  contentType: string | null
  onContentTypeChange: (value: string | null) => void
  activeTags: string[]
  onToggleTag: (name: string) => void
  sort: SearchSort
  onSortChange: (value: SearchSort) => void
  view: 'grid' | 'table'
  onViewChange: (value: 'grid' | 'table') => void
}

const CONTENT_TYPES: { label: string; value: string | null }[] = [
  { label: 'All', value: null },
  { label: 'Video', value: 'video/' },
  { label: 'Image', value: 'image/' },
  { label: 'Audio', value: 'audio/' },
]

export function FilterBar({
  workspaceId,
  query,
  onQueryChange,
  contentType,
  onContentTypeChange,
  activeTags,
  onToggleTag,
  sort,
  onSortChange,
  view,
  onViewChange,
}: FilterBarProps) {
  const tagsQuery = useQuery({ queryKey: ['tags', workspaceId], queryFn: () => listTags(workspaceId) })

  return (
    <div className="mv-flex-col mv-gap-3" style={{ marginBottom: 18 }}>
      <div className="mv-flex mv-items-center mv-gap-3">
        <div style={{ position: 'relative', flex: 1, maxWidth: 420 }}>
          <input
            className="mv-input"
            placeholder="Search assets by name or description…"
            value={query}
            onChange={(e) => onQueryChange(e.target.value)}
            style={{ paddingLeft: 34 }}
          />
          <span
            style={{
              position: 'absolute',
              left: 11,
              top: '50%',
              transform: 'translateY(-50%)',
              color: 'var(--mv-text-faint)',
              fontSize: 14,
            }}
          >
            ⌕
          </span>
        </div>

        <select
          className="mv-select"
          style={{ width: 160 }}
          value={sort}
          onChange={(e) => onSortChange(e.target.value as SearchSort)}
        >
          <option value="relevance">Best match</option>
          <option value="newest">Newest first</option>
          <option value="oldest">Oldest first</option>
          <option value="name">Name (A–Z)</option>
        </select>

        <div className="mv-flex mv-gap-1" style={{ marginLeft: 'auto' }}>
          <button
            className={`mv-btn mv-btn-sm ${view === 'grid' ? 'mv-btn-secondary' : 'mv-btn-ghost'}`}
            onClick={() => onViewChange('grid')}
            aria-pressed={view === 'grid'}
          >
            Grid
          </button>
          <button
            className={`mv-btn mv-btn-sm ${view === 'table' ? 'mv-btn-secondary' : 'mv-btn-ghost'}`}
            onClick={() => onViewChange('table')}
            aria-pressed={view === 'table'}
          >
            Table
          </button>
        </div>
      </div>

      <div className="mv-flex mv-items-center mv-gap-2" style={{ flexWrap: 'wrap' }}>
        {CONTENT_TYPES.map((ct) => (
          <button
            key={ct.label}
            onClick={() => onContentTypeChange(ct.value)}
            className="mv-btn mv-btn-sm"
            style={{
              background: contentType === ct.value ? 'var(--mv-accent-700)' : 'var(--mv-surface-alt)',
              color: contentType === ct.value ? '#fff' : 'var(--mv-text-muted)',
              border: '1px solid transparent',
            }}
          >
            {ct.label}
          </button>
        ))}

        {tagsQuery.data && tagsQuery.data.length > 0 && (
          <span className="mv-faint" style={{ margin: '0 4px', fontSize: 12 }}>
            |
          </span>
        )}

        {tagsQuery.data?.map((tag) => {
          const active = activeTags.includes(tag.name)
          return (
            <button
              key={tag.id}
              onClick={() => onToggleTag(tag.name)}
              className="mv-tag-pill"
              style={{
                cursor: 'pointer',
                borderColor: active ? tag.color : 'var(--mv-border)',
                background: active ? 'var(--mv-accent-50)' : 'var(--mv-surface-alt)',
              }}
            >
              <span className="mv-tag-dot" style={{ background: tag.color }} />
              {tag.name}
            </button>
          )
        })}
      </div>
    </div>
  )
}
