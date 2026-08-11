import { createContext, useCallback, useMemo, useState, type ReactNode } from 'react'

export interface ToastItem {
  id: number
  message: string
  variant: 'info' | 'error' | 'success'
}

interface ToastContextValue {
  toasts: ToastItem[]
  showToast: (message: string, variant?: ToastItem['variant']) => void
  dismissToast: (id: number) => void
}

// eslint-disable-next-line react-refresh/only-export-components
export const ToastContext = createContext<ToastContextValue | undefined>(undefined)

let nextId = 1

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<ToastItem[]>([])

  const dismissToast = useCallback((id: number) => {
    setToasts((prev) => prev.filter((t) => t.id !== id))
  }, [])

  const showToast = useCallback(
    (message: string, variant: ToastItem['variant'] = 'info') => {
      const id = nextId++
      setToasts((prev) => [...prev, { id, message, variant }])
      window.setTimeout(() => dismissToast(id), 4500)
    },
    [dismissToast],
  )

  const value = useMemo(() => ({ toasts, showToast, dismissToast }), [toasts, showToast, dismissToast])

  return <ToastContext.Provider value={value}>{children}</ToastContext.Provider>
}
