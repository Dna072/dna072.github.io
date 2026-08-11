import type { VideoStatus } from '@/types';

const LABELS: Record<VideoStatus, string> = {
  uploaded: 'Uploaded',
  queued: 'Queued',
  processing: 'Processing',
  completed: 'Completed',
  failed: 'Failed',
};

export function StatusBadge({ status }: { status: VideoStatus }) {
  return (
    <span className={`badge ${status}`}>
      <span className="dot" />
      {LABELS[status] ?? status}
    </span>
  );
}
