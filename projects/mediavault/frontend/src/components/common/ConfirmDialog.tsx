import { Modal } from '@/components/common/Modal'

interface ConfirmDialogProps {
  title: string
  message: string
  confirmLabel?: string
  danger?: boolean
  onConfirm: () => void
  onCancel: () => void
  isLoading?: boolean
}

export function ConfirmDialog({
  title,
  message,
  confirmLabel = 'Confirm',
  danger,
  onConfirm,
  onCancel,
  isLoading,
}: ConfirmDialogProps) {
  return (
    <Modal
      title={title}
      onClose={onCancel}
      width={400}
      footer={
        <>
          <button className="mv-btn mv-btn-secondary" onClick={onCancel} disabled={isLoading}>
            Cancel
          </button>
          <button
            className={`mv-btn ${danger ? 'mv-btn-danger' : 'mv-btn-primary'}`}
            onClick={onConfirm}
            disabled={isLoading}
          >
            {isLoading ? 'Working…' : confirmLabel}
          </button>
        </>
      }
    >
      <p style={{ margin: 0, color: 'var(--mv-text-muted)' }}>{message}</p>
    </Modal>
  )
}
