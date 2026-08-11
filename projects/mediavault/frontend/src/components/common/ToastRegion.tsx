import { useToast } from '@/hooks/useToast'

export function ToastRegion() {
  const { toasts, dismissToast } = useToast()

  if (toasts.length === 0) return null

  return (
    <div className="mv-toast-region">
      {toasts.map((toast) => (
        <div
          key={toast.id}
          className={`mv-toast ${toast.variant === 'error' ? 'mv-toast-error' : ''}`}
          onClick={() => dismissToast(toast.id)}
          role="status"
        >
          {toast.message}
        </div>
      ))}
    </div>
  )
}
