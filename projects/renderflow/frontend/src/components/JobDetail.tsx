import type { Job } from "../api/client";
import { formatTime } from "../utils";
import { StatusBadge } from "./StatusBadge";

interface Props {
  job: Job;
  onClose: () => void;
  onRetry: (job: Job) => void;
  onCancel: (job: Job) => void;
}

function Row({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="detail-row">
      <span className="detail-label">{label}</span>
      <span className="detail-value">{value}</span>
    </div>
  );
}

export function JobDetail({ job, onClose, onRetry, onCancel }: Props) {
  const retryable = job.status === "failed" || job.status === "cancelled";
  const cancellable = ["pending", "queued", "running", "retrying"].includes(job.status);

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <header className="modal-header">
          <h2>
            Job <span className="mono">{job.id}</span>
          </h2>
          <button className="btn btn-sm" onClick={onClose}>
            ✕
          </button>
        </header>
        <div className="modal-body">
          <Row label="Status" value={<StatusBadge status={job.status} />} />
          <Row label="Type" value={job.job_type} />
          <Row label="Priority" value={job.priority} />
          <Row label="Input" value={<span className="mono">{job.input_uri}</span>} />
          <Row label="Output" value={job.output_uri ? <span className="mono">{job.output_uri}</span> : "—"} />
          <Row label="Retries" value={`${job.retries} / ${job.max_retries}`} />
          <Row label="Worker" value={job.worker_id ?? "—"} />
          <Row label="Idempotency key" value={job.idempotency_key ?? "—"} />
          <Row label="Created" value={formatTime(job.created_at)} />
          <Row label="Started" value={formatTime(job.started_at)} />
          <Row label="Completed" value={formatTime(job.completed_at)} />
          <Row label="Next run" value={formatTime(job.next_run_at)} />
          {job.error_message && (
            <div className="error-box">
              <strong>Error</strong>
              <pre>{job.error_message}</pre>
            </div>
          )}
          {job.params && Object.keys(job.params).length > 0 && (
            <div className="json-box">
              <strong>Params</strong>
              <pre>{JSON.stringify(job.params, null, 2)}</pre>
            </div>
          )}
          {job.result && (
            <div className="json-box">
              <strong>Result</strong>
              <pre>{JSON.stringify(job.result, null, 2)}</pre>
            </div>
          )}
        </div>
        <footer className="modal-footer">
          {retryable && (
            <button className="btn btn-primary" onClick={() => onRetry(job)}>
              Retry job
            </button>
          )}
          {cancellable && (
            <button className="btn btn-danger" onClick={() => onCancel(job)}>
              Cancel job
            </button>
          )}
        </footer>
      </div>
    </div>
  );
}
