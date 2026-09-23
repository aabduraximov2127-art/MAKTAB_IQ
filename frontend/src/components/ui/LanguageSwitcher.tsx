import { useEffect, useRef, useState } from "react"
import { AnimatePresence, motion } from "framer-motion"
import { Check, Globe } from "lucide-react"
import { LANGS, getLang, setLang, t } from "../../i18n"

export function LanguageSwitcher() {
  const [open, setOpen] = useState(false)
  const ref = useRef<HTMLDivElement>(null)
  const current = LANGS.find((l) => l.code === getLang()) ?? LANGS[0]

  useEffect(() => {
    if (!open) return
    const onDown = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false)
    }
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && setOpen(false)
    document.addEventListener("mousedown", onDown)
    document.addEventListener("keydown", onKey)
    return () => {
      document.removeEventListener("mousedown", onDown)
      document.removeEventListener("keydown", onKey)
    }
  }, [open])

  return (
    <div ref={ref} className="relative">
      <button
        onClick={() => setOpen((v) => !v)}
        title={t("Til")}
        aria-label={t("Til")}
        aria-expanded={open}
        className="flex h-10 items-center gap-1.5 rounded-full px-3 text-xs font-semibold tracking-wide text-ink-500 transition-colors hover:bg-ink-100 dark:text-ink-400 dark:hover:bg-ink-800"
      >
        <Globe className="h-4 w-4" />
        {current.short}
      </button>
      <AnimatePresence>
        {open && (
          <motion.ul
            initial={{ opacity: 0, y: -6, scale: 0.97 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -6, scale: 0.97 }}
            transition={{ duration: 0.14 }}
            className="absolute right-0 z-40 mt-2 w-40 overflow-hidden rounded-2xl border border-ink-100 bg-white p-1.5 dark:border-ink-800 dark:bg-ink-900"
          >
            {LANGS.map((l) => (
              <li key={l.code}>
                <button
                  onClick={() => {
                    setOpen(false)
                    setLang(l.code)
                  }}
                  className="flex w-full items-center justify-between rounded-xl px-3 py-2 text-sm text-ink-700 transition-colors hover:bg-ink-50 dark:text-ink-200 dark:hover:bg-ink-800"
                >
                  <span>{l.label}</span>
                  {l.code === current.code && <Check className="h-4 w-4 text-brand-500" />}
                </button>
              </li>
            ))}
          </motion.ul>
        )}
      </AnimatePresence>
    </div>
  )
}
