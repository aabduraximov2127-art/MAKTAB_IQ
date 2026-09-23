import { useCallback, useEffect, useRef, useState } from "react"
import { Check, Copy, ExternalLink, Loader2, Send, Unlink } from "lucide-react"
import toast from "react-hot-toast"
import { api, getErrorMessage } from "../../lib/api"
import { useAuthStore } from "../../store/auth"
import { Button } from "../ui/Button"
import { Card, CardContent, CardHeader, CardTitle } from "../ui/Card"
import { Badge } from "../ui/Badge"
import { t } from "../../i18n"

const BOT_USERNAME = "maktabIQ_bot"
const POLL_MS = 3000

function mmss(seconds: number) {
  const m = Math.floor(seconds / 60)
  const s = seconds % 60
  return `${m}:${String(s).padStart(2, "0")}`
}

/**
 * Connect the account to the Telegram bot: the site issues a one-time code, the user sends it
 * to the bot, the bot verifies it against the site, and this card notices the link (polling).
 */
export function TelegramLinkCard({ className }: { className?: string }) {
  const user = useAuthStore((s) => s.user)
  const setUser = useAuthStore((s) => s.setUser)
  const linked = !!user?.telegram_linked

  const [code, setCode] = useState<string | null>(null)
  const [secondsLeft, setSecondsLeft] = useState(0)
  const [loading, setLoading] = useState(false)
  const [copied, setCopied] = useState(false)
  const wasLinked = useRef(linked)

  const refreshUser = useCallback(async () => {
    const { data } = await api.get("/users/me/")
    setUser(data)
    return data
  }, [setUser])

  async function requestCode() {
    setLoading(true)
    try {
      const { data } = await api.post("/users/me/telegram-link-code/")
      setCode(data.code)
      setSecondsLeft(data.expires_in ?? 600)
    } catch (err) {
      toast.error(getErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  async function unlink() {
    try {
      await api.post("/users/me/telegram-unlink/")
      await refreshUser()
      setCode(null)
      toast.success(t("Telegram uzildi"))
    } catch (err) {
      toast.error(getErrorMessage(err))
    }
  }

  async function copyCode() {
    if (!code) return
    try {
      await navigator.clipboard.writeText(code)
      setCopied(true)
      toast.success(t("Nusxalandi"))
      setTimeout(() => setCopied(false), 1500)
    } catch {
      /* clipboard unavailable */
    }
  }

  // Countdown while a code is active.
  useEffect(() => {
    if (!code || secondsLeft <= 0) return
    const id = setInterval(() => setSecondsLeft((s) => s - 1), 1000)
    return () => clearInterval(id)
  }, [code, secondsLeft > 0]) // eslint-disable-line react-hooks/exhaustive-deps

  // While waiting for the bot to confirm, poll the site (the bot verifies the code server-side).
  useEffect(() => {
    if (!code || linked || secondsLeft <= 0) return
    const id = setInterval(() => {
      api
        .get("/users/me/telegram-status/")
        .then(({ data }) => {
          if (data.linked) void refreshUser()
        })
        .catch(() => undefined)
    }, POLL_MS)
    return () => clearInterval(id)
  }, [code, linked, secondsLeft > 0, refreshUser]) // eslint-disable-line react-hooks/exhaustive-deps

  // Linked just now → celebrate once and drop the code.
  useEffect(() => {
    if (linked && !wasLinked.current) {
      toast.success(t("Telegram muvaffaqiyatli ulandi!"))
      setCode(null)
    }
    wasLinked.current = linked
  }, [linked])

  const expired = !!code && secondsLeft <= 0

  return (
    <Card className={className}>
      <CardHeader>
        <div className="flex items-center gap-2">
          <Send className="h-4 w-4 text-brand-500" />
          <CardTitle>{t("Telegram botga ulanish")}</CardTitle>
        </div>
        <Badge tone={linked ? "success" : "neutral"}>{linked ? t("Ulangan") : t("Ulanmagan")}</Badge>
      </CardHeader>
      <CardContent className="space-y-4">
        {linked ? (
          <>
            <p className="text-sm text-ink-500 dark:text-ink-400">
              {t("Telegram hisobingiz ulangan. Bildirishnomalar botga yuboriladi.")}
            </p>
            <Button variant="outline" size="sm" onClick={unlink}>
              <Unlink className="h-4 w-4" /> {t("Uzish")}
            </Button>
          </>
        ) : (
          <>
            <p className="text-sm text-ink-500 dark:text-ink-400">
              {t("Bildirishnomalar (davomat, baho, e'lonlar) Telegram orqali kelishi uchun kodni botga yuboring.")}
            </p>

            {code && !expired ? (
              <div className="space-y-3">
                <p className="eyebrow text-ink-400">{t("Kodni botga yuboring")}</p>
                <div className="flex flex-wrap items-center gap-3">
                  <span className="font-display select-all text-4xl tracking-[0.2em] text-ink-900 dark:text-white">{code}</span>
                  <Button variant="ghost" size="icon" onClick={copyCode} title={t("Kodni nusxalash")} aria-label={t("Kodni nusxalash")}>
                    {copied ? <Check className="h-4 w-4 text-emerald-500" /> : <Copy className="h-4 w-4" />}
                  </Button>
                </div>
                <p className="text-xs text-ink-400">{t("Kod {time} dan keyin eskiradi", { time: mmss(secondsLeft) })}</p>
                <div className="flex flex-wrap items-center gap-3">
                  <a
                    href={`https://t.me/${BOT_USERNAME}?start=${code}`}
                    target="_blank"
                    rel="noreferrer"
                    className="inline-flex h-11 items-center gap-2 rounded-full bg-brand-600 px-5 text-[13px] font-semibold uppercase tracking-[0.025em] text-white transition-colors hover:bg-brand-700"
                  >
                    <ExternalLink className="h-4 w-4" /> {t("Botni ochish")}
                  </a>
                  <span className="flex items-center gap-2 text-xs text-ink-400">
                    <Loader2 className="h-3.5 w-3.5 animate-spin" /> {t("Bot kodni kutmoqda...")}
                  </span>
                </div>
              </div>
            ) : (
              <div className="space-y-3">
                {expired && <p className="text-sm text-amber-500">{t("Kod muddati tugadi. Yangi kod oling.")}</p>}
                <Button onClick={requestCode} loading={loading}>
                  {expired ? t("Yangi kod olish") : t("Kod olish")}
                </Button>
              </div>
            )}
          </>
        )}
      </CardContent>
    </Card>
  )
}
