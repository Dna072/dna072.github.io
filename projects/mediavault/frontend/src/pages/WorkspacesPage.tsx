import { useState, type FormEvent } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'

import { createWorkspace, listWorkspaces } from '@/api/workspaces'
import { extractErrorMessage } from '@/api/client'
import { Logo } from '@/components/layout/Logo'
import { RoleBadge } from '@/components/common/RoleBadge'
import { useAuth } from '@/hooks/useAuth'

function slugify(value: string): string {
  return value
    .toLowerCase()
    .trim()
    .replace(/[^a-z0-9\s-]/g, '')
    .replace(/\s+/g, '-')
    .replace(/-+/g, '-')
}

export function WorkspacesPage() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [name, setName] = useState('')
  const [showCreate, setShowCreate] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const { data: workspaces, isLoading } = useQuery({
    queryKey: ['workspaces'],
    queryFn: listWorkspaces,
  })

  const createMutation = useMutation({
    mutationFn: () => createWorkspace({ name, slug: slugify(name) }),
    onSuccess: (workspace) => {
      queryClient.invalidateQueries({ queryKey: ['workspaces'] })
      navigate(`/w/${workspace.id}/library`)
    },
    onError: (err) => setError(extractErrorMessage(err, 'Could not create workspace')),
  })

  const onSubmit = (e: FormEvent) => {
    e.preventDefault()
    setError(null)
    if (name.trim().length === 0) return
    createMutation.mutate()
  }

  const handleLogout = async () => {
    await logout()
    navigate('/login')
  }

  return (
    <div style={{ maxWidth: 760, margin: '0 auto', padding: '48px 24px' }}>
      <div className="mv-flex mv-items-center mv-justify-between" style={{ marginBottom: 32 }}>
        <Logo />
        <div className="mv-flex mv-items-center mv-gap-3">
          <span className="mv-muted" style={{ fontSize: 13 }}>
            {user?.full_name}
          </span>
          <button className="mv-btn mv-btn-ghost mv-btn-sm" onClick={handleLogout}>
            Log out
          </button>
        </div>
      </div>

      <div className="mv-flex mv-items-center mv-justify-between" style={{ marginBottom: 16 }}>
        <h1 style={{ fontSize: 20, margin: 0 }}>Your workspaces</h1>
        <button className="mv-btn mv-btn-primary" onClick={() => setShowCreate((v) => !v)}>
          {showCreate ? 'Cancel' : '+ New workspace'}
        </button>
      </div>

      {showCreate && (
        <form onSubmit={onSubmit} className="mv-card" style={{ padding: 18, marginBottom: 24 }}>
          <div className="mv-field" style={{ marginBottom: 12 }}>
            <label className="mv-label" htmlFor="ws-name">
              Workspace name
            </label>
            <input
              id="ws-name"
              className="mv-input"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Acme Creative Studio"
              autoFocus
              required
            />
            {name && <span className="mv-hint">Slug: {slugify(name) || '—'}</span>}
          </div>
          {error && <p className="mv-error-text" style={{ marginBottom: 12 }}>{error}</p>}
          <button className="mv-btn mv-btn-primary" disabled={createMutation.isPending}>
            {createMutation.isPending ? 'Creating…' : 'Create workspace'}
          </button>
        </form>
      )}

      {isLoading && <div className="mv-spinner" />}

      {!isLoading && workspaces?.length === 0 && (
        <div className="mv-empty-state mv-card">
          <h3>No workspaces yet</h3>
          <p>Create your first workspace to start uploading media.</p>
        </div>
      )}

      <div className="mv-flex-col mv-gap-3">
        {workspaces?.map((workspace) => (
          <button
            key={workspace.id}
            onClick={() => navigate(`/w/${workspace.id}/library`)}
            className="mv-card"
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              padding: '16px 20px',
              textAlign: 'left',
              cursor: 'pointer',
              border: '1px solid var(--mv-border)',
            }}
          >
            <div>
              <div style={{ fontWeight: 700, fontSize: 15 }}>{workspace.name}</div>
              <div className="mv-muted" style={{ fontSize: 12 }}>
                {workspace.member_count} member{workspace.member_count === 1 ? '' : 's'} ·{' '}
                {workspace.asset_count} asset{workspace.asset_count === 1 ? '' : 's'}
              </div>
            </div>
            {workspace.my_role && <RoleBadge role={workspace.my_role} />}
          </button>
        ))}
      </div>
    </div>
  )
}
