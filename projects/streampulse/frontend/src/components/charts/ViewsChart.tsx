import {
  Area,
  AreaChart,
  CartesianGrid,
  Legend,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';

import { formatCompact, formatDateLabel } from '../../lib/format';
import type { TimeSeriesResponse } from '../../lib/types';

type Metric = 'views' | 'watch_hours' | 'unique_viewers';

const METRIC_LABEL: Record<Metric, string> = {
  views: 'Views',
  watch_hours: 'Watch hours',
  unique_viewers: 'Unique viewers',
};

export default function ViewsChart({
  data,
  metric,
}: {
  data: TimeSeriesResponse;
  metric: Metric;
}) {
  // Align current & previous periods by index so the comparison line overlays
  // regardless of the actual calendar dates.
  const rows = data.points.map((p, i) => ({
    bucket: p.bucket,
    current: p[metric],
    previous: data.previous_points ? data.previous_points[i]?.[metric] ?? null : null,
  }));

  const showPrev = Boolean(data.previous_points);

  return (
    <ResponsiveContainer width="100%" height={300}>
      <AreaChart data={rows} margin={{ top: 8, right: 12, left: 0, bottom: 0 }}>
        <defs>
          <linearGradient id="curFill" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#22d3ee" stopOpacity={0.45} />
            <stop offset="100%" stopColor="#22d3ee" stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid stroke="#223052" strokeDasharray="3 3" vertical={false} />
        <XAxis
          dataKey="bucket"
          tickFormatter={formatDateLabel}
          stroke="#63769b"
          fontSize={12}
          tickMargin={8}
          minTickGap={24}
        />
        <YAxis
          stroke="#63769b"
          fontSize={12}
          tickFormatter={(v) => formatCompact(v as number)}
          width={48}
        />
        <Tooltip
          contentStyle={{ background: '#111a2e', border: '1px solid #2c3d66' }}
          labelStyle={{ color: '#93a4c4' }}
          formatter={(value: number, name: string) => [
            formatCompact(value),
            name === 'current' ? METRIC_LABEL[metric] : 'Previous period',
          ]}
          labelFormatter={(l) => formatDateLabel(l as string)}
        />
        {showPrev && <Legend wrapperStyle={{ fontSize: 12, color: '#93a4c4' }} />}
        <Area
          type="monotone"
          dataKey="current"
          name={METRIC_LABEL[metric]}
          stroke="#22d3ee"
          strokeWidth={2.5}
          fill="url(#curFill)"
        />
        {showPrev && (
          <Line
            type="monotone"
            dataKey="previous"
            name="Previous period"
            stroke="#fb7185"
            strokeWidth={2}
            strokeDasharray="5 4"
            dot={false}
          />
        )}
      </AreaChart>
    </ResponsiveContainer>
  );
}
