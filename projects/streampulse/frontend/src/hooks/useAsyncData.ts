import { useCallback, useEffect, useRef, useState } from "react";
import { ApiError } from "../api/client";

export interface AsyncState<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
  reload: () => void;
}

/**
 * Fetches data from `fetcher` whenever any value in `deps` changes, exposing
 * loading/error/data so every chart/panel can render a consistent
 * loading / error / empty / populated state.
 */
export function useAsyncData<T>(fetcher: () => Promise<T>, deps: unknown[]): AsyncState<T> {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const requestId = useRef(0);

  const load = useCallback(() => {
    const id = ++requestId.current;
    setLoading(true);
    setError(null);
    fetcher()
      .then((result) => {
        if (requestId.current === id) {
          setData(result);
          setLoading(false);
        }
      })
      .catch((err) => {
        if (requestId.current === id) {
          setError(err instanceof ApiError ? err.message : "Something went wrong. Please try again.");
          setLoading(false);
        }
      });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [load]);

  return { data, loading, error, reload: load };
}
