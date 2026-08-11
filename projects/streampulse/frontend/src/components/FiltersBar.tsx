import { useState } from "react";
import type { DashboardFilters, VideoSummary } from "../types";
import { daysAgoISO, todayISO } from "../utils/format";
import "./FiltersBar.css";

const PRESETS: { key: string; label: string; days: number }[] = [
  { key: "7d", label: "7D", days: 7 },
  { key: "30d", label: "30D", days: 30 },
  { key: "90d", label: "90D", days: 90 },
];

interface FiltersBarProps {
  filters: DashboardFilters;
  onChange: (filters: DashboardFilters) => void;
  videos: VideoSummary[];
  videosLoading: boolean;
}

function detectPreset(filters: DashboardFilters): string {
  if (filters.end !== todayISO()) return "custom";
  for (const preset of PRESETS) {
    if (filters.start === daysAgoISO(preset.days - 1)) return preset.key;
  }
  return "custom";
}

export default function FiltersBar({ filters, onChange, videos, videosLoading }: FiltersBarProps) {
  const [activePreset, setActivePreset] = useState<string>(() => detectPreset(filters));
  const [showCustom, setShowCustom] = useState(activePreset === "custom");

  function applyPreset(preset: { key: string; days: number }) {
    setActivePreset(preset.key);
    setShowCustom(false);
    onChange({ ...filters, start: daysAgoISO(preset.days - 1), end: todayISO() });
  }

  function applyCustom() {
    setActivePreset("custom");
    setShowCustom(true);
  }

  return (
    <div className="filters-bar">
      <div className="filters-bar__group filters-bar__presets" role="group" aria-label="Date range presets">
        {PRESETS.map((preset) => (
          <button
            key={preset.key}
            type="button"
            className={`preset-btn ${activePreset === preset.key ? "preset-btn--active" : ""}`}
            onClick={() => applyPreset(preset)}
          >
            {preset.label}
          </button>
        ))}
        <button
          type="button"
          className={`preset-btn ${activePreset === "custom" ? "preset-btn--active" : ""}`}
          onClick={applyCustom}
        >
          Custom
        </button>
      </div>

      {showCustom && (
        <div className="filters-bar__group filters-bar__dates">
          <label className="filters-bar__field">
            <span>From</span>
            <input
              type="date"
              value={filters.start}
              max={filters.end}
              onChange={(e) => onChange({ ...filters, start: e.target.value })}
            />
          </label>
          <label className="filters-bar__field">
            <span>To</span>
            <input
              type="date"
              value={filters.end}
              min={filters.start}
              max={todayISO()}
              onChange={(e) => onChange({ ...filters, end: e.target.value })}
            />
          </label>
        </div>
      )}

      <div className="filters-bar__group">
        <label className="filters-bar__field">
          <span>Video</span>
          <select
            value={filters.videoId ?? ""}
            disabled={videosLoading}
            onChange={(e) => onChange({ ...filters, videoId: e.target.value ? Number(e.target.value) : null })}
          >
            <option value="">All videos</option>
            {videos.map((v) => (
              <option key={v.id} value={v.id}>
                {v.title}
              </option>
            ))}
          </select>
        </label>
      </div>

      <label className="filters-bar__compare">
        <input
          type="checkbox"
          checked={filters.compare}
          onChange={(e) => onChange({ ...filters, compare: e.target.checked })}
        />
        <span>Compare to previous period</span>
      </label>
    </div>
  );
}
