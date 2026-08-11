import { useState, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'

import { extractErrorMessage } from '@/api/client'
import { Logo } from '@/components/layout/Logo'
import { useAuth } from '@/hooks/useAuth'

export function RegisterPage() {
  const { register } = useAuth()
  const navigate = useNavigate()
  const [fullName, setFullName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setError(null)
    setIsSubmitting(true)
    try {
      await register(email, password, fullName)
      navigate('/workspaces', { replace: true })
    } catch (err) {
      setError(extractErrorMessage(err, 'Could not create your account'))
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="mv-auth-shell">
      <div className="mv-panel" style={{ width: 400 }}>
        <div style={{ marginBottom: 22 }}>
          <Logo />
        </div>
        <h1 style={{ fontSize: 20, margin: '0 0 4px' }}>Create your account</h1>
        <p className="mv-muted" style={{ margin: '0 0 22px', fontSize: 13 }}>
          Start organizing your team&apos;s media
        </p>

        <form onSubmit={onSubmit}>
          <div className="mv-field">
            <label className="mv-label" htmlFor="full_name">
              Full name
            </label>
            <input
              id="full_name"
              className="mv-input"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              placeholder="Ava Martinez"
              required
              autoFocus
            />
          </div>
          <div className="mv-field">
            <label className="mv-label" htmlFor="email">
              Email
            </label>
            <input
              id="email"
              type="email"
              className="mv-input"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@studio.com"
              required
            />
          </div>
          <div className="mv-field">
            <label className="mv-label" htmlFor="password">
              Password
            </label>
            <input
              id="password"
              type="password"
              className="mv-input"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="At least 8 characters"
              minLength={8}
              required
            />
          </div>

          {error && <p className="mv-error-text" style={{ marginBottom: 12 }}>{error}</p>}

          <button className="mv-btn mv-btn-primary" style={{ width: '100%' }} disabled={isSubmitting}>
            {isSubmitting ? 'Creating account…' : 'Create account'}
          </button>
        </form>

        <p className="mv-muted" style={{ marginTop: 18, fontSize: 13, textAlign: 'center' }}>
          Already have an account? <Link to="/login">Sign in</Link>
        </p>
      </div>
    </div>
  )
}
