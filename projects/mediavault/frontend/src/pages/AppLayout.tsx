import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { Outlet } from "react-router-dom";
import { workspaceApi } from "../api/resources";
import { Sidebar } from "../components/Sidebar";
import { LoadingState } from "../components/States";
import { useToast } from "../components/Toast";
import { useWorkspace } from "../workspace/WorkspaceContext";
import { Icon } from "../lib/icons";

export function AppLayout() {
  const { workspaces, loading, setCurrentId } = useWorkspace();

  if (loading) {
    return <LoadingState label="Loading your workspaces…" />;
  }

  if (workspaces.length === 0) {
    return <CreateFirstWorkspace onCreated={(id) => setCurrentId(id)} />;
  }

  return (
    <div className="app-shell">
      <Sidebar />
      <Outlet />
    </div>
  );
}

function CreateFirstWorkspace({ onCreated }: { onCreated: (id: string) => void }) {
  const qc = useQueryClient();
  const toast = useToast();
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");

  const create = useMutation({
    mutationFn: () => workspaceApi.create(name.trim(), description.trim()),
    onSuccess: async (ws) => {
      await qc.invalidateQueries({ queryKey: ["workspaces"] });
      onCreated(ws.id);
      toast.success("Workspace created");
    },
    onError: (e: Error) => toast.error(e.message),
  });

  return (
    <div style={{ minHeight: "100vh", display: "grid", placeItems: "center", padding: 24 }}>
      <div className="card" style={{ padding: 30, maxWidth: 440, width: "100%" }}>
        <div className="logo" style={{ display: "grid", placeItems: "center", width: 42, height: 42, borderRadius: 11, background: "var(--accent)", color: "#fff", marginBottom: 16 }}>
          <Icon.Vault size={24} />
        </div>
        <h1 style={{ fontSize: 22, margin: "0 0 4px" }}>Create your first workspace</h1>
        <p className="muted" style={{ marginTop: 0 }}>
          Workspaces keep each team's media, folders and members separate.
        </p>
        <div className="field">
          <label htmlFor="ws-name">Workspace name</label>
          <input
            id="ws-name"
            className="input"
            value={name}
            autoFocus
            onChange={(e) => setName(e.target.value)}
            placeholder="Creative Studio"
          />
        </div>
        <div className="field">
          <label htmlFor="ws-desc">Description (optional)</label>
          <textarea
            id="ws-desc"
            className="textarea"
            rows={2}
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="What will this workspace hold?"
          />
        </div>
        <button
          className="btn btn-primary"
          style={{ width: "100%", justifyContent: "center" }}
          disabled={!name.trim() || create.isPending}
          onClick={() => create.mutate()}
        >
          {create.isPending ? "Creating…" : "Create workspace"}
        </button>
      </div>
    </div>
  );
}
