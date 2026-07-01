/**
 * useApiData — production-grade React hook for fetching from the AuditCore API.
 *
 * Features:
 * - Auto-fetch on mount + when dependencies change
 * - Cached result for `staleTime` ms (default 30s)
 * - Manual refetch + invalidate
 * - Loading / error / success states
 * - AbortController on unmount or dependency change
 * - Bilingual-friendly: errors are ApiError instances with `request_id`
 *
 * Usage:
 *   const { data, error, isLoading, refetch } = useApiData(
 *     () => api.owner.trustIndex(companyId),
 *     [companyId],
 *     { staleTime: 60_000 }
 *   );
 */

import { useCallback, useEffect, useRef, useState } from "react";
import { ApiError } from "@/lib/api-client";

export interface UseApiDataOptions<T> {
  /** Re-fetch window in milliseconds. Default 30s. */
  staleTime?: number;
  /** Skip the initial fetch (e.g. when deps not yet ready). */
  enabled?: boolean;
  /** Called when fetch succeeds. */
  onSuccess?: (data: T) => void;
  /** Called when fetch fails. */
  onError?: (error: ApiError | Error) => void;
}

export interface UseApiDataResult<T> {
  data: T | null;
  error: ApiError | Error | null;
  isLoading: boolean;
  isFetching: boolean;
  isStale: boolean;
  refetch: () => Promise<void>;
  invalidate: () => void;
  requestId: string | null;
}

const DEFAULT_STALE_TIME = 30_000;

export function useApiData<T>(
  fetcher: () => Promise<T>,
  deps: ReadonlyArray<unknown>,
  options: UseApiDataOptions<T> = {},
): UseApiDataResult<T> {
  const { staleTime = DEFAULT_STALE_TIME, enabled = true, onSuccess, onError } = options;

  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<ApiError | Error | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [isStale, setIsStale] = useState<boolean>(false);
  const [requestId, setRequestId] = useState<string | null>(null);
  const lastFetchedAt = useRef<number | null>(null);
  const abortRef = useRef<AbortController | null>(null);
  const mountedRef = useRef<boolean>(true);
  const fetcherRef = useRef(fetcher);
  fetcherRef.current = fetcher;

  const invalidate = useCallback(() => {
    lastFetchedAt.current = null;
    setIsStale(true);
  }, []);

  const doFetch = useCallback(async () => {
    if (!enabled) return;
    abortRef.current?.abort();
    const ac = new AbortController();
    abortRef.current = ac;
    setIsLoading(true);
    setError(null);
    setRequestId(null);
    try {
      const result = await fetcherRef.current();
      if (!mountedRef.current || ac.signal.aborted) return;
      // Capture the latest request_id from any in-flight ApiError responses
      // (the api-client sets it via X-Request-ID)
      setData(result);
      lastFetchedAt.current = Date.now();
      setIsStale(false);
      onSuccess?.(result);
    } catch (err) {
      if (!mountedRef.current || ac.signal.aborted) return;
      const e = err instanceof ApiError ? err : err instanceof Error ? err : new Error(String(err));
      setError(e);
      if (e instanceof ApiError) setRequestId(e.request_id);
      onError?.(e);
    } finally {
      if (mountedRef.current) setIsLoading(false);
    }
  }, [enabled, onSuccess, onError]);

  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => {
    if (!enabled) {
      setIsLoading(false);
      return;
    }
    // Skip fetch if data is still fresh
    const age = lastFetchedAt.current ? Date.now() - lastFetchedAt.current : Infinity;
    if (age < staleTime && data !== null) {
      return;
    }
    doFetch();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [enabled, ...deps, staleTime]);

  // Stale-time refresh — runs every staleTime/3 ms to refresh in background
  useEffect(() => {
    if (!enabled || staleTime === Infinity) return;
    const interval = setInterval(
      () => {
        const age = lastFetchedAt.current ? Date.now() - lastFetchedAt.current : Infinity;
        if (age >= staleTime) {
          doFetch();
        }
      },
      Math.max(staleTime / 3, 5_000),
    );
    return () => clearInterval(interval);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [enabled, staleTime, ...deps]);

  // Cleanup on unmount
  useEffect(() => {
    mountedRef.current = true;
    return () => {
      mountedRef.current = false;
      abortRef.current?.abort();
    };
  }, []);

  const refetch = useCallback(async () => {
    lastFetchedAt.current = null;
    await doFetch();
  }, [doFetch]);

  return {
    data,
    error,
    isLoading,
    isFetching: isLoading,
    isStale,
    refetch,
    invalidate,
    requestId,
  };
}
