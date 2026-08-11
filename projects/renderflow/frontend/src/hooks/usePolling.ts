import { useCallback, useEffect, useRef, useState } from 'react'

interface PollingResult<T> {
  data: T | null
  error: string | null
  loading: boolean
  refresh: () => Promise<void>
}

/** Polls `fetcher` every `intervalMs`, keeping the ops UI near-real-time. */
export function usePolling<T>(
  fetcher: () => Promise<T>,
  intervalMs = 5000,
  enabled = true,
): PollingResult<T> {
  const [data, setData] = useState<T | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const fetcherRef = useRef(fetcher)

  useEffect(() => {
    fetcherRef.current = fetcher
  }, [fetcher])

  const refresh = useCallback(async () => {
    try {
      const result = await fetcherRef.current()
      setData(result)
      setError(null)
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Request failed')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    if (!enabled) return

    void refresh()
    const id = window.setInterval(() => void refresh(), intervalMs)
    return () => window.clearInterval(id)
  }, [refresh, intervalMs, enabled])

  return { data, error, loading, refresh }
}
