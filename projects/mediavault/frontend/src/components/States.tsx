import type { ReactNode } from "react";
import { Icon } from "../lib/icons";

export function Spinner() {
  return <span className="spinner" aria-label="Loading" role="status" />;
}

export function LoadingState({ label = "Loading…" }: { label?: string }) {
  return (
    <div className="state">
      <Spinner />
      <div className="muted">{label}</div>
    </div>
  );
}

export function EmptyState({
  title,
  hint,
  action,
  glyph,
}: {
  title: string;
  hint?: string;
  action?: ReactNode;
  glyph?: ReactNode;
}) {
  return (
    <div className="state">
      <div className="glyph">{glyph ?? <Icon.Library size={26} />}</div>
      <div style={{ fontWeight: 600, color: "var(--text)" }}>{title}</div>
      {hint && <div className="muted" style={{ maxWidth: 340 }}>{hint}</div>}
      {action}
    </div>
  );
}

export function ErrorState({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div className="state">
      <div className="glyph" style={{ color: "var(--red-500)" }}>
        <Icon.Close size={26} />
      </div>
      <div style={{ fontWeight: 600, color: "var(--text)" }}>Something went wrong</div>
      <div className="muted">{message}</div>
      {onRetry && (
        <button className="btn" onClick={onRetry}>
          Try again
        </button>
      )}
    </div>
  );
}

export function AssetGridSkeleton({ count = 8 }: { count?: number }) {
  return (
    <div className="asset-grid">
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} className="card asset-card" aria-hidden>
          <div className="skeleton" style={{ aspectRatio: "16 / 10", borderRadius: 0 }} />
          <div className="asset-body">
            <div className="skeleton" style={{ height: 13, width: "70%" }} />
            <div className="skeleton" style={{ height: 10, width: "40%", marginTop: 8 }} />
          </div>
        </div>
      ))}
    </div>
  );
}
