import { useCallback, useEffect, useRef, useState } from "react"
import { api, getErrorMessage } from "../lib/api"

interface UseFetchState<T> {
  data: T | null
  loading: boolean
  error: string | null
}

export function useFetch<T>(url: string | null, deps: unknown[] = []) {
  const [state, setState] = useState<UseFetchState<T>>({ data: null, loading: !!url, error: null })
  const requestId = useRef(0)

  const fetchData = useCallback(async () => {
    if (!url) return
    const id = ++requestId.current
    setState((s) => ({ ...s, loading: true, error: null }))
    try {
      const res = await api.get<T>(url)
      if (id === requestId.current) {
        setState({ data: res.data, loading: false, error: null })
      }
    } catch (err) {
      if (id === requestId.current) {
        setState({ data: null, loading: false, error: getErrorMessage(err, "Ma'lumotlarni yuklab bo'lmadi") })
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [url])

  useEffect(() => {
    fetchData()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [url, ...deps])

  return { ...state, refetch: fetchData }
}
