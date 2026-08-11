import type { Tag } from '@/types'

interface TagPillProps {
  tag: Tag
  onRemove?: () => void
}

export function TagPill({ tag, onRemove }: TagPillProps) {
  return (
    <span className="mv-tag-pill">
      <span className="mv-tag-dot" style={{ background: tag.color }} />
      {tag.name}
      {onRemove && (
        <button
          onClick={(e) => {
            e.stopPropagation()
            onRemove()
          }}
          aria-label={`Remove ${tag.name}`}
          style={{
            background: 'none',
            border: 'none',
            cursor: 'pointer',
            color: 'var(--mv-text-faint)',
            padding: 0,
            fontSize: 12,
            lineHeight: 1,
          }}
        >
          ✕
        </button>
      )}
    </span>
  )
}
