import { useEffect, useState } from "react"
import { api, hasSession, setTokens, clearTokens } from "./api"
import { getTelegram } from "./telegram"
import { Login } from "./screens/Login"
import { Home } from "./screens/Home"
import type { User } from "./types"

interface TelegramAuthResponse {
  linked: boolean
  access?: string
  refresh?: string
}

type Screen = { name: "loading" } | { name: "login" } | { name: "home"; user: User } | { name: "error"; message: string }

export default function App() {
  const [screen, setScreen] = useState<Screen>({ name: "loading" })

  useEffect(() => {
    const tg = getTelegram()
    if (!tg) {
      setScreen({ name: "error", message: "Telegram WebApp topilmadi. Ilovani Telegram ichida oching." })
      return
    }
    tg.ready()
    tg.expand()
    void bootstrap()
  }, [])

  async function bootstrap() {
    // Reusing an existing session (e.g. a re-render within the same open) skips the
    // round-trip through /auth/telegram/ — if it's no longer valid, fall through below.
    if (hasSession()) {
      try {
        const me = await api.get<User>("/users/me/")
        setScreen({ name: "home", user: me })
        return
      } catch {
        clearTokens()
      }
    }

    try {
      const tg = getTelegram()!
      const result = await api.post<TelegramAuthResponse>("/auth/telegram/", { init_data: tg.initData })
      if (result.linked && result.access && result.refresh) {
        setTokens(result.access, result.refresh)
        const me = await api.get<User>("/users/me/")
        setScreen({ name: "home", user: me })
        return
      }
    } catch {
      /* initData couldn't be verified (or this chat isn't linked yet) — either way, sign in below */
    }
    setScreen({ name: "login" })
  }

  if (screen.name === "loading") {
    return (
      <div className="center-screen">
        <div className="spinner" />
      </div>
    )
  }

  if (screen.name === "error") {
    return (
      <div className="center-screen">
        <p className="hint">{screen.message}</p>
      </div>
    )
  }

  if (screen.name === "login") {
    return <Login onSignedIn={(user) => setScreen({ name: "home", user })} />
  }

  return <Home user={screen.user} onSignedOut={() => setScreen({ name: "login" })} />
}
