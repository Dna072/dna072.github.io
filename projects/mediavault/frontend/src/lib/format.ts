export function formatBytes(bytes: number): string {
  if (bytes === 0) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB', 'TB']
  const exponent = Math.min(Math.floor(Math.log(bytes) / Math.log(1024)), units.length - 1)
  const value = bytes / 1024 ** exponent
  return `${exponent === 0 ? value : value.toFixed(1)} ${units[exponent]}`
}

export function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString(undefined, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  })
}

export function formatDateTime(iso: string): string {
  return new Date(iso).toLocaleString(undefined, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
  })
}

export function formatRelativeTime(iso: string): string {
  const date = new Date(iso).getTime()
  const diffSeconds = Math.round((date - Date.now()) / 1000)
  const divisions: [number, Intl.RelativeTimeFormatUnit][] = [
    [60, 'seconds'],
    [60, 'minutes'],
    [24, 'hours'],
    [7, 'days'],
    [4.345, 'weeks'],
    [12, 'months'],
    [Number.POSITIVE_INFINITY, 'years'],
  ]
  let duration = diffSeconds
  const rtf = new Intl.RelativeTimeFormat(undefined, { numeric: 'auto' })
  for (const [amount, unit] of divisions) {
    if (Math.abs(duration) < amount) {
      return rtf.format(Math.round(duration), unit)
    }
    duration /= amount
  }
  return rtf.format(Math.round(duration), 'years')
}

export function mediaKind(contentType: string): 'video' | 'image' | 'audio' | 'other' {
  if (contentType.startsWith('video/')) return 'video'
  if (contentType.startsWith('image/')) return 'image'
  if (contentType.startsWith('audio/')) return 'audio'
  return 'other'
}
