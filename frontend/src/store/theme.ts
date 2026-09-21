import { create } from "zustand"
import { persist } from "zustand/middleware"

type Theme = "dark"

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
    (set) => ({
      // The Dala-style design is a dark stage only (pure black void), so the
      // theme is fixed. The store keeps its shape for sidebar state.
      theme: "dark",
      toggle: () => {
        applyTheme("dark")
        set({ theme: "dark" })
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
