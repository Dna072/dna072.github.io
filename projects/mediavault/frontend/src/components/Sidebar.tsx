import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { NavLink, useLocation, useNavigate, useSearchParams } from "react-router-dom";
import { useState } from "react";
import { folderApi } from "../api/resources";
import { useAuth } from "../auth/AuthContext";
import { useWorkspace } from "../workspace/WorkspaceContext";
import { initials } from "../lib/format";
import { Icon } from "../lib/icons";
import { FolderTree } from "./FolderTree";
import { Modal } from "./Modal";
import { ThemeToggle } from "./ThemeToggle";
import { useToast } from "./Toast";

export function Sidebar() {
  const { user, logout } = useAuth();
  const { workspaces, current, currentId, setCurrentId } = useWorkspace();
  const [params, setParams] = useSearchParams();
  const navigate = useNavigate();
  const location = useLocation();
  const qc = useQueryClient();
  const toast = useToast();
  const [showNewFolder, setShowNewFolder] = useState(false);
  const [folderName, setFolderName] = useState("");

  const selectedFolder = params.get("folder");

  const { data: folders = [] } = useQuery({
    queryKey: ["folders", currentId],
    queryFn: () => folderApi.tree(currentId!),
    enabled: !!currentId,
  });

  const createFolder = useMutation({
    mutationFn: () => folderApi.create(currentId!, folderName.trim(), null),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["folders", currentId] });
      setShowNewFolder(false);
      setFolderName("");
      toast.success("Folder created");
    },
    onError: (e: Error) => toast.error(e.message),
  });

  const selectFolder = (id: string | null) => {
    const next = new URLSearchParams(params);
    if (id) next.set("folder", id);
    else next.delete("folder");
    next.delete("q");
    if (location.pathname !== "/library") navigate(`/library?${next.toString()}`);
    else setParams(next);
  };

  return (
    <aside className="sidebar">
      <div className="sidebar-brand">
        <span className="logo">
          <Icon.Vault size={18} />
        </span>
        MediaVault
      </div>

      <div className="ws-switcher">
        <select
          className="select"
          value={currentId ?? ""}
          onChange={(e) => setCurrentId(e.target.value)}
          aria-label="Select workspace"
        >
          {workspaces.map((w) => (
            <option key={w.id} value={w.id}>
              {w.name}
            </option>
          ))}
        </select>
      </div>

      <nav className="nav">
        <NavLink to="/library" className={({ isActive }) => `nav-item ${isActive ? "active" : ""}`}>
          <Icon.Library size={17} /> Library
        </NavLink>
        <NavLink to="/members" className={({ isActive }) => `nav-item ${isActive ? "active" : ""}`}>
          <Icon.Users size={17} /> People
        </NavLink>
      </nav>

      <div className="sidebar-section" style={{ display: "flex", alignItems: "center" }}>
        <span style={{ flex: 1 }}>Folders</span>
        {current && current.role !== "VIEWER" && (
          <button
            className="btn btn-ghost btn-sm"
            style={{ padding: 2 }}
            onClick={() => setShowNewFolder(true)}
            aria-label="New folder"
            title="New folder"
          >
            <Icon.Plus size={15} />
          </button>
        )}
      </div>
      <div className="sidebar-scroll">
        <FolderTree nodes={folders} selectedId={selectedFolder} onSelect={selectFolder} />
      </div>

      <div className="sidebar-footer">
        <span className="avatar">{initials(user?.full_name ?? "", user?.email ?? "?")}</span>
        <div style={{ flex: 1, overflow: "hidden" }}>
          <div
            style={{
              fontSize: 13,
              fontWeight: 600,
              whiteSpace: "nowrap",
              overflow: "hidden",
              textOverflow: "ellipsis",
            }}
          >
            {user?.full_name || user?.email}
          </div>
          <div className="muted" style={{ fontSize: 11 }}>
            {current?.role ?? ""}
          </div>
        </div>
        <ThemeToggle />
        <button className="btn btn-ghost btn-sm" onClick={logout} aria-label="Log out" title="Log out">
          <Icon.Logout size={17} />
        </button>
      </div>

      {showNewFolder && (
        <Modal
          title="New folder"
          onClose={() => setShowNewFolder(false)}
          footer={
            <>
              <button className="btn" onClick={() => setShowNewFolder(false)}>
                Cancel
              </button>
              <button
                className="btn btn-primary"
                disabled={!folderName.trim() || createFolder.isPending}
                onClick={() => createFolder.mutate()}
              >
                Create
              </button>
            </>
          }
        >
          <div className="field">
            <label htmlFor="folder-name">Folder name</label>
            <input
              id="folder-name"
              className="input"
              value={folderName}
              autoFocus
              onChange={(e) => setFolderName(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && folderName.trim() && createFolder.mutate()}
              placeholder="e.g. Brand Campaigns"
            />
          </div>
        </Modal>
      )}
    </aside>
  );
}
