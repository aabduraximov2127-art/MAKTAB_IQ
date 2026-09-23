import { useEffect, useState } from "react"
import { api } from "./api"

/** Minimal `fetch on mount` hook — no cache/refetch machinery, this app's screens are
 * simple enough not to need it. `path === null` skips fetching (e.g. while a prerequisite
 * id isn't known yet). */
export function useApi<T>(path: string | null) {
  const [data, setData] = useState<T | null>(null)
  const [loading, setLoading] = useState(path !== null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (path === null) {
      setData(null)
      setLoading(false)
      return
    }
    let cancelled = false
    setLoading(true)
    setError(null)
    api
      .get<T>(path)
      .then((result) => {
        if (!cancelled) setData(result)
      })
      .catch((err: unknown) => {
        if (!cancelled) setError(err instanceof Error ? err.message : "Xatolik")
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [path])

  return { data, loading, error }
}
