import axios, { type AxiosError, type InternalAxiosRequestConfig } from 'axios'

import type { TokenPair } from '@/types'

export const API_BASE_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8001'
export const API_V1 = `${API_BASE_URL}/api/v1`

const ACCESS_TOKEN_KEY = 'mediavault.access_token'
const REFRESH_TOKEN_KEY = 'mediavault.refresh_token'

export const tokenStorage = {
  getAccess: () => localStorage.getItem(ACCESS_TOKEN_KEY),
  getRefresh: () => localStorage.getItem(REFRESH_TOKEN_KEY),
  set: (tokens: TokenPair) => {
    localStorage.setItem(ACCESS_TOKEN_KEY, tokens.access_token)
    localStorage.setItem(REFRESH_TOKEN_KEY, tokens.refresh_token)
  },
  clear: () => {
    localStorage.removeItem(ACCESS_TOKEN_KEY)
    localStorage.removeItem(REFRESH_TOKEN_KEY)
  },
}

export const apiClient = axios.create({ baseURL: API_V1 })

apiClient.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = tokenStorage.getAccess()
  if (token) {
    config.headers.set('Authorization', `Bearer ${token}`)
  }
  return config
})

let refreshPromise: Promise<string | null> | null = null

async function refreshAccessToken(): Promise<string | null> {
  const refreshToken = tokenStorage.getRefresh()
  if (!refreshToken) return null
  try {
    const response = await axios.post<TokenPair>(`${API_V1}/auth/refresh`, {
      refresh_token: refreshToken,
    })
    tokenStorage.set(response.data)
    return response.data.access_token
  } catch {
    tokenStorage.clear()
    return null
  }
}

apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const original = error.config as (InternalAxiosRequestConfig & { _retried?: boolean }) | undefined
    const status = error.response?.status
    const isAuthEndpoint = original?.url?.includes('/auth/')

    if (status === 401 && original && !original._retried && !isAuthEndpoint) {
      original._retried = true
      refreshPromise ??= refreshAccessToken().finally(() => {
        refreshPromise = null
      })
      const newToken = await refreshPromise
      if (newToken) {
        original.headers.set('Authorization', `Bearer ${newToken}`)
        return apiClient(original)
      }
      tokenStorage.clear()
      window.dispatchEvent(new CustomEvent('mediavault:unauthorized'))
    }
    return Promise.reject(error)
  },
)

export function extractErrorMessage(error: unknown, fallback = 'Something went wrong'): string {
  if (axios.isAxiosError(error)) {
    const data = error.response?.data as { detail?: unknown } | undefined
    const detail = data?.detail
    if (typeof detail === 'string') return detail
    if (Array.isArray(detail)) {
      return detail
        .map((item) => (typeof item === 'string' ? item : item?.msg))
        .filter(Boolean)
        .join('; ') || fallback
    }
  }
  return fallback
}
