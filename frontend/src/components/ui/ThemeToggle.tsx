import { AnimatePresence, motion } from "framer-motion"
import { Moon, Sun } from "lucide-react"
import { useThemeStore } from "../../store/theme"
import { t } from "../../i18n"

export function ThemeToggle() {
  const theme = useThemeStore((s) => s.theme)
  const toggle = useThemeStore((s) => s.toggle)
  const isDark = theme === "dark"

  return (
    <button
      onClick={toggle}
      title={isDark ? t("Yorug' rejim") : t("Qorong'i rejim")}
      aria-label={isDark ? t("Yorug' rejim") : t("Qorong'i rejim")}
      className="flex h-10 w-10 items-center justify-center overflow-hidden rounded-full text-ink-500 transition-colors hover:bg-ink-100 dark:text-ink-400 dark:hover:bg-ink-800"
    >
      <AnimatePresence mode="wait" initial={false}>
        <motion.span
          key={theme}
          initial={{ y: -14, opacity: 0, rotate: -40 }}
          animate={{ y: 0, opacity: 1, rotate: 0 }}
          exit={{ y: 14, opacity: 0, rotate: 40 }}
          transition={{ duration: 0.18 }}
          className="flex"
        >
          {isDark ? <Sun className="h-5 w-5" /> : <Moon className="h-5 w-5" />}
        </motion.span>
      </AnimatePresence>
    </button>
  )
}
