import { useState } from "react"
import { Copy, LogOut, Send, ShieldCheck } from "lucide-react"
import toast from "react-hot-toast"
import { api, getErrorMessage } from "../lib/api"
import { useAuthStore } from "../store/auth"
import { PageHeader } from "../components/ui/PageHeader"
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/Card"
import { Button } from "../components/ui/Button"
import { Avatar } from "../components/ui/Avatar"
import { Badge } from "../components/ui/Badge"
import { ROLE_LABELS, fullName } from "../lib/format"

export default function ProfilePage() {
  const user = useAuthStore((s) => s.user)
  const logout = useAuthStore((s) => s.logout)

  const [code, setCode] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  if (!user) return null

  async function generateCode() {
    setLoading(true)
    try {
      const { data } = await api.post("/users/me/telegram-link-code/")
      setCode(data.code)
    } catch (err) {
      toast.error(getErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  function copyCode() {
    if (!code) return
    navigator.clipboard.writeText(code)
    toast.success("Nusxalandi")
  }

  return (
    <div>
      <PageHeader title="Profil" description="Shaxsiy ma'lumotlaringiz va sozlamalar" />

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardContent className="flex items-center gap-4">
            <Avatar name={fullName(user)} size="lg" />
            <div>
              <p className="font-display text-lg font-bold text-ink-900 dark:text-white">{fullName(user)}</p>
              <div className="mt-1 flex items-center gap-2">
                <Badge tone="brand">{ROLE_LABELS[user.role]}</Badge>
                <span className="text-sm text-ink-400">@{user.username}</span>
              </div>
            </div>
          </CardContent>

          <div className="grid grid-cols-1 gap-4 border-t border-ink-100 p-5 sm:grid-cols-2 dark:border-ink-800">
            <InfoRow label="Email" value={user.email || "—"} />
            <InfoRow label="Telefon" value={user.phone || "—"} />
            <InfoRow label="Holat" value={user.is_active ? "Faol" : "Nofaol"} />
            <InfoRow label="Ro'yxatdan o'tgan" value={new Date(user.date_joined).toLocaleDateString("uz-UZ")} />
          </div>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Sozlamalar</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <Button variant="outline" className="w-full" onClick={logout}>
              <LogOut className="h-4 w-4" /> Tizimdan chiqish
            </Button>
          </CardContent>
        </Card>

        <Card className="lg:col-span-3">
          <CardHeader>
            <CardTitle>Telegram bilan bog'lash</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-ink-500 dark:text-ink-400">
              Bildirishnomalarni (davomat, baho, e'lonlar) Telegram orqali olish uchun kod oling va MaktabIQ botiga{" "}
              <code className="rounded bg-ink-100 px-1.5 py-0.5 text-xs dark:bg-ink-800">/link &lt;kod&gt;</code> buyrug'i bilan yuboring.
            </p>
            <div className="mt-4 flex flex-wrap items-center gap-3">
              <Button onClick={generateCode} loading={loading}>
                <Send className="h-4 w-4" /> Kod olish
              </Button>
              {code && (
                <button
                  onClick={copyCode}
                  className="flex items-center gap-2 rounded-xl border border-dashed border-brand-300 bg-brand-50 px-4 py-2.5 font-mono text-lg font-bold tracking-widest text-brand-700 dark:border-brand-500/40 dark:bg-brand-500/10 dark:text-brand-300"
                >
                  {code} <Copy className="h-4 w-4" />
                </button>
              )}
            </div>
            <div className="mt-4 flex items-center gap-2 rounded-xl bg-ink-100/60 px-3.5 py-2.5 text-xs text-ink-500 dark:bg-ink-800/50 dark:text-ink-400">
              <ShieldCheck className="h-4 w-4 shrink-0 text-emerald-500" /> Kod 10 daqiqa amal qiladi
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

function InfoRow({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-xs font-medium uppercase tracking-wide text-ink-400">{label}</p>
      <p className="mt-1 text-sm font-medium text-ink-800 dark:text-ink-100">{value}</p>
    </div>
  )
}
