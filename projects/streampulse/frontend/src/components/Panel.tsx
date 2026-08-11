import type { ReactNode } from "react";
import { EmptyState, ErrorState, LoadingState } from "./StateViews";
import "./Panel.css";

interface PanelProps {
  title: string;
  subtitle?: string;
  actions?: ReactNode;
  loading?: boolean;
  error?: string | null;
  isEmpty?: boolean;
  emptyMessage?: string;
  onRetry?: () => void;
  className?: string;
  children: ReactNode;
}

export default function Panel({
  title,
  subtitle,
  actions,
  loading,
  error,
  isEmpty,
  emptyMessage,
  onRetry,
  className,
  children,
}: PanelProps) {
  return (
    <section className={`panel ${className ?? ""}`}>
      <header className="panel__header">
        <div>
          <h2 className="panel__title">{title}</h2>
          {subtitle && <p className="panel__subtitle">{subtitle}</p>}
        </div>
        {actions && <div className="panel__actions">{actions}</div>}
      </header>
      <div className="panel__body">
        {loading ? (
          <LoadingState />
        ) : error ? (
          <ErrorState message={error} onRetry={onRetry} />
        ) : isEmpty ? (
          <EmptyState message={emptyMessage} />
        ) : (
          children
        )}
      </div>
    </section>
  );
}
