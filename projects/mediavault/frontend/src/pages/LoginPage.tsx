import { useState } from "react";
import { useAuth } from "../auth/AuthContext";
import { ApiClientError } from "../api/client";
import { Icon } from "../lib/icons";

export function LoginPage() {
  const { login, register } = useAuth();
  const [mode, setMode] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setBusy(true);
    try {
      if (mode === "login") await login(email, password);
      else await register(email, password, fullName);
    } catch (err) {
      const message =
        err instanceof ApiClientError ? err.message : "Unable to connect. Please try again.";
      setError(message);
    } finally {
      setBusy(false);
    }
  };

  const useDemo = () => {
    setMode("login");
    setEmail("admin@mediavault.dev");
    setPassword("ChangeMe123!");
  };

  return (
    <div className="auth-wrap">
      <div className="auth-hero">
        <div style={{ display: "flex", alignItems: "center", gap: 10, fontWeight: 700, fontSize: 18 }}>
          <span className="logo" style={{ display: "grid", placeItems: "center", width: 34, height: 34, borderRadius: 9, background: "var(--teal-600)" }}>
            <Icon.Vault size={20} />
          </span>
          MediaVault
        </div>
        <h1>The asset library built for video-first creative teams.</h1>
        <ul>
          <li>
            <Icon.Folder size={18} className="check" />
            Organize footage in nested folders with fast full-text search.
          </li>
          <li>
            <Icon.Users size={18} className="check" />
            Role-based access — admins, members and viewers per workspace.
          </li>
          <li>
            <Icon.Share size={18} className="check" />
            Signed, expiring links for secure external delivery.
          </li>
        </ul>
        <p style={{ color: "rgba(255,255,255,0.6)", fontSize: 12.5, maxWidth: 420 }}>
          A production-style portfolio project. No real customer data.
        </p>
      </div>

      <div className="auth-panel">
        <div className="auth-card">
          <h2>{mode === "login" ? "Welcome back" : "Create your account"}</h2>
          <p className="muted" style={{ marginTop: 0 }}>
            {mode === "login"
              ? "Sign in to your workspace."
              : "Start organizing your media in minutes."}
          </p>

          {error && <div className="error-banner">{error}</div>}

          <form onSubmit={submit}>
            {mode === "register" && (
              <div className="field">
                <label htmlFor="name">Full name</label>
                <input
                  id="name"
                  className="input"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  placeholder="Jordan Rivera"
                />
              </div>
            )}
            <div className="field">
              <label htmlFor="email">Email</label>
              <input
                id="email"
                type="email"
                className="input"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@studio.com"
              />
            </div>
            <div className="field">
              <label htmlFor="password">Password</label>
              <input
                id="password"
                type="password"
                className="input"
                required
                minLength={8}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
              />
            </div>
            <button className="btn btn-primary" style={{ width: "100%", justifyContent: "center" }} disabled={busy}>
              {busy ? "Please wait…" : mode === "login" ? "Sign in" : "Create account"}
            </button>
          </form>

          <div style={{ marginTop: 16, fontSize: 13, textAlign: "center" }} className="muted">
            {mode === "login" ? "New to MediaVault?" : "Already have an account?"}{" "}
            <button
              className="btn btn-ghost btn-sm"
              style={{ padding: 0, color: "var(--accent)" }}
              onClick={() => {
                setMode(mode === "login" ? "register" : "login");
                setError(null);
              }}
            >
              {mode === "login" ? "Create one" : "Sign in"}
            </button>
          </div>

          <div className="demo-hint">
            Demo account: <code>admin@mediavault.dev</code> / <code>ChangeMe123!</code>{" "}
            <button className="btn btn-ghost btn-sm" style={{ padding: "2px 6px", color: "var(--accent)" }} onClick={useDemo}>
              Use demo
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
