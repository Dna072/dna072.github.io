import type { ReactNode } from 'react';

export function Panel({
  title,
  subtitle,
  right,
  children,
  className = 'col-12',
}: {
  title?: string;
  subtitle?: string;
  right?: ReactNode;
  children: ReactNode;
  className?: string;
}) {
  return (
    <section className={`panel ${className}`}>
      {(title || right) && (
        <div className="panel-head">
          <div>
            {title && <h3>{title}</h3>}
            {subtitle && <div className="subtitle">{subtitle}</div>}
          </div>
          {right}
        </div>
      )}
      {children}
    </section>
  );
}

export function LoadingState({ height = 220 }: { height?: number }) {
  return <div className="skeleton" style={{ width: '100%', height }} aria-busy="true" />;
}

export function ErrorState({ onRetry }: { onRetry?: () => void }) {
  return (
    <div className="state" role="alert">
      <div className="icon">⚠️</div>
      <div>Couldn&apos;t load this data.</div>
      {onRetry && (
        <button className="btn ghost" onClick={onRetry}>
          Retry
        </button>
      )}
    </div>
  );
}

export function EmptyState({ message = 'No data in this range.' }: { message?: string }) {
  return (
    <div className="state">
      <div className="icon">📭</div>
      <div>{message}</div>
    </div>
  );
}

/**
 * Renders the right UI for a React Query result: loading skeleton, error with
 * retry, empty state, or the children when data is present.
 */
export function QueryBoundary<T>({
  query,
  isEmpty,
  loadingHeight,
  emptyMessage,
  children,
}: {
  query: {
    isLoading: boolean;
    isError: boolean;
    data: T | undefined;
    refetch: () => void;
  };
  isEmpty?: (data: T) => boolean;
  loadingHeight?: number;
  emptyMessage?: string;
  children: (data: T) => ReactNode;
}) {
  if (query.isLoading) return <LoadingState height={loadingHeight} />;
  if (query.isError || query.data === undefined) return <ErrorState onRetry={query.refetch} />;
  if (isEmpty?.(query.data)) return <EmptyState message={emptyMessage} />;
  return <>{children(query.data)}</>;
}
