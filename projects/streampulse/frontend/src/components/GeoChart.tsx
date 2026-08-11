import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { GeoBreakdown } from "../types";
import { formatCompactNumber } from "../utils/format";
import "./GeoChart.css";

function GeoTooltip({ active, payload }: any) {
  if (!active || !payload?.length) return null;
  const item: GeoBreakdown = payload[0].payload;
  return (
    <div className="ts-tooltip">
      <p className="ts-tooltip__row">
        <strong>{item.country_name}</strong>
      </p>
      <p className="ts-tooltip__row">{item.views.toLocaleString()} views · {item.share_percent.toFixed(1)}%</p>
      <p className="ts-tooltip__row">{item.watch_time_hours.toLocaleString()}h watch time</p>
    </div>
  );
}

export default function GeoChart({ items }: { items: GeoBreakdown[] }) {
  const top = items.slice(0, 8);

  return (
    <ResponsiveContainer width="100%" height={Math.max(220, top.length * 34)}>
      <BarChart data={top} layout="vertical" margin={{ top: 4, right: 20, left: 8, bottom: 0 }}>
        <CartesianGrid stroke="rgba(255,255,255,0.06)" horizontal={false} />
        <XAxis type="number" tickFormatter={formatCompactNumber} tick={{ fill: "#8b98ab", fontSize: 11 }} axisLine={false} tickLine={false} />
        <YAxis
          type="category"
          dataKey="country_name"
          tick={{ fill: "#e7edf6", fontSize: 12 }}
          axisLine={false}
          tickLine={false}
          width={110}
        />
        <Tooltip content={<GeoTooltip />} cursor={{ fill: "rgba(34,211,238,0.06)" }} />
        <Bar dataKey="views" radius={[0, 6, 6, 0]} maxBarSize={18}>
          {top.map((_, index) => (
            <Cell key={index} fill={index === 0 ? "#22d3ee" : "rgba(34,211,238,0.55)"} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
