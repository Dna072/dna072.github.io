import { useQuery } from '@tanstack/react-query'
import { Link, useLocation, useNavigate } from 'react-router-dom'

import { listTags } from '@/api/tags'
import { Avatar } from '@/components/common/Avatar'
import { FolderTree } from '@/components/folders/FolderTree'
import { Logo } from '@/components/layout/Logo'
import { useAuth } from '@/hooks/useAuth'
import { canAdminister, canWrite } from '@/lib/rbac'
import type { Workspace } from '@/types'

interface SidebarProps {
  workspace: Workspace
}

export function Sidebar({ workspace }: SidebarProps) {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const searchParams = new URLSearchParams(location.search)

  const tagsQuery = useQuery({
    queryKey: ['tags', workspace.id],
    queryFn: () => listTags(workspace.id),
  })

  const isLibraryRoot =
    location.pathname === `/w/${workspace.id}/library` &&
    !searchParams.get('folder') &&
    !searchParams.get('tag')
  const activeTag = searchParams.get('tag')

  const handleLogout = async () => {
    await logout()
    navigate('/login')
  }

  return (
    <aside
      style={{
        borderRight: '1px solid var(--mv-border)',
        background: 'var(--mv-surface)',
        display: 'flex',
        flexDirection: 'column',
        height: '100vh',
        position: 'sticky',
        top: 0,
      }}
    >
      <div style={{ padding: '18px 18px 14px' }}>
        <Logo />
      </div>

      <div style={{ padding: '0 18px 14px' }}>
        <Link
          to="/workspaces"
          className="mv-card"
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '9px 12px',
            fontSize: 13,
            fontWeight: 600,
            color: 'var(--mv-text)',
          }}
        >
          <span className="mv-truncate">{workspace.name}</span>
          <span className="mv-faint" style={{ fontSize: 11 }}>
            Switch
          </span>
        </Link>
      </div>

      <nav style={{ flex: 1, overflowY: 'auto', padding: '0 12px' }}>
        <Link
          to={`/w/${workspace.id}/library`}
          className="mv-sidebar-link"
          style={{
            display: 'block',
            padding: '8px 12px',
            borderRadius: 8,
            fontWeight: isLibraryRoot ? 700 : 600,
            background: isLibraryRoot ? 'var(--mv-accent-100)' : 'transparent',
            color: isLibraryRoot ? 'var(--mv-accent-900)' : 'var(--mv-text)',
            marginBottom: 14,
          }}
        >
          All assets
        </Link>

        <div style={{ marginBottom: 18 }}>
          <div
            className="mv-flex mv-items-center mv-justify-between"
            style={{ padding: '0 12px 6px' }}
          >
            <span
              style={{
                fontSize: 11,
                fontWeight: 700,
                textTransform: 'uppercase',
                letterSpacing: '0.04em',
                color: 'var(--mv-text-faint)',
              }}
            >
              Folders
            </span>
          </div>
          <FolderTree workspaceId={workspace.id} />
        </div>

        <div style={{ marginBottom: 18 }}>
          <div style={{ padding: '0 12px 6px' }}>
            <span
              style={{
                fontSize: 11,
                fontWeight: 700,
                textTransform: 'uppercase',
                letterSpacing: '0.04em',
                color: 'var(--mv-text-faint)',
              }}
            >
              Tags
            </span>
          </div>
          <div className="mv-flex-col mv-gap-1">
            {tagsQuery.data?.length ? (
              tagsQuery.data.map((tag) => (
                <Link
                  key={tag.id}
                  to={`/w/${workspace.id}/library?tag=${encodeURIComponent(tag.name)}`}
                  className="mv-flex mv-items-center mv-gap-2 mv-truncate"
                  style={{
                    padding: '6px 12px',
                    borderRadius: 8,
                    fontSize: 13,
                    background: activeTag === tag.name ? 'var(--mv-accent-100)' : 'transparent',
                    color: activeTag === tag.name ? 'var(--mv-accent-900)' : 'var(--mv-text-muted)',
                    fontWeight: activeTag === tag.name ? 700 : 500,
                  }}
                >
                  <span className="mv-tag-dot" style={{ background: tag.color }} />
                  <span className="mv-truncate">{tag.name}</span>
                </Link>
              ))
            ) : (
              <p className="mv-faint" style={{ fontSize: 12, padding: '0 12px' }}>
                No tags yet.
              </p>
            )}
          </div>
        </div>

        {canAdminister(workspace.my_role) && (
          <Link
            to={`/w/${workspace.id}/settings`}
            className="mv-flex mv-items-center mv-gap-2"
            style={{
              padding: '8px 12px',
              borderRadius: 8,
              fontSize: 13,
              fontWeight: 600,
              color:
                location.pathname === `/w/${workspace.id}/settings`
                  ? 'var(--mv-accent-900)'
                  : 'var(--mv-text-muted)',
              background:
                location.pathname === `/w/${workspace.id}/settings`
                  ? 'var(--mv-accent-100)'
                  : 'transparent',
            }}
          >
            Members & permissions
          </Link>
        )}
      </nav>

      <div
        style={{
          borderTop: '1px solid var(--mv-border)',
          padding: 14,
          display: 'flex',
          alignItems: 'center',
          gap: 10,
        }}
      >
        <Avatar name={user?.full_name ?? '?'} />
        <div style={{ flex: 1, minWidth: 0 }}>
          <div className="mv-truncate" style={{ fontSize: 13, fontWeight: 600 }}>
            {user?.full_name}
          </div>
          <div className="mv-truncate mv-faint" style={{ fontSize: 11 }}>
            {canWrite(workspace.my_role) ? 'You can upload & edit' : 'View only'}
          </div>
        </div>
        <button className="mv-btn mv-btn-ghost mv-btn-sm" onClick={handleLogout}>
          Log out
        </button>
      </div>
    </aside>
  )
}
