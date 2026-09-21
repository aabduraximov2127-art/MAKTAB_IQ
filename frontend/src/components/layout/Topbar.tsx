import { Menu } from "lucide-react"
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
  return (
    <header className="sticky top-0 z-20 flex h-16 items-center justify-between gap-4 border-b border-ink-100 bg-white px-4 dark:border-ink-800 dark:bg-ink-950 sm:px-6">
      <div className="flex items-center gap-3">
        <button
          onClick={onMenuClick}
          className="flex h-10 w-10 items-center justify-center rounded-xl text-ink-500 hover:bg-ink-100 dark:text-ink-400 dark:hover:bg-ink-800 lg:hidden"
        >
          <Menu className="h-5 w-5" />
        </button>
        <div className="hidden sm:block">
          <p className="eyebrow text-ink-400">
            {greeting()}
            {firstName ? `, ${firstName}` : ""}
          </p>
        </div>
      </div>

      <div className="flex items-center gap-2">
        <NotificationBell />
        <div className="mx-1 hidden h-6 w-px bg-ink-200 dark:bg-ink-800 sm:block" />
        <UserMenu />
      </div>
    </header>
  )
}
