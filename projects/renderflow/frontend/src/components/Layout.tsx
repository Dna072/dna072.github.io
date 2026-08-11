import { NavLink, Outlet } from 'react-router-dom'

const NAV = [
  { to: '/', label: 'Dashboard', end: true },
  { to: '/jobs', label: 'Jobs' },
  { to: '/submit', label: 'Submit' },
  { to: '/failed', label: 'Failed' },
  { to: '/workers', label: 'Workers' },
]

export function Layout() {
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <span className="brand-mark" aria-hidden="true" />
          <div>
            <strong>RenderFlow</strong>
            <span className="brand-sub">Ops Console</span>
          </div>
        </div>
        <nav className="nav">
          {NAV.map(({ to, label, end }) => (
            <NavLink
              key={to}
              to={to}
              end={end}
              className={({ isActive }: { isActive: boolean }) =>
                isActive ? 'nav-link active' : 'nav-link'
              }
            >
              {label}
            </NavLink>
          ))}
        </nav>
        <footer className="sidebar-footer">
          <span className="pulse-dot" aria-hidden="true" />
          Live polling · 5s
        </footer>
      </aside>
      <main className="main">
        <Outlet />
      </main>
    </div>
  )
}
