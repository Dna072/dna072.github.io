import { Navigate, Route, Routes } from "react-router-dom";
import { useAuth } from "./auth/AuthContext";
import { WorkspaceProvider } from "./workspace/WorkspaceContext";
import { LoadingState } from "./components/States";
import { AppLayout } from "./pages/AppLayout";
import { LibraryPage } from "./pages/LibraryPage";
import { LoginPage } from "./pages/LoginPage";
import { MembersPage } from "./pages/MembersPage";

export default function App() {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div style={{ height: "100vh" }}>
        <LoadingState label="Starting MediaVault…" />
      </div>
    );
  }

  if (!user) {
    return (
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    );
  }

  return (
    <WorkspaceProvider>
      <Routes>
        <Route element={<AppLayout />}>
          <Route path="/library" element={<LibraryPage />} />
          <Route path="/members" element={<MembersPage />} />
        </Route>
        <Route path="*" element={<Navigate to="/library" replace />} />
      </Routes>
    </WorkspaceProvider>
  );
}
