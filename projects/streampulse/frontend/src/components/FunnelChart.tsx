import { Cell, Funnel, FunnelChart as RechartsFunnel, LabelList, ResponsiveContainer, Tooltip } from "recharts";
import type { FunnelStage } from "../types";
import { formatCompactNumber } from "../utils/format";
import "./FunnelChart.css";

const COLORS = ["#22d3ee", "#38bdf8", "#818cf8", "#a78bfa", "#34d399"];

interface FunnelChartProps {
  stages: FunnelStage[];
}

function FunnelTooltip({ active, payload }: any) {
  if (!active || !payload?.length) return null;
  const stage = payload[0]?.payload;
  if (!stage) return null;
  return (
    <div className="ts-tooltip">
      <p className="ts-tooltip__row">
        <strong>{stage.label}</strong>
      </p>
      <p className="ts-tooltip__row">{formatCompactNumber(stage.count)} viewers · {stage.percent_of_plays.toFixed(1)}% of plays</p>
    </div>
  );
}

export default function FunnelChart({ stages }: FunnelChartProps) {
  const data = stages.map((s) => ({ ...s, name: s.label, value: s.count }));

  return (
    <div className="funnel-chart">
      <ResponsiveContainer width="100%" height={260}>
        <RechartsFunnel width={400} height={260}>
          <Tooltip content={<FunnelTooltip />} />
          <Funnel dataKey="value" data={data} isAnimationActive nameKey="name">
            {data.map((entry, index) => (
              <Cell key={entry.stage} fill={COLORS[index % COLORS.length]} />
            ))}
            <LabelList position="right" dataKey="name" fill="#e7edf6" stroke="none" fontSize={12} />
          </Funnel>
        </RechartsFunnel>
      </ResponsiveContainer>
      <ul className="funnel-chart__stats">
        {stages.map((stage, index) => (
          <li key={stage.stage}>
            <span className="funnel-chart__dot" style={{ background: COLORS[index % COLORS.length] }} />
            <span className="funnel-chart__label">{stage.label}</span>
            <span className="funnel-chart__value">{formatCompactNumber(stage.count)}</span>
            <span className="funnel-chart__pct">{stage.percent_of_plays.toFixed(1)}%</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
