import type { ReactNode } from 'react'
import { createPortal } from 'react-dom'

export function Drawer({ onClose, children }: { onClose: () => void; children: ReactNode }) {
  return createPortal(
    <div
      style={{
        position: 'fixed',
        inset: 0,
        background: 'rgba(10, 38, 32, 0.4)',
        zIndex: 800,
        display: 'flex',
        justifyContent: 'flex-end',
      }}
      onMouseDown={(e) => {
        if (e.target === e.currentTarget) onClose()
      }}
    >
      <div
        className="mv-card"
        style={{
          width: 420,
          maxWidth: '100%',
          height: '100vh',
          borderRadius: 0,
          overflowY: 'auto',
          boxShadow: 'var(--mv-shadow-lg)',
        }}
      >
        {children}
      </div>
    </div>,
    document.body,
  )
}
