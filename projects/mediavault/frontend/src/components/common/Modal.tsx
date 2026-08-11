import { useEffect, type ReactNode } from 'react'
import { createPortal } from 'react-dom'

interface ModalProps {
  title: string
  onClose: () => void
  children: ReactNode
  footer?: ReactNode
  width?: number
}

export function Modal({ title, onClose, children, footer, width = 480 }: ModalProps) {
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [onClose])

  return createPortal(
    <div
      style={{
        position: 'fixed',
        inset: 0,
        background: 'rgba(10, 38, 32, 0.45)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 900,
        padding: 20,
      }}
      onMouseDown={(e) => {
        if (e.target === e.currentTarget) onClose()
      }}
    >
      <div
        className="mv-card"
        style={{
          width,
          maxWidth: '100%',
          maxHeight: '88vh',
          display: 'flex',
          flexDirection: 'column',
          boxShadow: 'var(--mv-shadow-lg)',
        }}
      >
        <div
          className="mv-flex mv-items-center mv-justify-between"
          style={{ padding: '16px 20px', borderBottom: '1px solid var(--mv-border)' }}
        >
          <h2 style={{ fontSize: 15, margin: 0, fontWeight: 700 }}>{title}</h2>
          <button className="mv-btn mv-btn-ghost mv-btn-icon" onClick={onClose} aria-label="Close">
            ✕
          </button>
        </div>
        <div style={{ padding: 20, overflowY: 'auto', flex: 1 }}>{children}</div>
        {footer && (
          <div
            style={{
              padding: '14px 20px',
              borderTop: '1px solid var(--mv-border)',
              display: 'flex',
              justifyContent: 'flex-end',
              gap: 8,
            }}
          >
            {footer}
          </div>
        )}
      </div>
    </div>,
    document.body,
  )
}
