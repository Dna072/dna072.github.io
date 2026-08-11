import { useState, type FormEvent } from 'react';

import { useAuth } from '../context/AuthContext';

const DEMO_EMAIL = 'demo@streampulse.dev';
const DEMO_PASSWORD = 'streampulse-demo';

export default function Login() {
  const { login } = useAuth();
  const [email, setEmail] = useState(DEMO_EMAIL);
  const [password, setPassword] = useState(DEMO_PASSWORD);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setBusy(true);
    try {
      await login(email, password);
    } catch {
      setError('Invalid credentials, or the API is unreachable.');
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="login-wrap">
      <form className="login-card" onSubmit={onSubmit}>
        <div className="brand">
          <span className="logo">S</span>
          <div>
            StreamPulse
            <small>Video Analytics</small>
          </div>
        </div>
        <h1>Sign in</h1>
        <p className="sub">Access the analytics dashboard.</p>

        <div className="field">
          <label htmlFor="email">Email</label>
          <input
            id="email"
            type="email"
            value={email}
            autoComplete="username"
            onChange={(e) => setEmail(e.target.value)}
            required
          />
        </div>
        <div className="field">
          <label htmlFor="password">Password</label>
          <input
            id="password"
            type="password"
            value={password}
            autoComplete="current-password"
            onChange={(e) => setPassword(e.target.value)}
            required
          />
        </div>

        {error && <div className="error-text">{error}</div>}

        <button className="btn" type="submit" disabled={busy} style={{ width: '100%', marginTop: 8 }}>
          {busy ? 'Signing in…' : 'Sign in'}
        </button>

        <div className="hint">
          <strong>Demo credentials</strong> are pre-filled. This is a portfolio project
          seeded with synthetic data — not real traffic.
        </div>
      </form>
    </div>
  );
}
