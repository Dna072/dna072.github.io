import { useAuth } from "../context/AuthContext";
import "./Header.css";

export default function Header() {
  const { user, logout } = useAuth();

  return (
    <header className="app-header">
      <div className="app-header__brand">
        <span className="app-header__logo" aria-hidden="true" />
        <span>
          StreamPulse<span className="app-header__accent">.</span>
        </span>
      </div>
      <div className="app-header__user">
        <span className="app-header__name">{user?.full_name}</span>
        <button type="button" className="app-header__logout" onClick={logout}>
          Sign out
        </button>
      </div>
    </header>
  );
}
