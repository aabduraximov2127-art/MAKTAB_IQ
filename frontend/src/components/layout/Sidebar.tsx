import { NavLink } from "react-router-dom"
import { motion } from "framer-motion"
import { ChevronLeft, ChevronRight, LogOut, X } from "lucide-react"
import { useAuthStore } from "../../store/auth"
import { Logo } from "../shared/Logo"
import { useThemeStore } from "../../store/theme"
import { navForUser } from "../../lib/nav"
import { roleLabels, fullName, initials } from "../../lib/format"
import { cn } from "../../lib/cn"
import { t } from "../../i18n"

interface SidebarProps {
  mobileOpen: boolean
  onCloseMobile: () => void
}

function SidebarContent({
  collapsed,
  onNavigate,
  onCloseMobile,
}: {
  collapsed: boolean
  onNavigate: () => void
  onCloseMobile?: () => void
}) {
  const user = useAuthStore((s) => s.user)
  const logout = useAuthStore((s) => s.logout)
  if (!user) return null

  const items = navForUser(user)
  const sections = Array.from(new Set(items.map((i) => i.section ?? "")))

  return (
    <div className="flex h-full flex-col bg-white dark:bg-ink-900">
      <div className={cn("flex items-center gap-2 px-5 py-5", collapsed ? "justify-center px-3" : "justify-between")}>
        <Logo showWord={!collapsed} />
        {onCloseMobile && (
          <button onClick={onCloseMobile} className="rounded-lg p-1.5 text-ink-400 hover:bg-ink-100 dark:hover:bg-ink-800 lg:hidden">
            <X className="h-5 w-5" />
          </button>
        )}
      </div>

      <nav className="flex-1 space-y-5 overflow-y-auto overflow-x-hidden px-3 pb-4">
        {sections.map((section) => (
          <div key={section}>
            {!collapsed && (
              <p className="px-3 pb-1.5 eyebrow text-[11px] text-ink-400 dark:text-ink-500">
                {section}
              </p>
            )}
            <div className="space-y-0.5">
              {items
                .filter((i) => (i.section ?? "") === section)
                .map((item) => (
                  <NavLink
                    key={item.to}
                    to={item.to}
                    end={item.to === "/"}
                    onClick={onNavigate}
                    title={collapsed ? item.label : undefined}
                    className={({ isActive }) =>
                      cn(
                        "group relative flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-colors",
                        collapsed && "justify-center px-0",
                        isActive
                          ? "text-brand-700 dark:text-brand-300"
                          : "text-ink-600 hover:bg-ink-50 hover:text-ink-900 dark:text-ink-400 dark:hover:bg-ink-800/70 dark:hover:text-white"
                      )
                    }
                  >
                    {({ isActive }) => (
                      <>
                        {isActive && (
                          <motion.span
                            layoutId="sidebar-active"
                            className="absolute inset-0 rounded-xl bg-brand-50 dark:bg-brand-500/10"
                            transition={{ type: "spring", duration: 0.4, bounce: 0.2 }}
                          />
                        )}
                        <item.icon className="relative h-[18px] w-[18px] shrink-0" />
                        {!collapsed && <span className="relative truncate">{item.label}</span>}
                      </>
                    )}
                  </NavLink>
                ))}
            </div>
          </div>
        ))}
      </nav>

      <div className="border-t border-ink-100 p-3 dark:border-ink-800">
        <div className={cn("flex items-center gap-2.5 rounded-xl p-2", collapsed && "justify-center")}>
          <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-brand-100 text-sm font-semibold text-brand-700 dark:bg-brand-500/15 dark:text-brand-300">
            {initials(user)}
          </div>
          {!collapsed && (
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-semibold text-ink-800 dark:text-ink-100">{fullName(user)}</p>
              <p className="truncate text-xs text-ink-400">{roleLabels(user)}</p>
            </div>
          )}
          {!collapsed && (
            <button
              onClick={logout}
              title={t("Chiqish")}
              className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg text-ink-400 transition-colors hover:bg-rose-50 hover:text-rose-600 dark:hover:bg-rose-500/10"
            >
              <LogOut className="h-4 w-4" />
            </button>
          )}
        </div>
      </div>
    </div>
  )
}

export function Sidebar({ mobileOpen, onCloseMobile }: SidebarProps) {
  const collapsed = useThemeStore((s) => s.sidebarCollapsed)
  const toggleSidebar = useThemeStore((s) => s.toggleSidebar)

  return (
    <>
      <motion.aside
        animate={{ width: collapsed ? 80 : 288 }}
        transition={{ type: "spring", duration: 0.35, bounce: 0.1 }}
        className="relative hidden shrink-0 border-r border-ink-100 dark:border-ink-800 lg:block"
      >
        <SidebarContent collapsed={collapsed} onNavigate={() => {}} />
        <button
          onClick={toggleSidebar}
          className="absolute -right-3 top-20 flex h-6 w-6 items-center justify-center rounded-full border border-ink-200 bg-white text-ink-500 shadow-soft transition-colors hover:bg-ink-50 hover:text-brand-600 dark:border-ink-700 dark:bg-ink-800 dark:text-ink-300 dark:hover:bg-ink-700"
          title={collapsed ? t("Sidebarni kengaytirish") : t("Sidebarni yig'ish")}
        >
          {collapsed ? <ChevronRight className="h-3.5 w-3.5" /> : <ChevronLeft className="h-3.5 w-3.5" />}
        </button>
      </motion.aside>

      {mobileOpen && (
        <div className="fixed inset-0 z-40 lg:hidden">
          <div className="absolute inset-0 bg-ink-950/50" onClick={onCloseMobile} />
          <motion.div
            initial={{ x: -300 }}
            animate={{ x: 0 }}
            exit={{ x: -300 }}
            transition={{ type: "spring", duration: 0.35, bounce: 0.15 }}
            className="absolute inset-y-0 left-0 w-72 shadow-soft-lg"
          >
            <SidebarContent collapsed={false} onNavigate={onCloseMobile} onCloseMobile={onCloseMobile} />
          </motion.div>
        </div>
      )}
    </>
  )
}
