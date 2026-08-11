import { formatNumber, formatPercent } from '../lib/format';
import type { VideoPerformancePage } from '../lib/types';

type SortKey = 'views' | 'watch_hours' | 'engagement_rate' | 'completion_rate';

const COLUMNS: { key: SortKey; label: string }[] = [
  { key: 'views', label: 'Views' },
  { key: 'watch_hours', label: 'Watch h' },
  { key: 'engagement_rate', label: 'Engmt' },
  { key: 'completion_rate', label: 'Compl.' },
];

export default function TopVideosTable({
  data,
  sortBy,
  onSort,
  page,
  onPage,
}: {
  data: VideoPerformancePage;
  sortBy: SortKey;
  onSort: (key: SortKey) => void;
  page: number;
  onPage: (page: number) => void;
}) {
  const pageSize = data.limit;
  const totalPages = Math.max(Math.ceil(data.total / pageSize), 1);
  const startRank = page * pageSize;

  return (
    <>
      <table>
        <thead>
          <tr>
            <th className="rank">#</th>
            <th>Video</th>
            {COLUMNS.map((c) => (
              <th
                key={c.key}
                className={`num ${sortBy === c.key ? 'sorted' : ''}`}
                onClick={() => onSort(c.key)}
                title={`Sort by ${c.label}`}
              >
                {c.label} {sortBy === c.key ? '▾' : ''}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.items.map((v, i) => (
            <tr key={v.video_id}>
              <td className="rank">{startRank + i + 1}</td>
              <td>
                <div>{v.title}</div>
                <span className="chip">{v.category}</span>
              </td>
              <td className="num">{formatNumber(v.views)}</td>
              <td className="num">{formatNumber(v.watch_hours)}</td>
              <td className="num">{formatPercent(v.engagement_rate)}</td>
              <td className="num">{formatPercent(v.completion_rate)}</td>
            </tr>
          ))}
        </tbody>
      </table>

      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          marginTop: 14,
          color: 'var(--text-dim)',
          fontSize: 13,
        }}
      >
        <span>
          {data.total} video{data.total === 1 ? '' : 's'} with views · page {page + 1} of{' '}
          {totalPages}
        </span>
        <div style={{ display: 'flex', gap: 8 }}>
          <button className="btn ghost" disabled={page === 0} onClick={() => onPage(page - 1)}>
            Prev
          </button>
          <button
            className="btn ghost"
            disabled={page + 1 >= totalPages}
            onClick={() => onPage(page + 1)}
          >
            Next
          </button>
        </div>
      </div>
    </>
  );
}
