function initials(name: string): string {
  const parts = name.trim().split(/\s+/)
  const first = parts[0]?.[0] ?? ''
  const last = parts.length > 1 ? parts[parts.length - 1]?.[0] ?? '' : ''
  return (first + last).toUpperCase() || '?'
}

const PALETTE = ['#1c6249', '#2f6b8f', '#c17a3f', '#7a5fa8', '#b8422f', '#3f8f6f']

function colorFor(name: string): string {
  let hash = 0
  for (const char of name) hash = (hash * 31 + char.charCodeAt(0)) % PALETTE.length
  return PALETTE[Math.abs(hash) % PALETTE.length]
}

export function Avatar({ name, size = 28 }: { name: string; size?: number }) {
  return (
    <div
      style={{
        width: size,
        height: size,
        borderRadius: '50%',
        background: colorFor(name),
        color: '#fff',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        fontSize: size * 0.4,
        fontWeight: 700,
        flexShrink: 0,
      }}
      aria-hidden
    >
      {initials(name)}
    </div>
  )
}
