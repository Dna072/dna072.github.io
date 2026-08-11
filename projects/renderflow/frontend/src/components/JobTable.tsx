import type { Job } from "../api/client";
import { shortId, timeAgo } from "../utils";
import { StatusBadge } from "./StatusBadge";

interface Props {
  jobs: Job[];
  onSelect: (job: Job) => void;
  onRetry?: (job: Job) => void;
  onCancel?: (job: Job) => void;
}

const RETRYABLE = new Set(["failed", "cancelled"]);
const CANCELLABLE = new Set(["pending", "queued", "running", "retrying"]);

export function JobTable({ jobs, onSelect, onRetry, onCancel }: Props) {
  if (jobs.length === 0) {
    return <p className="empty">No jobs match the current filter.</p>;
  }
  return (
    <div className="table-wrap">
      <table className="jobs-table">
        <thead>
          <tr>
            <th>ID</th>
            <th>Type</th>
            <th>Status</th>
            <th>Prio</th>
            <th>Retries</th>
            <th>Created</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {jobs.map((job) => (
            <tr key={job.id} onClick={() => onSelect(job)}>
              <td className="mono">{shortId(job.id)}</td>
              <td>{job.job_type}</td>
              <td>
                <StatusBadge status={job.status} />
              </td>
              <td>{job.priority}</td>
              <td>
                {job.retries}/{job.max_retries}
              </td>
              <td>{timeAgo(job.created_at)}</td>
              <td className="actions" onClick={(e) => e.stopPropagation()}>
                {onRetry && RETRYABLE.has(job.status) && (
                  <button className="btn btn-sm" onClick={() => onRetry(job)}>
                    Retry
                  </button>
                )}
                {onCancel && CANCELLABLE.has(job.status) && (
                  <button className="btn btn-sm btn-danger" onClick={() => onCancel(job)}>
                    Cancel
                  </button>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
