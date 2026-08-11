import { mediaKind } from '@/lib/format'

export function MediaIcon({ contentType, size = 22 }: { contentType: string; size?: number }) {
  const kind = mediaKind(contentType)
  const common = { width: size, height: size, viewBox: '0 0 24 24', fill: 'none' }

  if (kind === 'video') {
    return (
      <svg {...common}>
        <rect x="2.5" y="4.5" width="15" height="15" rx="3" stroke="currentColor" strokeWidth="1.6" />
        <path d="M17.5 9.5 21 7v10l-3.5-2.5" stroke="currentColor" strokeWidth="1.6" strokeLinejoin="round" />
        <path d="M8 9.5v5l4-2.5-4-2.5Z" fill="currentColor" />
      </svg>
    )
  }
  if (kind === 'image') {
    return (
      <svg {...common}>
        <rect x="3" y="4" width="18" height="16" rx="3" stroke="currentColor" strokeWidth="1.6" />
        <circle cx="8.5" cy="9.5" r="1.6" fill="currentColor" />
        <path d="M3.5 17 9 12l3.5 3 3-3.5 5 5.2" stroke="currentColor" strokeWidth="1.6" strokeLinejoin="round" strokeLinecap="round" />
      </svg>
    )
  }
  if (kind === 'audio') {
    return (
      <svg {...common}>
        <path d="M9 17V6.5l10-2v10.5" stroke="currentColor" strokeWidth="1.6" strokeLinejoin="round" />
        <circle cx="6.5" cy="17" r="2.5" stroke="currentColor" strokeWidth="1.6" />
        <circle cx="16.5" cy="15" r="2.5" stroke="currentColor" strokeWidth="1.6" />
      </svg>
    )
  }
  return (
    <svg {...common}>
      <path d="M6 3h9l3 3v15H6z" stroke="currentColor" strokeWidth="1.6" strokeLinejoin="round" />
      <path d="M15 3v3h3" stroke="currentColor" strokeWidth="1.6" strokeLinejoin="round" />
    </svg>
  )
}
