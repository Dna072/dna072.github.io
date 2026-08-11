import { Cell, Legend, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";
import type { DeviceBreakdown } from "../types";
import "./DeviceChart.css";

const DEVICE_COLORS: Record<string, string> = {
  mobile: "#22d3ee",
  desktop: "#818cf8",
  tablet: "#a78bfa",
  tv: "#34d399",
};

const DEVICE_LABELS: Record<string, string> = {
  mobile: "Mobile",
  desktop: "Desktop",
  tablet: "Tablet",
  tv: "TV",
};

function DeviceTooltip({ active, payload }: any) {
  if (!active || !payload?.length) return null;
  const item: DeviceBreakdown = payload[0].payload;
  return (
    <div className="ts-tooltip">
      <p className="ts-tooltip__row">
        <strong>{DEVICE_LABELS[item.device_type] ?? item.device_type}</strong>
      </p>
      <p className="ts-tooltip__row">{item.views.toLocaleString()} views · {item.share_percent.toFixed(1)}%</p>
    </div>
  );
}

export default function DeviceChart({ devices }: { devices: DeviceBreakdown[] }) {
  return (
    <div className="device-chart">
      <ResponsiveContainer width="100%" height={220}>
        <PieChart>
          <Pie
            data={devices}
            dataKey="views"
            nameKey="device_type"
            innerRadius={56}
            outerRadius={86}
            paddingAngle={2}
            strokeWidth={0}
          >
            {devices.map((d) => (
              <Cell key={d.device_type} fill={DEVICE_COLORS[d.device_type] ?? "#8b98ab"} />
            ))}
          </Pie>
          <Tooltip content={<DeviceTooltip />} />
          <Legend
            verticalAlign="bottom"
            height={36}
            formatter={(value: string) => DEVICE_LABELS[value] ?? value}
            wrapperStyle={{ fontSize: 12, color: "#8b98ab" }}
          />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}
