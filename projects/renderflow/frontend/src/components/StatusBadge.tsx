import type { JobStatus } from "../api/client";

export function StatusBadge({ status }: { status: JobStatus | string }) {
  return <span className={`badge badge-${status}`}>{status}</span>;
}
