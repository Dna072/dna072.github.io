import type { Asset } from "../api/types";
import { formatBytes, formatRelative } from "../lib/format";
import { kindIcon } from "../lib/icons";

interface Props {
  assets: Asset[];
  onOpen: (asset: Asset) => void;
}

export function AssetGrid({ assets, onOpen }: Props) {
  return (
    <div className="asset-grid">
      {assets.map((asset) => {
        const KindIcon = kindIcon(asset.kind);
        return (
          <div
            key={asset.id}
            className="card asset-card"
            onClick={() => onOpen(asset)}
            role="button"
            tabIndex={0}
            onKeyDown={(e) => e.key === "Enter" && onOpen(asset)}
          >
            <div className="asset-thumb">
              <KindIcon size={34} />
              <span className="asset-kind-pill">{asset.kind}</span>
            </div>
            <div className="asset-body">
              <div className="asset-name" title={asset.name}>
                {asset.name}
              </div>
              <div className="asset-meta">
                <span>{formatBytes(asset.size_bytes)}</span>
                <span>·</span>
                <span>{formatRelative(asset.created_at)}</span>
              </div>
              {asset.tags.length > 0 && (
                <div className="asset-tags">
                  {asset.tags.slice(0, 3).map((tag) => (
                    <span key={tag.id} className="tag-chip">
                      <span className="tag-dot" style={{ background: tag.color }} />
                      {tag.name}
                    </span>
                  ))}
                  {asset.tags.length > 3 && (
                    <span className="tag-chip">+{asset.tags.length - 3}</span>
                  )}
                </div>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}
