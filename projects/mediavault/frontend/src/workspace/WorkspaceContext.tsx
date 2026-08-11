import { createContext, useCallback, useContext, useMemo, useState, type ReactNode } from "react";
import { useQuery } from "@tanstack/react-query";
import { workspaceApi } from "../api/resources";
import type { Workspace } from "../api/types";

interface WorkspaceState {
  workspaces: Workspace[];
  current: Workspace | null;
  currentId: string | null;
  setCurrentId: (id: string) => void;
  loading: boolean;
  error: unknown;
  refetch: () => void;
}

const WorkspaceContext = createContext<WorkspaceState | undefined>(undefined);

const LAST_WS_KEY = "mv_last_workspace";

export function WorkspaceProvider({ children }: { children: ReactNode }) {
  const [currentId, setCurrentIdState] = useState<string | null>(
    () => localStorage.getItem(LAST_WS_KEY),
  );

  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ["workspaces"],
    queryFn: workspaceApi.list,
  });

  const setCurrentId = useCallback((id: string) => {
    localStorage.setItem(LAST_WS_KEY, id);
    setCurrentIdState(id);
  }, []);

  const value = useMemo<WorkspaceState>(() => {
    const workspaces = data ?? [];
    const resolvedId =
      currentId && workspaces.some((w) => w.id === currentId)
        ? currentId
        : (workspaces[0]?.id ?? null);
    const current = workspaces.find((w) => w.id === resolvedId) ?? null;
    return {
      workspaces,
      current,
      currentId: resolvedId,
      setCurrentId,
      loading: isLoading,
      error,
      refetch,
    };
  }, [data, currentId, setCurrentId, isLoading, error, refetch]);

  return <WorkspaceContext.Provider value={value}>{children}</WorkspaceContext.Provider>;
}

// eslint-disable-next-line react-refresh/only-export-components
export function useWorkspace(): WorkspaceState {
  const ctx = useContext(WorkspaceContext);
  if (!ctx) throw new Error("useWorkspace must be used within WorkspaceProvider");
  return ctx;
}
