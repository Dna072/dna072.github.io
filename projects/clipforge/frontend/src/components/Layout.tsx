import { NavLink, Outlet } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const NAV = [
  { to: '/', label: 'Dashboard', icon: '◱', end: true },
  { to: '/library', label: 'Library', icon: '▤', end: false },
  { to: '/upload', label: 'Upload', icon: '↑', end: false },
];

export function Layout() {
  const { user, logout } = useAuth();
  const initials = (user?.full_name || user?.email || '?')
    .split(' ')
    .map((p) => p[0])
    .slice(0, 2)
    .join('')
    .toUpperCase();

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand__mark">◆</div>
          Clip<span>Forge</span>
        </div>

        <nav className="nav-links">
          {NAV.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className={({ isActive }) => `nav-link${isActive ? ' active' : ''}`}
            >
              <span className="nav-icon">{item.icon}</span>
              {item.label}
            </NavLink>
          ))}
        </nav>

        <div className="sidebar__footer">
          <div className="user-chip">
            <div className="avatar">{initials}</div>
            <div style={{ overflow: 'hidden' }}>
              <div style={{ fontSize: '0.85rem', fontWeight: 600 }}>
                {user?.full_name}
              </div>
              <div
                style={{
                  fontSize: '0.72rem',
                  color: 'var(--text-dim)',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  whiteSpace: 'nowrap',
                }}
              >
                {user?.email}
              </div>
            </div>
          </div>
          <button className="btn btn-ghost" style={{ width: '100%' }} onClick={logout}>
            Sign out
          </button>
        </div>
      </aside>

      <main className="main">
        <Outlet />
      </main>
    </div>
  );
}
