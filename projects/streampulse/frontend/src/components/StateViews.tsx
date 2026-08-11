import "./StateViews.css";

export function LoadingState({ label = "Loading data…" }: { label?: string }) {
  return (
    <div className="state-view state-view--loading">
      <span className="spinner" aria-hidden="true" />
      <span>{label}</span>
    </div>
  );
}

export function ErrorState({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div className="state-view state-view--error">
      <span className="state-view__icon">⚠</span>
      <span>{message}</span>
      {onRetry && (
        <button type="button" className="state-view__retry" onClick={onRetry}>
          Retry
        </button>
      )}
    </div>
  );
}

export function EmptyState({ message = "No data for this range yet." }: { message?: string }) {
  return (
    <div className="state-view state-view--empty">
      <span className="state-view__icon">◌</span>
      <span>{message}</span>
    </div>
  );
}
