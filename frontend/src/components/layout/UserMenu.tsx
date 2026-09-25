import { useEffect, useRef, useState } from "react"
import { AnimatePresence, motion } from "framer-motion"
import { ChevronDown, Settings, User as UserIcon } from "lucide-react"
import { Link } from "react-router-dom"
import { useAuthStore } from "../../store/auth"
import { SignOutIcon } from "./SignOutIcon"
import { fullName, initials, roleLabels } from "../../lib/format"

export function UserMenu() {
  const [open, setOpen] = useState(false)
  const ref = useRef<HTMLDivElement>(null)
  const user = useAuthStore((s) => s.user)
  const logout = useAuthStore((s) => s.logout)

  useEffect(() => {
    function onClick(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false)
    }
    document.addEventListener("mousedown", onClick)
    return () => document.removeEventListener("mousedown", onClick)
  }, [])

  if (!user) return null

  return (
    <div className="relative" ref={ref}>
      <button
        onClick={() => setOpen((v) => !v)}
        className="flex items-center gap-2 rounded-xl py-1 pl-1 pr-2 transition-colors hover:bg-ink-100 dark:hover:bg-ink-800"
      >
        <div className="flex h-8 w-8 items-center justify-center rounded-full bg-brand-100 text-xs font-semibold text-brand-700 dark:bg-brand-500/15 dark:text-brand-300">
          {initials(user)}
        </div>
        <span className="hidden text-sm font-medium text-ink-700 dark:text-ink-200 sm:block">{fullName(user)}</span>
        <ChevronDown className="hidden h-4 w-4 text-ink-400 sm:block" />
      </button>

      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ opacity: 0, y: -8, scale: 0.97 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -8, scale: 0.97 }}
            transition={{ duration: 0.15 }}
            className="absolute right-0 z-30 mt-2 w-56 overflow-hidden rounded-2xl border border-ink-100 bg-white p-1.5 shadow-soft-lg dark:border-ink-800 dark:bg-ink-900"
          >
            <div className="px-3 py-2">
              <p className="truncate text-sm font-semibold text-ink-800 dark:text-white">{fullName(user)}</p>
              <p className="text-xs text-ink-400">{roleLabels(user)}</p>
            </div>
            <div className="my-1 h-px bg-ink-100 dark:bg-ink-800" />
            <Link
              to="/profile"
              onClick={() => setOpen(false)}
              className="flex items-center gap-2 rounded-lg px-3 py-2 text-sm text-ink-600 hover:bg-ink-50 dark:text-ink-300 dark:hover:bg-ink-800"
            >
              <UserIcon className="h-4 w-4" /> Profil
            </Link>
            <Link
              to="/profile"
              onClick={() => setOpen(false)}
              className="flex items-center gap-2 rounded-lg px-3 py-2 text-sm text-ink-600 hover:bg-ink-50 dark:text-ink-300 dark:hover:bg-ink-800"
            >
              <Settings className="h-4 w-4" /> Sozlamalar
            </Link>
            <div className="my-1 h-px bg-ink-100 dark:bg-ink-800" />
            <button
              onClick={logout}
              className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-sm text-rose-600 hover:bg-rose-50 dark:text-rose-400 dark:hover:bg-rose-500/10"
            >
              <SignOutIcon className="h-4 w-4" /> Chiqish
            </button>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
