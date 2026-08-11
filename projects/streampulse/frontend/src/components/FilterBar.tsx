import { useVideoCatalog } from '../lib/queries';
import type { AnalyticsFilters } from '../lib/types';

function isoDaysAgo(days: number): string {
  const d = new Date();
  d.setUTCDate(d.getUTCDate() - days);
  return d.toISOString().slice(0, 10);
}

function todayIso(): string {
  return new Date().toISOString().slice(0, 10);
}

const PRESETS = [
  { label: '7d', days: 7 },
  { label: '30d', days: 30 },
  { label: '90d', days: 90 },
];

export default function FilterBar({
  filters,
  onChange,
}: {
  filters: AnalyticsFilters;
  onChange: (next: AnalyticsFilters) => void;
}) {
  const catalog = useVideoCatalog();

  const activePreset = PRESETS.find(
    (p) => filters.startDate === isoDaysAgo(p.days) && filters.endDate === todayIso(),
  );

  function applyPreset(days: number) {
    onChange({ ...filters, startDate: isoDaysAgo(days), endDate: todayIso() });
  }

  return (
    <div className="filterbar">
      <div className="field">
        <label>Quick range</label>
        <div className="preset-group">
          {PRESETS.map((p) => (
            <button
              key={p.label}
              className={`preset ${activePreset?.days === p.days ? 'active' : ''}`}
              onClick={() => applyPreset(p.days)}
            >
              {p.label}
            </button>
          ))}
        </div>
      </div>

      <div className="field">
        <label htmlFor="start">Start date</label>
        <input
          id="start"
          type="date"
          value={filters.startDate}
          max={filters.endDate}
          onChange={(e) => onChange({ ...filters, startDate: e.target.value })}
        />
      </div>

      <div className="field">
        <label htmlFor="end">End date</label>
        <input
          id="end"
          type="date"
          value={filters.endDate}
          min={filters.startDate}
          max={todayIso()}
          onChange={(e) => onChange({ ...filters, endDate: e.target.value })}
        />
      </div>

      <div className="field">
        <label htmlFor="video">Video</label>
        <select
          id="video"
          value={filters.videoId ?? ''}
          onChange={(e) =>
            onChange({
              ...filters,
              videoId: e.target.value ? Number(e.target.value) : null,
            })
          }
        >
          <option value="">All videos</option>
          {catalog.data?.map((v) => (
            <option key={v.id} value={v.id}>
              {v.title}
            </option>
          ))}
        </select>
      </div>

      <div className="spacer" />

      <label className="toggle" title="Compare with the previous equal-length period">
        <input
          type="checkbox"
          checked={filters.compare}
          onChange={(e) => onChange({ ...filters, compare: e.target.checked })}
        />
        Compare to previous period
      </label>
    </div>
  );
}
