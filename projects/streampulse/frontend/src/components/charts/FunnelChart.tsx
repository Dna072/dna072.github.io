import { formatNumber, formatPercent } from '../../lib/format';
import type { FunnelResponse } from '../../lib/types';

export default function FunnelChart({ data }: { data: FunnelResponse }) {
  const top = data.stages[0]?.count || 1;

  return (
    <div className="funnel">
      {data.stages.map((s, i) => {
        const widthPct = Math.max((s.count / top) * 100, 2);
        // Conversion from the immediately preceding stage.
        const prev = i === 0 ? null : data.stages[i - 1].count;
        const stepConv = prev && prev > 0 ? s.count / prev : null;
        return (
          <div className="funnel-row" key={s.stage}>
            <div className="name">{s.stage}</div>
            <div className="funnel-track">
              <div className="funnel-fill" style={{ width: `${widthPct}%` }}>
                {formatNumber(s.count)}
              </div>
            </div>
            <div className="pct">
              {formatPercent(s.pct_of_top)}
              {stepConv !== null && <small> · {formatPercent(stepConv, 0)} step</small>}
            </div>
          </div>
        );
      })}
    </div>
  );
}
