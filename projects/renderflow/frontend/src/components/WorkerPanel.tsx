import type { WorkerList } from "../api/client";
import { timeAgo } from "../utils";

export function WorkerPanel({ data }: { data: WorkerList | null }) {
  const workers = data?.items ?? [];
  return (
    <div className="card">
      <div className="card-head">
        <h2>Workers</h2>
        <span className="pill">
          {data?.online ?? 0} online / {data?.total ?? 0}
        </span>
      </div>
      {workers.length === 0 ? (
        <p className="empty">No workers have reported in yet.</p>
      ) : (
        <table className="jobs-table">
          <thead>
            <tr>
              <th>Worker</th>
              <th>State</th>
              <th>Current job</th>
              <th>Done</th>
              <th>Failed</th>
              <th>Heartbeat</th>
            </tr>
          </thead>
          <tbody>
            {workers.map((w) => (
              <tr key={w.worker_id}>
                <td className="mono">
                  <span className={`dot ${w.healthy ? "dot-ok" : "dot-bad"}`} />
                  {w.worker_id}
                </td>
                <td>{w.status}</td>
                <td className="mono">{w.current_job_id ? w.current_job_id.slice(0, 8) : "—"}</td>
                <td>{w.jobs_processed}</td>
                <td>{w.jobs_failed}</td>
                <td>{timeAgo(w.last_heartbeat_at)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
