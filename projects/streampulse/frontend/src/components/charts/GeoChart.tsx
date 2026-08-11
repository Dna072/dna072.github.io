import { formatNumber, formatPercent } from '../../lib/format';
import type { BreakdownResponse } from '../../lib/types';

export default function GeoChart({ data }: { data: BreakdownResponse }) {
  const max = Math.max(...data.rows.map((r) => r.views), 1);

  return (
    <table>
      <thead>
        <tr>
          <th>Country</th>
          <th className="bar-cell">Share</th>
          <th className="num">Views</th>
        </tr>
      </thead>
      <tbody>
        {data.rows.map((r) => (
          <tr key={r.key}>
            <td>{r.label}</td>
            <td className="bar-cell">
              <div className="mini-bar-track">
                <div className="mini-bar" style={{ width: `${(r.views / max) * 100}%` }} />
              </div>
              <small style={{ color: 'var(--text-dim)' }}>{formatPercent(r.share)}</small>
            </td>
            <td className="num">{formatNumber(r.views)}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
