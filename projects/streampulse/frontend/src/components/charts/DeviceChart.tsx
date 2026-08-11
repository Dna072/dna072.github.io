import { Cell, Legend, Pie, PieChart, ResponsiveContainer, Tooltip } from 'recharts';

import { formatNumber, formatPercent } from '../../lib/format';
import type { BreakdownResponse } from '../../lib/types';

const COLORS = ['#22d3ee', '#38bdf8', '#818cf8', '#fb7185', '#34d399', '#fbbf24'];

export default function DeviceChart({ data }: { data: BreakdownResponse }) {
  const rows = data.rows.map((r) => ({ name: r.label, value: r.views, share: r.share }));

  return (
    <ResponsiveContainer width="100%" height={260}>
      <PieChart>
        <Pie
          data={rows}
          dataKey="value"
          nameKey="name"
          innerRadius={62}
          outerRadius={98}
          paddingAngle={2}
          stroke="#0a0f1c"
          strokeWidth={2}
        >
          {rows.map((_, i) => (
            <Cell key={i} fill={COLORS[i % COLORS.length]} />
          ))}
        </Pie>
        <Tooltip
          contentStyle={{ background: '#111a2e', border: '1px solid #2c3d66' }}
          formatter={(value: number, _n, item) => [
            `${formatNumber(value)} views · ${formatPercent(
              (item.payload as { share: number }).share,
            )}`,
            (item.payload as { name: string }).name,
          ]}
        />
        <Legend
          wrapperStyle={{ fontSize: 12, color: '#93a4c4' }}
          iconType="circle"
          formatter={(v) => <span style={{ color: '#93a4c4' }}>{v}</span>}
        />
      </PieChart>
    </ResponsiveContainer>
  );
}
