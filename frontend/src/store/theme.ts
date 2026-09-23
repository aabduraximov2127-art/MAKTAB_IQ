import { create } from "zustand"
import { persist } from "zustand/middleware"

export type Theme = "light" | "dark"

interface ThemeState {
  theme: Theme
  toggle: () => void
  set: (theme: Theme) => void
  sidebarCollapsed: boolean
  toggleSidebar: () => void
}

function applyTheme(theme: Theme) {
  document.documentElement.classList.toggle("dark", theme === "dark")
}

type ViewTransitionDocument = Document & { startViewTransition?: (cb: () => void) => unknown }

/** Switch theme with a top-to-bottom "curtain" reveal (View Transitions API); falls back to an instant swap. */
function switchTheme(next: Theme, commit: () => void) {
  const doc = document as ViewTransitionDocument
  const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches
  if (!doc.startViewTransition || reduce) {
    applyTheme(next)
    commit()
    return
  }
  doc.startViewTransition(() => {
    applyTheme(next)
    commit()
  })
}

export const useThemeStore = create<ThemeState>()(
  persist(
    (set, get) => ({
      theme: "dark",
      toggle: () => {
        const next: Theme = get().theme === "dark" ? "light" : "dark"
        switchTheme(next, () => set({ theme: next }))
      },
      set: (theme) => {
        applyTheme(theme)
        set({ theme })
      },
      sidebarCollapsed: false,
      toggleSidebar: () => set((s) => ({ sidebarCollapsed: !s.sidebarCollapsed })),
    }),
    {
      name: "maktabiq-theme-v2",
      onRehydrateStorage: () => (state) => {
        if (state) applyTheme(state.theme)
      },
    }
  )
)
