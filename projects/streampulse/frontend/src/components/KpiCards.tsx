import { formatDeltaPct, formatDuration, formatNumber, formatPercent } from '../lib/format';
import type { MetricDelta, OverviewMetrics } from '../lib/types';

function DeltaBadge({ metric, invert = false }: { metric: MetricDelta; invert?: boolean }) {
  if (metric.previous === null || metric.delta_pct === null) {
    return <span className="delta flat">no comparison</span>;
  }
  const raw = metric.delta_pct;
  const positiveIsGood = !invert;
  const isPos = raw > 0;
  const good = positiveIsGood ? isPos : !isPos;
  const cls = raw === 0 ? 'flat' : good ? 'pos' : 'neg';
  const arrow = raw === 0 ? '→' : raw > 0 ? '▲' : '▼';
  return (
    <span className={`delta ${cls}`}>
      {arrow} {formatDeltaPct(raw)}
    </span>
  );
}

function Card({
  label,
  value,
  metric,
  previousText,
  invert,
}: {
  label: string;
  value: string;
  metric: MetricDelta;
  previousText?: string;
  invert?: boolean;
}) {
  return (
    <div className="kpi">
      <div className="label">{label}</div>
      <div className="value">{value}</div>
      <DeltaBadge metric={metric} invert={invert} />
      {metric.previous !== null && previousText && (
        <div className="prev">prev: {previousText}</div>
      )}
    </div>
  );
}

export default function KpiCards({ data }: { data: OverviewMetrics }) {
  return (
    <div className="kpi-grid">
      <Card
        label="Total views"
        value={formatNumber(data.total_views.value)}
        metric={data.total_views}
        previousText={
          data.total_views.previous !== null
            ? formatNumber(data.total_views.previous)
            : undefined
        }
      />
      <Card
        label="Unique viewers"
        value={formatNumber(data.unique_viewers.value)}
        metric={data.unique_viewers}
        previousText={
          data.unique_viewers.previous !== null
            ? formatNumber(data.unique_viewers.previous)
            : undefined
        }
      />
      <Card
        label="Watch time"
        value={`${formatNumber(data.total_watch_hours.value)} h`}
        metric={data.total_watch_hours}
        previousText={
          data.total_watch_hours.previous !== null
            ? `${formatNumber(data.total_watch_hours.previous)} h`
            : undefined
        }
      />
      <Card
        label="Avg view duration"
        value={formatDuration(data.avg_view_duration_seconds.value)}
        metric={data.avg_view_duration_seconds}
        previousText={
          data.avg_view_duration_seconds.previous !== null
            ? formatDuration(data.avg_view_duration_seconds.previous)
            : undefined
        }
      />
      <Card
        label="Engagement rate"
        value={formatPercent(data.engagement_rate.value)}
        metric={data.engagement_rate}
        previousText={
          data.engagement_rate.previous !== null
            ? formatPercent(data.engagement_rate.previous)
            : undefined
        }
      />
      <Card
        label="Completion rate"
        value={formatPercent(data.completion_rate.value)}
        metric={data.completion_rate}
        previousText={
          data.completion_rate.previous !== null
            ? formatPercent(data.completion_rate.previous)
            : undefined
        }
      />
    </div>
  );
}
