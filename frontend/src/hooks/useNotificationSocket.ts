import { useEffect, useRef } from "react"
import toast from "react-hot-toast"
import { useAuthStore } from "../store/auth"
import { useNotificationStore } from "../store/notifications"
import type { Notification } from "../types"
import { NOTIFICATION_ICON_LABEL } from "../lib/format"

export function useNotificationSocket() {
  const accessToken = useAuthStore((s) => s.accessToken)
  const prepend = useNotificationStore((s) => s.prepend)
  const socketRef = useRef<WebSocket | null>(null)

  useEffect(() => {
    if (!accessToken) return

    let cancelled = false
    let retryDelay = 1500

    function connect() {
      if (cancelled) return
      const protocol = window.location.protocol === "https:" ? "wss" : "ws"
      const socket = new WebSocket(`${protocol}://${window.location.host}/ws/notifications/?token=${accessToken}`)
      socketRef.current = socket

      socket.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data) as Notification
          prepend(data)
          toast(data.title, {
            icon: "🔔",
            style: { borderRadius: "12px" },
          })
        } catch {
          /* ignore malformed payloads */
        }
      }

      socket.onclose = () => {
        if (cancelled) return
        setTimeout(connect, retryDelay)
        retryDelay = Math.min(retryDelay * 1.5, 15000)
      }
    }

    connect()
    return () => {
      cancelled = true
      socketRef.current?.close()
    }
  }, [accessToken, prepend])
}

export function labelFor(type: Notification["type"]) {
  return NOTIFICATION_ICON_LABEL[type] ?? type
}
