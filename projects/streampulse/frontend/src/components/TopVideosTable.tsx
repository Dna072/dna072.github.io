import type { SortField, VideoPerformance } from "../types";
import { formatCompactNumber, formatDateTimeLabel, formatPercent } from "../utils/format";
import "./TopVideosTable.css";

interface Column {
  field: SortField;
  label: string;
  render: (v: VideoPerformance) => string;
}

const COLUMNS: Column[] = [
  { field: "views", label: "Views", render: (v) => formatCompactNumber(v.views) },
  { field: "unique_viewers", label: "Uniques", render: (v) => formatCompactNumber(v.unique_viewers) },
  { field: "watch_time_hours", label: "Watch time", render: (v) => `${v.watch_time_hours.toLocaleString()}h` },
  { field: "avg_watch_percent", label: "Avg watched", render: (v) => formatPercent(v.avg_watch_percent) },
  { field: "completion_rate", label: "Completion", render: (v) => formatPercent(v.completion_rate) },
];

interface TopVideosTableProps {
  items: VideoPerformance[];
  sort: SortField;
  order: "asc" | "desc";
  onSortChange: (field: SortField) => void;
}

export default function TopVideosTable({ items, sort, order, onSortChange }: TopVideosTableProps) {
  return (
    <div className="videos-table-wrapper scrollbar-thin">
      <table className="videos-table">
        <thead>
          <tr>
            <th className="videos-table__title-col">Video</th>
            {COLUMNS.map((col) => (
              <th key={col.field}>
                <button
                  type="button"
                  className={`videos-table__sort ${sort === col.field ? "videos-table__sort--active" : ""}`}
                  onClick={() => onSortChange(col.field)}
                >
                  {col.label}
                  {sort === col.field && <span className="videos-table__caret">{order === "desc" ? "▼" : "▲"}</span>}
                </button>
              </th>
            ))}
            <th>Likes</th>
            <th>Comments</th>
            <th>Shares</th>
          </tr>
        </thead>
        <tbody>
          {items.map((video) => (
            <tr key={video.video_id}>
              <td className="videos-table__title-col">
                <div className="videos-table__video">
                  {video.thumbnail_url && <img src={video.thumbnail_url} alt="" loading="lazy" />}
                  <div>
                    <p className="videos-table__title">{video.title}</p>
                    <p className="videos-table__meta">
                      {video.category} · {formatDateTimeLabel(video.published_at)}
                    </p>
                  </div>
                </div>
              </td>
              {COLUMNS.map((col) => (
                <td key={col.field}>{col.render(video)}</td>
              ))}
              <td>{formatCompactNumber(video.likes)}</td>
              <td>{formatCompactNumber(video.comments)}</td>
              <td>{formatCompactNumber(video.shares)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
