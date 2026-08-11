import { NavLink, Outlet, useNavigate } from 'react-router-dom';

import { useAuth } from '@/context/AuthContext';

const NAV = [
  { to: '/dashboard', label: 'Dashboard', icon: '▤' },
  { to: '/library', label: 'Library', icon: '▦' },
  { to: '/upload', label: 'Upload', icon: '↑' },
];

export function Layout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <span className="brand-mark">▶</span>
          ClipForge
        </div>
        {NAV.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
          >
            <span className="icon">{item.icon}</span>
            {item.label}
          </NavLink>
        ))}
        <div className="sidebar-footer">
          <div style={{ padding: '4px 8px', marginBottom: 8 }}>
            <div style={{ fontWeight: 600, fontSize: 14 }}>{user?.full_name}</div>
            <div className="muted" style={{ fontSize: 12 }}>
              {user?.email}
            </div>
          </div>
          <button className="btn btn-ghost btn-sm btn-block" onClick={handleLogout}>
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
