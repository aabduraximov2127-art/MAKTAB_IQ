import { Menu, Moon, Sun } from "lucide-react"
import { useThemeStore } from "../../store/theme"
import { NotificationBell } from "./NotificationBell"
import { UserMenu } from "./UserMenu"

function greeting() {
  const hour = new Date().getHours()
  if (hour < 6) return "Xayrli tun"
  if (hour < 12) return "Xayrli tong"
  if (hour < 17) return "Xayrli kun"
  return "Xayrli kech"
}

export function Topbar({ onMenuClick, firstName }: { onMenuClick: () => void; firstName?: string }) {
  const theme = useThemeStore((s) => s.theme)
  const toggle = useThemeStore((s) => s.toggle)

  return (
    <header className="sticky top-0 z-20 flex h-16 items-center justify-between gap-4 border-b border-ink-100 bg-white/80 px-4 backdrop-blur-lg dark:border-ink-800 dark:bg-ink-950/80 sm:px-6">
      <div className="flex items-center gap-3">
        <button
          onClick={onMenuClick}
          className="flex h-10 w-10 items-center justify-center rounded-xl text-ink-500 hover:bg-ink-100 dark:text-ink-400 dark:hover:bg-ink-800 lg:hidden"
        >
          <Menu className="h-5 w-5" />
        </button>
        <div className="hidden sm:block">
          <p className="text-sm text-ink-400">
            {greeting()}
            {firstName ? `, ${firstName}` : ""} 👋
          </p>
        </div>
      </div>

      <div className="flex items-center gap-2">
        <button
          onClick={toggle}
          className="flex h-10 w-10 items-center justify-center rounded-xl text-ink-500 transition-colors hover:bg-ink-100 dark:text-ink-400 dark:hover:bg-ink-800"
        >
          {theme === "dark" ? <Sun className="h-5 w-5" /> : <Moon className="h-5 w-5" />}
        </button>
        <NotificationBell />
        <div className="mx-1 hidden h-6 w-px bg-ink-200 dark:bg-ink-700 sm:block" />
        <UserMenu />
      </div>
    </header>
  )
}
