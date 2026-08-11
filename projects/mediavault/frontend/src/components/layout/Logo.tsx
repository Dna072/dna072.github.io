export function Logo({ size = 26 }: { size?: number }) {
  return (
    <div className="mv-flex mv-items-center mv-gap-2">
      <svg width={size} height={size} viewBox="0 0 32 32">
        <rect width="32" height="32" rx="7" fill="var(--mv-accent-900)" />
        <path d="M11 9.5 L23 16 L11 22.5 Z" fill="var(--mv-accent-400)" />
      </svg>
      <span style={{ fontWeight: 800, fontSize: 16, letterSpacing: '-0.01em' }}>MediaVault</span>
    </div>
  )
}
