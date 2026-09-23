import { type FormEvent, useState } from "react"
import { ApiError, api, setTokens } from "../api"
import { getTelegram, isInsideTelegram } from "../telegram"
import { useMainButton } from "../useMainButton"
import type { User } from "../types"

interface LoginResponse {
  access: string
  refresh: string
}

export function Login({ onSignedIn }: { onSignedIn: (user: User) => void }) {
  const [username, setUsername] = useState("")
  const [password, setPassword] = useState("")
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const insideTelegram = isInsideTelegram()

  async function submit() {
    if (!username.trim() || !password) {
      setError("Login va parolni kiriting")
      return
    }
    setLoading(true)
    setError(null)
    try {
      const tg = getTelegram()
      const data = await api.post<LoginResponse>("/auth/telegram/login/", {
        init_data: tg?.initData ?? "",
        username: username.trim(),
        password,
      })
      setTokens(data.access, data.refresh)
      tg?.HapticFeedback?.notificationOccurred("success")
      const me = await api.get<User>("/users/me/")
      onSignedIn(me)
    } catch (err) {
      getTelegram()?.HapticFeedback?.notificationOccurred("error")
      setError(err instanceof ApiError ? err.message : "Xatolik yuz berdi")
    } finally {
      setLoading(false)
    }
  }

  function handleSubmit(e: FormEvent) {
    e.preventDefault()
    void submit()
  }

  useMainButton({ text: "Kirish", active: insideTelegram, loading, onClick: () => void submit() })

  return (
    <div>
      <div className="app-header">
        <div className="greeting">MaktabIQ</div>
        <div className="subtitle">Hisobingizga kirib, Telegramni ulang</div>
      </div>

      <form onSubmit={handleSubmit}>
        <div className="section-body" style={{ padding: "14px" }}>
          <div className="field">
            <label htmlFor="username">Foydalanuvchi nomi</label>
            <input
              id="username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              autoCapitalize="none"
              autoCorrect="off"
              autoFocus
            />
          </div>
          <div className="field" style={{ marginBottom: 4 }}>
            <label htmlFor="password">Parol</label>
            <input id="password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} />
          </div>
        </div>

        {error && <p className="error-text">{error}</p>}

        {!insideTelegram && (
          <button
            type="submit"
            disabled={loading}
            style={{
              marginTop: 14,
              width: "100%",
              padding: "12px",
              borderRadius: 12,
              border: "none",
              fontSize: 15,
              fontWeight: 600,
              background: "var(--tg-theme-button-color, #2481cc)",
              color: "var(--tg-theme-button-text-color, #fff)",
            }}
          >
            {loading ? "Kuting..." : "Kirish"}
          </button>
        )}
      </form>

      <p className="hint" style={{ marginTop: 16, padding: "0 4px" }}>
        Kirgach, shu Telegram hisobingiz avtomatik ulanadi — keyingi safar ilova o'zi tanib
        oladi, qayta login kerak emas.
      </p>
    </div>
  )
}
