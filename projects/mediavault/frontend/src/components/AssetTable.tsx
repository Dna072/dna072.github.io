import type { Asset } from "../api/types";
import { formatBytes, formatRelative } from "../lib/format";
import { kindIcon } from "../lib/icons";

interface Props {
  assets: Asset[];
  onOpen: (asset: Asset) => void;
  sortBy: string;
  sortDir: string;
  onSort: (field: string) => void;
}

const COLUMNS: { key: string; label: string; sortable?: boolean }[] = [
  { key: "name", label: "Name", sortable: true },
  { key: "kind", label: "Type" },
  { key: "size_bytes", label: "Size", sortable: true },
  { key: "tags", label: "Tags" },
  { key: "created_at", label: "Added", sortable: true },
];

export function AssetTable({ assets, onOpen, sortBy, sortDir, onSort }: Props) {
  return (
    <div className="card" style={{ overflow: "hidden" }}>
      <table className="table">
        <thead>
          <tr>
            {COLUMNS.map((col) => (
              <th
                key={col.key}
                onClick={() => col.sortable && onSort(col.key)}
                style={{ cursor: col.sortable ? "pointer" : "default", userSelect: "none" }}
              >
                {col.label}
                {col.sortable && sortBy === col.key && (sortDir === "asc" ? " ↑" : " ↓")}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {assets.map((asset) => {
            const KindIcon = kindIcon(asset.kind);
            return (
              <tr key={asset.id} onClick={() => onOpen(asset)}>
                <td>
                  <span className="cell-name">
                    <KindIcon size={17} />
                    {asset.name}
                  </span>
                </td>
                <td className="muted">{asset.kind}</td>
                <td className="muted">{formatBytes(asset.size_bytes)}</td>
                <td>
                  <div style={{ display: "flex", gap: 4, flexWrap: "wrap" }}>
                    {asset.tags.slice(0, 2).map((tag) => (
                      <span key={tag.id} className="tag-chip">
                        <span className="tag-dot" style={{ background: tag.color }} />
                        {tag.name}
                      </span>
                    ))}
                    {asset.tags.length > 2 && (
                      <span className="tag-chip">+{asset.tags.length - 2}</span>
                    )}
                  </div>
                </td>
                <td className="muted">{formatRelative(asset.created_at)}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
