import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect } from "react";
import { API_BASE } from "../api/client";
import { assetApi, shareApi, tagApi } from "../api/resources";
import type { Asset } from "../api/types";
import { useWorkspace } from "../workspace/WorkspaceContext";
import { formatBytes, formatDate } from "../lib/format";
import { Icon, kindIcon } from "../lib/icons";
import { Spinner } from "./States";
import { useToast } from "./Toast";

interface Props {
  asset: Asset;
  onClose: () => void;
}

export function AssetDrawer({ asset: initial, onClose }: Props) {
  const { currentId, current } = useWorkspace();
  const wsId = currentId!;
  const qc = useQueryClient();
  const toast = useToast();
  const canWrite = current?.role !== "VIEWER";
  const KindIcon = kindIcon(initial.kind);

  const { data: asset = initial } = useQuery({
    queryKey: ["asset", wsId, initial.id],
    queryFn: () => assetApi.get(wsId, initial.id),
    initialData: initial,
  });

  const { data: signed } = useQuery({
    queryKey: ["signed", wsId, initial.id],
    queryFn: () => assetApi.signedUrl(wsId, initial.id),
  });

  const { data: allTags = [] } = useQuery({
    queryKey: ["tags", wsId],
    queryFn: () => tagApi.list(wsId),
  });

  const { data: shares = [], refetch: refetchShares } = useQuery({
    queryKey: ["shares", wsId, initial.id],
    queryFn: () => shareApi.list(wsId, initial.id),
  });

  const invalidateAssets = () => {
    qc.invalidateQueries({ queryKey: ["assets", wsId] });
    qc.invalidateQueries({ queryKey: ["asset", wsId, initial.id] });
  };

  const toggleTag = useMutation({
    mutationFn: (tagId: string) => {
      const has = asset.tags.some((t) => t.id === tagId);
      const next = has
        ? asset.tags.filter((t) => t.id !== tagId).map((t) => t.id)
        : [...asset.tags.map((t) => t.id), tagId];
      return assetApi.setTags(wsId, asset.id, next);
    },
    onSuccess: invalidateAssets,
    onError: (e: Error) => toast.error(e.message),
  });

  const createShare = useMutation({
    mutationFn: () =>
      shareApi.create(wsId, asset.id, { allow_download: true, expires_in_seconds: 60 * 60 * 24 * 7 }),
    onSuccess: () => {
      refetchShares();
      toast.success("Share link created");
    },
    onError: (e: Error) => toast.error(e.message),
  });

  const revokeShare = useMutation({
    mutationFn: (shareId: string) => shareApi.revoke(wsId, asset.id, shareId),
    onSuccess: () => refetchShares(),
  });

  const removeAsset = useMutation({
    mutationFn: () => assetApi.remove(wsId, asset.id),
    onSuccess: () => {
      invalidateAssets();
      qc.invalidateQueries({ queryKey: ["folders", wsId] });
      toast.success("Asset deleted");
      onClose();
    },
    onError: (e: Error) => toast.error(e.message),
  });

  useEffect(() => {
    const handler = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [onClose]);

  const previewUrl = signed?.url;
  const shareLink = (token: string) => `${window.location.origin}${API_BASE}/shares/${token}`;

  return (
    <div className="overlay" onClick={onClose}>
      <div className="drawer" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2 style={{ fontSize: 15, overflow: "hidden", textOverflow: "ellipsis" }}>{asset.name}</h2>
          <button className="btn btn-ghost btn-sm" onClick={onClose} aria-label="Close">
            <Icon.Close size={16} />
          </button>
        </div>

        <div style={{ overflowY: "auto", flex: 1 }}>
          <div className="drawer-preview">
            {previewUrl && asset.kind === "IMAGE" ? (
              <img src={previewUrl} alt={asset.name} />
            ) : previewUrl && asset.kind === "VIDEO" ? (
              <video src={previewUrl} controls style={{ width: "100%", height: "100%" }} />
            ) : (
              <KindIcon size={48} />
            )}
          </div>

          <div className="drawer-section">
            <div className="meta-row">
              <span className="k">Type</span>
              <span>{asset.content_type}</span>
            </div>
            <div className="meta-row">
              <span className="k">Size</span>
              <span>{formatBytes(asset.size_bytes)}</span>
            </div>
            {asset.width && asset.height && (
              <div className="meta-row">
                <span className="k">Dimensions</span>
                <span>
                  {asset.width} × {asset.height}
                </span>
              </div>
            )}
            <div className="meta-row">
              <span className="k">Status</span>
              <span>{asset.status}</span>
            </div>
            <div className="meta-row">
              <span className="k">Added</span>
              <span>{formatDate(asset.created_at)}</span>
            </div>
            <div className="meta-row">
              <span className="k">Checksum</span>
              <span style={{ fontFamily: "var(--mono)", fontSize: 11 }}>
                {asset.checksum_sha256?.slice(0, 12) ?? "—"}
              </span>
            </div>
            {previewUrl && (
              <a className="btn btn-primary" href={previewUrl} style={{ marginTop: 12, width: "100%", justifyContent: "center" }}>
                <Icon.Download size={16} /> Download
              </a>
            )}
          </div>

          {asset.description && (
            <div className="drawer-section">
              <div className="sidebar-section" style={{ padding: "0 0 8px" }}>
                Description
              </div>
              <p style={{ margin: 0, fontSize: 13 }}>{asset.description}</p>
            </div>
          )}

          <div className="drawer-section">
            <div className="sidebar-section" style={{ padding: "0 0 10px" }}>
              Tags
            </div>
            <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
              {allTags.length === 0 && <span className="muted" style={{ fontSize: 12.5 }}>No tags yet.</span>}
              {allTags.map((tag) => {
                const active = asset.tags.some((t) => t.id === tag.id);
                return (
                  <button
                    key={tag.id}
                    className={`filter-chip ${active ? "active" : ""}`}
                    disabled={!canWrite || toggleTag.isPending}
                    onClick={() => toggleTag.mutate(tag.id)}
                  >
                    <span className="tag-dot" style={{ background: tag.color }} />
                    {tag.name}
                  </button>
                );
              })}
            </div>
          </div>

          <div className="drawer-section">
            <div style={{ display: "flex", alignItems: "center", marginBottom: 10 }}>
              <span className="sidebar-section" style={{ padding: 0, flex: 1 }}>
                Share links
              </span>
              {canWrite && (
                <button
                  className="btn btn-sm"
                  onClick={() => createShare.mutate()}
                  disabled={createShare.isPending}
                >
                  <Icon.Share size={14} /> New link
                </button>
              )}
            </div>
            {shares.filter((s) => !s.revoked).length === 0 && (
              <div className="muted" style={{ fontSize: 12.5 }}>
                No active share links.
              </div>
            )}
            {shares
              .filter((s) => !s.revoked)
              .map((share) => (
                <div
                  key={share.id}
                  style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 8 }}
                >
                  <input
                    className="input"
                    readOnly
                    value={shareLink(share.token)}
                    style={{ fontSize: 11.5, fontFamily: "var(--mono)" }}
                    onFocus={(e) => e.target.select()}
                  />
                  <button
                    className="btn btn-sm"
                    onClick={() => {
                      navigator.clipboard?.writeText(shareLink(share.token));
                      toast.success("Link copied");
                    }}
                  >
                    Copy
                  </button>
                  {canWrite && (
                    <button
                      className="btn btn-danger btn-sm"
                      onClick={() => revokeShare.mutate(share.id)}
                      aria-label="Revoke"
                    >
                      <Icon.Trash size={15} />
                    </button>
                  )}
                </div>
              ))}
          </div>
        </div>

        {canWrite && (
          <div className="modal-footer">
            <button
              className="btn btn-danger"
              onClick={() => {
                if (confirm(`Delete "${asset.name}"? This cannot be undone.`)) removeAsset.mutate();
              }}
              disabled={removeAsset.isPending}
            >
              {removeAsset.isPending ? <Spinner /> : <Icon.Trash size={16} />} Delete
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
