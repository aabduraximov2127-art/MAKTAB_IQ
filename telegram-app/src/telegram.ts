/** Thin wrapper around window.Telegram.WebApp (loaded by the <script> tag in index.html). */

export interface TelegramUser {
  id: number
  first_name: string
  last_name?: string
  username?: string
}

interface HapticFeedback {
  impactOccurred(style: "light" | "medium" | "heavy" | "rigid" | "soft"): void
  notificationOccurred(type: "error" | "success" | "warning"): void
}

interface MainButton {
  text: string
  isVisible: boolean
  isActive: boolean
  setText(text: string): MainButton
  show(): MainButton
  hide(): MainButton
  enable(): MainButton
  disable(): MainButton
  showProgress(leaveActive?: boolean): MainButton
  hideProgress(): MainButton
  onClick(cb: () => void): MainButton
  offClick(cb: () => void): MainButton
}

export interface TelegramWebApp {
  initData: string
  initDataUnsafe: { user?: TelegramUser; auth_date?: number; hash?: string }
  colorScheme: "light" | "dark"
  platform: string
  version: string
  ready(): void
  expand(): void
  close(): void
  openLink(url: string, options?: { try_instant_view?: boolean }): void
  onEvent(event: "themeChanged" | "viewportChanged", cb: () => void): void
  offEvent(event: "themeChanged" | "viewportChanged", cb: () => void): void
  HapticFeedback?: HapticFeedback
  MainButton: MainButton
}

declare global {
  interface Window {
    Telegram?: { WebApp: TelegramWebApp }
  }
}

/** True once the version check below has confirmed a real Telegram host is present. */
export function isInsideTelegram(): boolean {
  return !!window.Telegram?.WebApp?.initData
}

export function getTelegram(): TelegramWebApp | null {
  return window.Telegram?.WebApp ?? null
}

/**
 * Dev-only stand-in for `window.Telegram.WebApp` so the app is usable in a plain browser
 * tab while building it — `npm run dev` and open http://localhost:5174 directly. Never
 * runs in production: `import.meta.env.DEV` is compiled away by Vite in a real build, and
 * outside Telegram there is no real initData anyway, so the backend simply reports
 * "not linked" and the login screen appears exactly like it would on a phone.
 */
export function installDevFallback() {
  if (!import.meta.env.DEV || window.Telegram?.WebApp) return
  const listeners = new Map<string, Set<() => void>>()
  const scheme: "light" | "dark" = window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light"
  document.documentElement.style.setProperty("--tg-theme-bg-color", scheme === "dark" ? "#17212b" : "#ffffff")
  document.documentElement.style.setProperty("--tg-theme-text-color", scheme === "dark" ? "#f5f5f5" : "#222222")
  window.Telegram = {
    WebApp: {
      initData: "",
      initDataUnsafe: {},
      colorScheme: scheme,
      platform: "web",
      version: "7.0",
      ready() {},
      expand() {},
      close() {
        window.close()
      },
      openLink(url: string) {
        window.open(url, "_blank")
      },
      onEvent(event, cb) {
        if (!listeners.has(event)) listeners.set(event, new Set())
        listeners.get(event)!.add(cb)
      },
      offEvent(event, cb) {
        listeners.get(event)?.delete(cb)
      },
      MainButton: {
        text: "",
        isVisible: false,
        isActive: true,
        setText(text) {
          this.text = text
          return this
        },
        show() {
          this.isVisible = true
          return this
        },
        hide() {
          this.isVisible = false
          return this
        },
        enable() {
          this.isActive = true
          return this
        },
        disable() {
          this.isActive = false
          return this
        },
        showProgress() {
          return this
        },
        hideProgress() {
          return this
        },
        onClick() {
          return this
        },
        offClick() {
          return this
        },
      },
    },
  }
}
