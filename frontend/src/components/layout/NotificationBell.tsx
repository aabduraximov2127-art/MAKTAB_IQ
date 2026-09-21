import { useEffect, useRef, useState } from "react"
import { AnimatePresence, motion } from "framer-motion"
import { Bell, CheckCheck } from "lucide-react"
import { Link } from "react-router-dom"
import { api } from "../../lib/api"
import { useNotificationStore } from "../../store/notifications"
import { formatRelative } from "../../lib/format"
import { labelFor } from "../../hooks/useNotificationSocket"
import { EmptyState } from "../ui/EmptyState"

export function NotificationBell() {
  const [open, setOpen] = useState(false)
  const ref = useRef<HTMLDivElement>(null)
  const { items, unread, setAll, markAllRead } = useNotificationStore()

  useEffect(() => {
    api
      .get("/notifications/?page_size=8")
      .then((res) => setAll(res.data.results))
      .catch(() => {})
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  useEffect(() => {
    function onClick(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false)
    }
    document.addEventListener("mousedown", onClick)
    return () => document.removeEventListener("mousedown", onClick)
  }, [])

  async function handleMarkAll() {
    markAllRead()
    try {
      await api.post("/notifications/mark_all_read/")
    } catch {
      /* optimistic — ignore */
    }
  }

  return (
    <div className="relative" ref={ref}>
      <button
        onClick={() => setOpen((v) => !v)}
        className="relative flex h-10 w-10 items-center justify-center rounded-xl text-ink-500 transition-colors hover:bg-ink-100 dark:text-ink-400 dark:hover:bg-ink-800"
      >
        <Bell className="h-5 w-5" />
        {unread > 0 && (
          <span className="absolute right-1.5 top-1.5 flex h-4 min-w-4 items-center justify-center rounded-full bg-rose-500 px-1 text-[10px] font-bold text-white">
            {unread > 9 ? "9+" : unread}
          </span>
        )}
      </button>

      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ opacity: 0, y: -8, scale: 0.97 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -8, scale: 0.97 }}
            transition={{ duration: 0.15 }}
            className="absolute right-0 z-30 mt-2 w-80 overflow-hidden rounded-2xl border border-ink-100 bg-white shadow-soft-lg dark:border-ink-800 dark:bg-ink-900"
          >
            <div className="flex items-center justify-between border-b border-ink-100 px-4 py-3 dark:border-ink-800">
              <p className="font-display text-sm font-semibold text-ink-800 dark:text-white">Bildirishnomalar</p>
              {unread > 0 && (
                <button
                  onClick={handleMarkAll}
                  className="flex items-center gap-1 text-xs font-medium text-brand-600 hover:text-brand-700 dark:text-brand-400"
                >
                  <CheckCheck className="h-3.5 w-3.5" /> Hammasini o'qish
                </button>
              )}
            </div>
            <div className="max-h-96 overflow-y-auto">
              {items.length === 0 ? (
                <div className="p-4">
                  <EmptyState title="Bildirishnoma yo'q" />
                </div>
              ) : (
                items.map((n) => (
                  <div
                    key={n.id}
                    className={`border-b border-ink-50 px-4 py-3 last:border-0 dark:border-ink-800/60 ${
                      !n.is_read ? "bg-brand-50/50 dark:bg-brand-500/5" : ""
                    }`}
                  >
                    <div className="flex items-start justify-between gap-2">
                      <p className="text-xs font-semibold text-brand-600 dark:text-brand-400">{labelFor(n.type)}</p>
                      {!n.is_read && <span className="mt-1 h-1.5 w-1.5 shrink-0 rounded-full bg-brand-500" />}
                    </div>
                    <p className="mt-0.5 text-sm font-medium text-ink-800 dark:text-ink-100">{n.title}</p>
                    <p className="mt-0.5 line-clamp-2 text-xs text-ink-500 dark:text-ink-400">{n.message}</p>
                    <p className="mt-1 text-[11px] text-ink-400">{formatRelative(n.created_at)}</p>
                  </div>
                ))
              )}
            </div>
            <Link
              to="/notifications"
              onClick={() => setOpen(false)}
              className="block border-t border-ink-100 px-4 py-2.5 text-center text-sm font-medium text-brand-600 hover:bg-ink-50 dark:border-ink-800 dark:text-brand-400 dark:hover:bg-ink-800/60"
            >
              Barchasini ko'rish
            </Link>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
