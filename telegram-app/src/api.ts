const API_BASE =
  (import.meta.env.VITE_API_URL as string | undefined)?.replace(/\/$/, "") || "/api/v1"
const STORAGE_KEY = "maktabiq-tg-tokens"

interface Tokens {
  access: string
  refresh: string
}

let tokens: Tokens | null = null
try {
  const raw = sessionStorage.getItem(STORAGE_KEY)
  if (raw) tokens = JSON.parse(raw) as Tokens
} catch {
  /* storage unavailable (private mode etc.) — just start signed out */
}

function persist() {
  try {
    if (tokens) sessionStorage.setItem(STORAGE_KEY, JSON.stringify(tokens))
    else sessionStorage.removeItem(STORAGE_KEY)
  } catch {
    /* ignore */
  }
}

export function setTokens(access: string, refresh: string) {
  tokens = { access, refresh }
  persist()
}

export function clearTokens() {
  tokens = null
  persist()
}

export function hasSession(): boolean {
  return !!tokens
}

export class ApiError extends Error {
  status: number
  body: unknown
  constructor(message: string, status: number, body: unknown) {
    super(message)
    this.status = status
    this.body = body
  }
}

let refreshing: Promise<boolean> | null = null

async function refreshAccessToken(): Promise<boolean> {
  if (!tokens) return false
  try {
    const res = await fetch(`${API_BASE}/auth/refresh/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh: tokens.refresh }),
    })
    if (!res.ok) {
      clearTokens()
      return false
    }
    const data = await res.json()
    tokens = { access: data.access, refresh: data.refresh ?? tokens.refresh }
    persist()
    return true
  } catch {
    return false
  }
}

async function request<T>(path: string, init: RequestInit = {}, retried = false): Promise<T> {
  const headers = new Headers(init.headers)
  if (init.body) headers.set("Content-Type", "application/json")
  if (tokens) headers.set("Authorization", `Bearer ${tokens.access}`)

  const res = await fetch(`${API_BASE}${path}`, { ...init, headers })

  if (res.status === 401 && tokens && !retried) {
    refreshing ??= refreshAccessToken().finally(() => {
      refreshing = null
    })
    if (await refreshing) return request<T>(path, init, true)
  }

  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    const message =
      (body as { message?: string; detail?: string }).message ??
      (body as { message?: string; detail?: string }).detail ??
      `HTTP ${res.status}`
    throw new ApiError(message, res.status, body)
  }
  if (res.status === 204) return undefined as T
  return (await res.json()) as T
}

export const api = {
  get: <T>(path: string) => request<T>(path),
  post: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: "POST", body: body !== undefined ? JSON.stringify(body) : undefined }),
}
