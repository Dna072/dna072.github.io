import { useCallback, useMemo, useState } from "react";
import { api, type Job } from "./api/client";
import { usePolling } from "./hooks/usePolling";
import { StatCards } from "./components/StatCards";
import { SubmitForm } from "./components/SubmitForm";
import { JobTable } from "./components/JobTable";
import { JobDetail } from "./components/JobDetail";
import { WorkerPanel } from "./components/WorkerPanel";

type Tab = "dashboard" | "jobs" | "failed";

const STATUS_FILTERS = [
  "",
  "queued",
  "running",
  "retrying",
  "succeeded",
  "failed",
  "cancelled",
];
const TYPE_FILTERS = ["", "transcode", "thumbnail", "audio_extract", "metadata"];

export function App() {
  const [tab, setTab] = useState<Tab>("dashboard");
  const [statusFilter, setStatusFilter] = useState("");
  const [typeFilter, setTypeFilter] = useState("");
  const [selected, setSelected] = useState<Job | null>(null);
  const [banner, setBanner] = useState<string | null>(null);

  const stats = usePolling(() => api.stats(), 3000);
  const workers = usePolling(() => api.workers(), 3000);

  const jobsLoader = useCallback(
    () => api.listJobs({ status: statusFilter, job_type: typeFilter, limit: 100 }),
    [statusFilter, typeFilter],
  );
  const jobs = usePolling(jobsLoader, 3000, tab === "jobs");
  const failed = usePolling(() => api.failedJobs(100), 3000, tab === "failed");

  const refreshAll = useCallback(() => {
    stats.refresh();
    workers.refresh();
    jobs.refresh();
    failed.refresh();
  }, [stats, workers, jobs, failed]);

  const onRetry = useCallback(
    async (job: Job) => {
      try {
        await api.retryJob(job.id, true);
        setBanner(`Re-queued job ${job.id.slice(0, 8)}`);
        setSelected(null);
        refreshAll();
      } catch (e) {
        setBanner(e instanceof Error ? e.message : "Retry failed");
      }
    },
    [refreshAll],
  );

  const onCancel = useCallback(
    async (job: Job) => {
      try {
        await api.cancelJob(job.id);
        setBanner(`Cancelled job ${job.id.slice(0, 8)}`);
        setSelected(null);
        refreshAll();
      } catch (e) {
        setBanner(e instanceof Error ? e.message : "Cancel failed");
      }
    },
    [refreshAll],
  );

  const health = useMemo(() => {
    const online = workers.data?.online ?? 0;
    return online > 0 ? "operational" : "no workers";
  }, [workers.data]);

  return (
    <div className="app">
      <header className="topbar">
        <div className="brand">
          <span className="logo">▶</span>
          <div>
            <h1>RenderFlow</h1>
            <p>Distributed media processing — operations console</p>
          </div>
        </div>
        <div className="topbar-right">
          <span className={`status-pill ${health === "operational" ? "ok" : "warn"}`}>
            <span className="dot dot-ok" /> {health}
          </span>
        </div>
      </header>

      <nav className="tabs">
        {(["dashboard", "jobs", "failed"] as Tab[]).map((t) => (
          <button
            key={t}
            className={tab === t ? "tab active" : "tab"}
            onClick={() => setTab(t)}
          >
            {t === "failed" ? "Failed / Retry" : t}
          </button>
        ))}
      </nav>

      {banner && (
        <div className="banner" onClick={() => setBanner(null)}>
          {banner} <span className="banner-close">✕</span>
        </div>
      )}

      <main className="content">
        {tab === "dashboard" && (
          <>
            <StatCards stats={stats.data} />
            <div className="two-col">
              <SubmitForm onSubmitted={refreshAll} />
              <WorkerPanel data={workers.data} />
            </div>
          </>
        )}

        {tab === "jobs" && (
          <div className="card">
            <div className="card-head">
              <h2>Jobs</h2>
              <div className="filters">
                <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
                  {STATUS_FILTERS.map((s) => (
                    <option key={s} value={s}>
                      {s || "all statuses"}
                    </option>
                  ))}
                </select>
                <select value={typeFilter} onChange={(e) => setTypeFilter(e.target.value)}>
                  {TYPE_FILTERS.map((s) => (
                    <option key={s} value={s}>
                      {s || "all types"}
                    </option>
                  ))}
                </select>
                <button className="btn btn-sm" onClick={() => jobs.refresh()}>
                  Refresh
                </button>
              </div>
            </div>
            {jobs.error && <p className="msg-err">{jobs.error}</p>}
            <JobTable
              jobs={jobs.data?.items ?? []}
              onSelect={setSelected}
              onRetry={onRetry}
              onCancel={onCancel}
            />
          </div>
        )}

        {tab === "failed" && (
          <div className="card">
            <div className="card-head">
              <h2>Failed jobs</h2>
              <button className="btn btn-sm" onClick={() => failed.refresh()}>
                Refresh
              </button>
            </div>
            <p className="hint">
              Jobs here exhausted their automatic retries. Inspect the error and
              re-queue with a fresh retry budget.
            </p>
            {failed.error && <p className="msg-err">{failed.error}</p>}
            <JobTable
              jobs={failed.data?.items ?? []}
              onSelect={setSelected}
              onRetry={onRetry}
            />
          </div>
        )}
      </main>

      <footer className="footer">
        RenderFlow · production-style portfolio project · API docs at{" "}
        <a href="/docs">/docs</a>
      </footer>

      {selected && (
        <JobDetail
          job={selected}
          onClose={() => setSelected(null)}
          onRetry={onRetry}
          onCancel={onCancel}
        />
      )}
    </div>
  );
}
