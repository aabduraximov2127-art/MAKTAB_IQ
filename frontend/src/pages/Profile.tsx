import { LogOut } from "lucide-react"
import { useAuthStore } from "../store/auth"
import { PageHeader } from "../components/ui/PageHeader"
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/Card"
import { Button } from "../components/ui/Button"
import { Avatar } from "../components/ui/Avatar"
import { Badge } from "../components/ui/Badge"
import { TelegramLinkCard } from "../components/shared/TelegramLinkCard"
import { ROLE_LABELS, fullName } from "../lib/format"
import { localeTag, t } from "../i18n"

export default function ProfilePage() {
  const user = useAuthStore((s) => s.user)
  const logout = useAuthStore((s) => s.logout)


  if (!user) return null


  return (
    <div>
      <PageHeader title={t("Profil")} description={t("Shaxsiy ma'lumotlaringiz va sozlamalar")} />

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
            <InfoRow label={t("Email")} value={user.email || "—"} />
            <InfoRow label={t("Telefon")} value={user.phone || "—"} />
            <InfoRow label={t("Holat")} value={user.is_active ? t("Faol") : t("Nofaol")} />
            <InfoRow label={t("Ro'yxatdan o'tgan")} value={new Date(user.date_joined).toLocaleDateString(localeTag())} />
          </div>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>{t("Sozlamalar")}</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <Button variant="outline" className="w-full" onClick={logout}>
              <LogOut className="h-4 w-4" /> {t("Tizimdan chiqish")}
            </Button>
          </CardContent>
        </Card>

        <TelegramLinkCard className="lg:col-span-3" />
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
