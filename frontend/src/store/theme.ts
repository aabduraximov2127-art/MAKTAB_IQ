import { create } from "zustand"
import { persist } from "zustand/middleware"

type Theme = "light" | "dark"

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

export const useThemeStore = create<ThemeState>()(
  persist(
    (set, get) => ({
      // Default to light regardless of OS preference — most users find an
      // auto-selected dark mode here too gloomy for a school dashboard. The
      // toggle in the topbar still switches to dark on request.
      theme: "light",
      toggle: () => {
        const next = get().theme === "dark" ? "light" : "dark"
        applyTheme(next)
        set({ theme: next })
      },
      set: (theme) => {
        applyTheme(theme)
        set({ theme })
      },
      sidebarCollapsed: false,
      toggleSidebar: () => set((s) => ({ sidebarCollapsed: !s.sidebarCollapsed })),
    }),
    {
      name: "maktabiq-theme",
      onRehydrateStorage: () => (state) => {
        if (state) applyTheme(state.theme)
      },
    }
  )
)
