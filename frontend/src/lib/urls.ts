/** Absolute API base when hosted separately (Render static); local Vite proxy keeps "/api/v1". */
export const API_BASE =
  (import.meta.env.VITE_API_URL as string | undefined)?.replace(/\/$/, "") || "/api/v1"

/** WebSocket URL for paths like `/ws/notifications/?token=...`. */
export function wsUrl(path: string): string {
  const api = import.meta.env.VITE_API_URL as string | undefined
  if (api) {
    const u = new URL(api)
    const proto = u.protocol === "https:" ? "wss:" : "ws:"
    return `${proto}//${u.host}${path.startsWith("/") ? path : `/${path}`}`
  }
  const proto = window.location.protocol === "https:" ? "wss:" : "ws:"
  return `${proto}//${window.location.host}${path.startsWith("/") ? path : `/${path}`}`
}
