import { Area, CartesianGrid, ComposedChart, Line, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { TimeSeriesPoint } from "../types";
import { formatCompactNumber, formatDateLabel } from "../utils/format";
import "./TimeSeriesChart.css";

interface TimeSeriesChartProps {
  points: TimeSeriesPoint[];
  comparePoints: TimeSeriesPoint[] | null;
}

interface ChartRow {
  date: string;
  views: number;
  watchTimeHours: number;
  previousViews?: number;
}

function buildRows(points: TimeSeriesPoint[], comparePoints: TimeSeriesPoint[] | null): ChartRow[] {
  return points.map((point, index) => ({
    date: point.date,
    views: point.views,
    watchTimeHours: point.watch_time_hours,
    previousViews: comparePoints?.[index]?.views,
  }));
}

function ChartTooltip({ active, payload, label }: any) {
  if (!active || !payload?.length) return null;
  return (
    <div className="ts-tooltip">
      <p className="ts-tooltip__date">{formatDateLabel(label)}</p>
      {payload.map((entry: any) => (
        <p key={entry.dataKey} className="ts-tooltip__row">
          <span className="ts-tooltip__dot" style={{ background: entry.color }} />
          {entry.name}: <strong>{typeof entry.value === "number" ? formatCompactNumber(entry.value) : entry.value}</strong>
        </p>
      ))}
    </div>
  );
}

export default function TimeSeriesChart({ points, comparePoints }: TimeSeriesChartProps) {
  const rows = buildRows(points, comparePoints);

  return (
    <ResponsiveContainer width="100%" height={300}>
      <ComposedChart data={rows} margin={{ top: 6, right: 12, left: -14, bottom: 0 }}>
        <defs>
          <linearGradient id="viewsGradient" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#22d3ee" stopOpacity={0.35} />
            <stop offset="100%" stopColor="#22d3ee" stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid stroke="rgba(255,255,255,0.06)" vertical={false} />
        <XAxis
          dataKey="date"
          tickFormatter={formatDateLabel}
          tick={{ fill: "#8b98ab", fontSize: 11 }}
          axisLine={{ stroke: "rgba(255,255,255,0.08)" }}
          tickLine={false}
          minTickGap={24}
        />
        <YAxis
          yAxisId="views"
          tickFormatter={formatCompactNumber}
          tick={{ fill: "#8b98ab", fontSize: 11 }}
          axisLine={false}
          tickLine={false}
          width={48}
        />
        <YAxis
          yAxisId="watch"
          orientation="right"
          tickFormatter={(v) => `${formatCompactNumber(v)}h`}
          tick={{ fill: "#5f6b80", fontSize: 11 }}
          axisLine={false}
          tickLine={false}
          width={48}
        />
        <Tooltip content={<ChartTooltip />} />
        <Area
          yAxisId="views"
          type="monotone"
          dataKey="views"
          name="Views"
          stroke="#22d3ee"
          fill="url(#viewsGradient)"
          strokeWidth={2}
          dot={false}
        />
        {comparePoints && (
          <Line
            yAxisId="views"
            type="monotone"
            dataKey="previousViews"
            name="Previous period"
            stroke="#8b98ab"
            strokeDasharray="4 4"
            strokeWidth={1.75}
            dot={false}
          />
        )}
        <Line
          yAxisId="watch"
          type="monotone"
          dataKey="watchTimeHours"
          name="Watch time (h)"
          stroke="#a78bfa"
          strokeWidth={1.75}
          dot={false}
        />
      </ComposedChart>
    </ResponsiveContainer>
  );
}
