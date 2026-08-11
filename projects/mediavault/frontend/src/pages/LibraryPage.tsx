import { useQuery } from "@tanstack/react-query";
import { useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { assetApi, folderApi, searchApi, tagApi, type AssetQuery } from "../api/resources";
import type { Asset } from "../api/types";
import { useWorkspace } from "../workspace/WorkspaceContext";
import { AssetGrid } from "../components/AssetGrid";
import { AssetTable } from "../components/AssetTable";
import { AssetDrawer } from "../components/AssetDrawer";
import { UploadModal } from "../components/UploadModal";
import { AssetGridSkeleton, EmptyState, ErrorState } from "../components/States";
import { Icon } from "../lib/icons";

const KINDS = ["VIDEO", "IMAGE", "DOCUMENT", "OTHER"] as const;
const PAGE_SIZE = 24;

export function LibraryPage() {
  const { currentId, current } = useWorkspace();
  const wsId = currentId!;
  const [params, setParams] = useSearchParams();

  const folderId = params.get("folder");
  const q = params.get("q") ?? "";

  const [view, setView] = useState<"grid" | "list">("grid");
  const [kind, setKind] = useState<string>("");
  const [tagIds, setTagIds] = useState<string[]>([]);
  const [includeSub, setIncludeSub] = useState(true);
  const [sortBy, setSortBy] = useState("created_at");
  const [sortDir, setSortDir] = useState("desc");
  const [page, setPage] = useState(1);
  const [selected, setSelected] = useState<Asset | null>(null);
  const [showUpload, setShowUpload] = useState(false);

  const { data: tags = [] } = useQuery({ queryKey: ["tags", wsId], queryFn: () => tagApi.list(wsId) });

  const { data: breadcrumbs = [] } = useQuery({
    queryKey: ["breadcrumbs", wsId, folderId],
    queryFn: () => folderApi.breadcrumbs(wsId, folderId!),
    enabled: !!folderId,
  });

  const query: AssetQuery = useMemo(
    () => ({
      page,
      page_size: PAGE_SIZE,
      folder_id: folderId,
      include_subfolders: includeSub,
      kind: kind || undefined,
      tag_ids: tagIds.length ? tagIds : undefined,
      sort_by: sortBy,
      sort_dir: sortDir,
    }),
    [page, folderId, includeSub, kind, tagIds, sortBy, sortDir],
  );

  const searching = q.trim().length > 0;

  const listQuery = useQuery({
    queryKey: ["assets", wsId, query],
    queryFn: () => assetApi.list(wsId, query),
    enabled: !searching,
  });

  const searchQuery = useQuery({
    queryKey: ["search", wsId, q, kind, tagIds, page],
    queryFn: () =>
      searchApi.search(wsId, {
        q,
        page,
        page_size: PAGE_SIZE,
        kind: kind || undefined,
        tag_ids: tagIds.length ? tagIds : undefined,
      }),
    enabled: searching,
  });

  const pageData = searching ? searchQuery.data?.results : listQuery.data;
  const isLoading = searching ? searchQuery.isLoading : listQuery.isLoading;
  const error = searching ? searchQuery.error : listQuery.error;
  const assets = pageData?.items ?? [];

  const setSearch = (value: string) => {
    const next = new URLSearchParams(params);
    if (value) next.set("q", value);
    else next.delete("q");
    setParams(next);
    setPage(1);
  };

  const toggleTag = (id: string) => {
    setTagIds((prev) => (prev.includes(id) ? prev.filter((t) => t !== id) : [...prev, id]));
    setPage(1);
  };

  const onSort = (field: string) => {
    if (sortBy === field) setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    else {
      setSortBy(field);
      setSortDir("asc");
    }
  };

  const canWrite = current?.role !== "VIEWER";
  const title = searching
    ? `Search: “${q}”`
    : breadcrumbs.length
      ? breadcrumbs[breadcrumbs.length - 1].name
      : "All assets";

  return (
    <div className="main">
      <div className="topbar">
        <div className="search-box">
          <Icon.Search size={17} className="icon" />
          <input
            className="input"
            placeholder="Search assets by name, description or filename…"
            value={q}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        <div className="spacer" />
        {canWrite && (
          <button className="btn btn-primary" onClick={() => setShowUpload(true)}>
            <Icon.Upload size={16} /> Upload
          </button>
        )}
      </div>

      <div className="content">
        <div className="content-header">
          <h1>{title}</h1>
          {!searching && breadcrumbs.length > 0 && (
            <div className="breadcrumbs">
              <span>·</span>
              <a onClick={() => setSearch("")}>Root</a>
              {breadcrumbs.map((b) => (
                <span key={b.id} style={{ display: "flex", alignItems: "center", gap: 6 }}>
                  <Icon.Chevron size={13} /> {b.name}
                </span>
              ))}
            </div>
          )}
        </div>

        <div className="toolbar">
          <button
            className={`filter-chip ${kind === "" ? "active" : ""}`}
            onClick={() => {
              setKind("");
              setPage(1);
            }}
          >
            All types
          </button>
          {KINDS.map((k) => (
            <button
              key={k}
              className={`filter-chip ${kind === k ? "active" : ""}`}
              onClick={() => {
                setKind(kind === k ? "" : k);
                setPage(1);
              }}
            >
              {k.charAt(0) + k.slice(1).toLowerCase()}
            </button>
          ))}

          {tags.length > 0 && <span style={{ width: 1, height: 20, background: "var(--border)", margin: "0 4px" }} />}
          {tags.map((tag) => (
            <button
              key={tag.id}
              className={`filter-chip ${tagIds.includes(tag.id) ? "active" : ""}`}
              onClick={() => toggleTag(tag.id)}
            >
              <span className="tag-dot" style={{ background: tag.color }} />
              {tag.name}
            </button>
          ))}

          <div className="spacer" />

          {!searching && folderId && (
            <label className="filter-chip" style={{ cursor: "pointer" }}>
              <input
                type="checkbox"
                checked={includeSub}
                onChange={(e) => setIncludeSub(e.target.checked)}
                style={{ accentColor: "var(--accent)" }}
              />
              Include subfolders
            </label>
          )}

          <div className="view-toggle">
            <button className={view === "grid" ? "active" : ""} onClick={() => setView("grid")} aria-label="Grid view">
              <Icon.Grid size={16} />
            </button>
            <button className={view === "list" ? "active" : ""} onClick={() => setView("list")} aria-label="List view">
              <Icon.List size={16} />
            </button>
          </div>
        </div>

        {isLoading ? (
          <AssetGridSkeleton />
        ) : error ? (
          <ErrorState
            message={(error as Error).message}
            onRetry={() => (searching ? searchQuery.refetch() : listQuery.refetch())}
          />
        ) : assets.length === 0 ? (
          <EmptyState
            title={searching ? "No matching assets" : "This space is empty"}
            hint={
              searching
                ? "Try a different search term or clear your filters."
                : canWrite
                  ? "Upload your first asset to get started."
                  : "No assets have been added here yet."
            }
            action={
              !searching && canWrite ? (
                <button className="btn btn-primary" onClick={() => setShowUpload(true)}>
                  <Icon.Upload size={16} /> Upload asset
                </button>
              ) : undefined
            }
          />
        ) : view === "grid" ? (
          <AssetGrid assets={assets} onOpen={setSelected} />
        ) : (
          <AssetTable assets={assets} onOpen={setSelected} sortBy={sortBy} sortDir={sortDir} onSort={onSort} />
        )}

        {pageData && pageData.pages > 1 && (
          <div style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: 12, marginTop: 22 }}>
            <button className="btn btn-sm" disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>
              Previous
            </button>
            <span className="muted" style={{ fontSize: 13 }}>
              Page {pageData.page} of {pageData.pages} · {pageData.total} assets
            </span>
            <button className="btn btn-sm" disabled={page >= pageData.pages} onClick={() => setPage((p) => p + 1)}>
              Next
            </button>
          </div>
        )}
      </div>

      {selected && <AssetDrawer asset={selected} onClose={() => setSelected(null)} />}
      {showUpload && <UploadModal folderId={folderId} onClose={() => setShowUpload(false)} />}
    </div>
  );
}
