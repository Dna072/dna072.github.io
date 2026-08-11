import type { AssetStatus } from '@/types'

const LABELS: Record<AssetStatus, string> = {
  UPLOADING: 'Uploading',
  PROCESSING: 'Processing',
  READY: 'Ready',
  FAILED: 'Failed',
}

export function StatusBadge({ status }: { status: AssetStatus }) {
  return (
    <span className={`mv-badge mv-badge-status-${status.toLowerCase()}`}>{LABELS[status]}</span>
  )
}
