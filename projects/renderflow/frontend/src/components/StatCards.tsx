import type { JobStats } from "../api/client";

const ORDER = [
  "queued",
  "running",
  "retrying",
  "succeeded",
  "failed",
  "cancelled",
];

export function StatCards({ stats }: { stats: JobStats | null }) {
  const counts = stats?.counts ?? {};
  return (
    <div className="stat-grid">
      <div className="stat-card stat-total">
        <div className="stat-value">{stats?.total ?? 0}</div>
        <div className="stat-label">Total jobs</div>
      </div>
      {ORDER.map((key) => (
        <div key={key} className={`stat-card stat-${key}`}>
          <div className="stat-value">{counts[key] ?? 0}</div>
          <div className="stat-label">{key}</div>
        </div>
      ))}
    </div>
  );
}
