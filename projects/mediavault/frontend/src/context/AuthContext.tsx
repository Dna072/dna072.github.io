import { createContext, useCallback, useEffect, useMemo, useState, type ReactNode } from 'react'

import { fetchMe, login as loginApi, logout as logoutApi, register as registerApi } from '@/api/auth'
import { tokenStorage } from '@/api/client'
import type { User } from '@/types'

interface AuthContextValue {
  user: User | null
  isLoading: boolean
  isAuthenticated: boolean
  login: (email: string, password: string) => Promise<void>
  register: (email: string, password: string, fullName: string) => Promise<void>
  logout: () => Promise<void>
}

// eslint-disable-next-line react-refresh/only-export-components
export const AuthContext = createContext<AuthContextValue | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  const hydrate = useCallback(async () => {
    const token = tokenStorage.getAccess()
    if (!token) {
      setIsLoading(false)
      return
    }
    try {
      const me = await fetchMe()
      setUser(me)
    } catch {
      tokenStorage.clear()
      setUser(null)
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    void hydrate()
    const onUnauthorized = () => setUser(null)
    window.addEventListener('mediavault:unauthorized', onUnauthorized)
    return () => window.removeEventListener('mediavault:unauthorized', onUnauthorized)
  }, [hydrate])

  const login = useCallback(async (email: string, password: string) => {
    const response = await loginApi({ email, password })
    tokenStorage.set(response)
    setUser(response.user)
  }, [])

  const register = useCallback(async (email: string, password: string, fullName: string) => {
    const response = await registerApi({ email, password, full_name: fullName })
    tokenStorage.set(response)
    setUser(response.user)
  }, [])

  const logout = useCallback(async () => {
    const refreshToken = tokenStorage.getRefresh()
    if (refreshToken) {
      try {
        await logoutApi(refreshToken)
      } catch {
        // Best-effort server-side revocation; always clear client state.
      }
    }
    tokenStorage.clear()
    setUser(null)
  }, [])

  const value = useMemo<AuthContextValue>(
    () => ({ user, isLoading, isAuthenticated: user !== null, login, register, logout }),
    [user, isLoading, login, register, logout],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
