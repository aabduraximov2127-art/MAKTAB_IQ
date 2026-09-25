import { type FormEvent, useState } from "react"
import { Pencil } from "lucide-react"
import toast from "react-hot-toast"
import { useAuthStore } from "../store/auth"
import { api, getErrorMessage } from "../lib/api"
import { useAccess } from "../lib/access"
import { SignOutIcon } from "../components/layout/SignOutIcon"
import { PageHeader } from "../components/ui/PageHeader"
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/Card"
import { Button } from "../components/ui/Button"
import { Field, Input } from "../components/ui/Input"
import { PhoneInput, isPhoneComplete } from "../components/ui/PhoneInput"
import { Avatar } from "../components/ui/Avatar"
import { Badge } from "../components/ui/Badge"
import { TelegramLinkCard } from "../components/shared/TelegramLinkCard"
import { roleLabels, fullName } from "../lib/format"
import type { User } from "../types"
import { localeTag, t } from "../i18n"

export default function ProfilePage() {
  const user = useAuthStore((s) => s.user)
  const logout = useAuthStore((s) => s.logout)
  const { can } = useAccess()
  const [editing, setEditing] = useState(false)

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
                <Badge tone="brand">{roleLabels(user)}</Badge>
                <span className="text-sm text-ink-400">@{user.username}</span>
              </div>
            </div>
          </CardContent>

          {editing ? (
            <ProfileForm user={user} onCancel={() => setEditing(false)} onSaved={() => setEditing(false)} />
          ) : (
            <>
              <div className="grid grid-cols-1 gap-4 border-t border-ink-100 p-5 sm:grid-cols-2 dark:border-ink-800">
                <InfoRow label={t("Email")} value={user.email || "—"} />
                <InfoRow label={t("Telefon")} value={user.phone || "—"} />
                <InfoRow label={t("Holat")} value={user.is_active ? t("Faol") : t("Nofaol")} />
                <InfoRow label={t("Ro'yxatdan o'tgan")} value={new Date(user.date_joined).toLocaleDateString(localeTag())} />
              </div>
              {can("update_own_profile") && (
                <div className="border-t border-ink-100 p-5 dark:border-ink-800">
                  <Button variant="outline" onClick={() => setEditing(true)}>
                    <Pencil className="h-4 w-4" /> {t("Profilni tahrirlash")}
                  </Button>
                </div>
              )}
            </>
          )}
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>{t("Sozlamalar")}</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <Button variant="outline" className="w-full" onClick={logout}>
              <SignOutIcon className="h-4 w-4" /> {t("Tizimdan chiqish")}
            </Button>
          </CardContent>
        </Card>

        <TelegramLinkCard className="lg:col-span-3" />
      </div>
    </div>
  )
}

/** Name, e-mail and phone — only shown to people holding ``update_own_profile``. */
function ProfileForm({ user, onCancel, onSaved }: { user: User; onCancel: () => void; onSaved: () => void }) {
  const setUser = useAuthStore((s) => s.setUser)
  const [form, setForm] = useState({
    first_name: user.first_name,
    last_name: user.last_name,
    email: user.email,
    phone: user.phone,
  })
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    if (!isPhoneComplete(form.phone)) {
      toast.error(t("Telefon raqami to'liq emas"))
      return
    }
    setLoading(true)
    try {
      const { data } = await api.patch<User>("/users/me/profile/", form)
      setUser({ ...user, ...data })
      toast.success(t("Profil yangilandi"))
      onSaved()
    } catch (err) {
      toast.error(getErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4 border-t border-ink-100 p-5 dark:border-ink-800">
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <Field label={t("Ism")}>
          <Input value={form.first_name} onChange={(e) => setForm((f) => ({ ...f, first_name: e.target.value }))} required />
        </Field>
        <Field label={t("Familiya")}>
          <Input value={form.last_name} onChange={(e) => setForm((f) => ({ ...f, last_name: e.target.value }))} required />
        </Field>
        <Field label={t("Email")}>
          <Input type="email" value={form.email} onChange={(e) => setForm((f) => ({ ...f, email: e.target.value }))} />
        </Field>
        <Field label={t("Telefon")}>
          <PhoneInput value={form.phone} onChange={(phone) => setForm((f) => ({ ...f, phone }))} />
        </Field>
      </div>
      <div className="flex gap-2">
        <Button type="submit" loading={loading}>
          {t("Saqlash")}
        </Button>
        <Button type="button" variant="outline" onClick={onCancel}>
          {t("Bekor qilish")}
        </Button>
      </div>
    </form>
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
