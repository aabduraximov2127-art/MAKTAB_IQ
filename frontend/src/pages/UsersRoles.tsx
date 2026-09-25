import { useState } from "react"
import { Search, ShieldCheck, Trash2, X } from "lucide-react"
import toast from "react-hot-toast"
import { useFetch } from "../hooks/useFetch"
import { api, getErrorMessage } from "../lib/api"
import { ASSIGNABLE_ROLES, useAccess } from "../lib/access"
import { ROLE_LABELS, fullName } from "../lib/format"
import { PageHeader } from "../components/ui/PageHeader"
import { Button } from "../components/ui/Button"
import { Avatar } from "../components/ui/Avatar"
import { Badge } from "../components/ui/Badge"
import { Drawer } from "../components/ui/Drawer"
import { Input } from "../components/ui/Input"
import { Select } from "../components/ui/Select"
import { Pagination } from "../components/ui/Pagination"
import { Skeleton } from "../components/ui/Skeleton"
import { DataTable, type Column } from "../components/ui/Table"
import type { EffectiveRole, Paginated, Role } from "../types"
import { t } from "../i18n"

const PAGE_SIZE = 15

interface AdminUser {
  id: number
  username: string
  first_name: string
  last_name: string
  role: Role
  roles: Role[]
  extra_permissions: string[]
  is_active: boolean
}

interface AccessInfo {
  id: number
  username: string
  primary_role: Role
  extra_roles: Role[]
  roles: EffectiveRole[]
  permissions: string[]
  extra_permissions: string[]
  curated_classes: { id: number; name: string }[]
}

interface PermissionDef {
  codename: string
  category: string
  description: string
  system: boolean
}

const CATEGORY_LABELS: Record<string, string> = {
  own: t("Shaxsiy ma'lumotlar"),
  child: t("Farzand"),
  teacher: t("O'qituvchi"),
  class_teacher: t("Sinf rahbari"),
  school: t("Maktab bo'yicha"),
  management: t("Boshqaruv"),
}

/**
 * Users & Roles — the administrator's console: give and take away roles (a user may hold
 * several), hand a single user an extra permission, and (de)activate accounts. The API
 * enforces every rule (no self-edit, school confinement, only a SUPERADMIN hands out
 * SUPERADMIN or system-level permissions); the disabled controls here only mirror them.
 */
export default function UsersRolesPage() {
  const { can } = useAccess()
  const [search, setSearch] = useState("")
  const [role, setRole] = useState("")
  const [page, setPage] = useState(1)
  const [selected, setSelected] = useState<AdminUser | null>(null)

  const query = new URLSearchParams({ page: String(page), page_size: String(PAGE_SIZE) })
  if (search) query.set("search", search)
  if (role) query.set("role", role)

  const { data, loading, refetch } = useFetch<Paginated<AdminUser>>(`/users/?${query.toString()}`, [page, search, role])

  const columns: Column<AdminUser>[] = [
    {
      key: "user",
      header: t("Foydalanuvchi"),
      render: (u) => (
        <div className="flex items-center gap-3">
          <Avatar name={fullName(u)} size="sm" />
          <div className="min-w-0">
            <p className="truncate font-medium text-ink-800 dark:text-ink-100">{fullName(u)}</p>
            <p className="truncate text-xs text-ink-400">@{u.username}</p>
          </div>
        </div>
      ),
    },
    {
      key: "roles",
      header: t("Rollar"),
      render: (u) => (
        <div className="flex flex-wrap gap-1.5">
          {u.roles.map((r, i) => (
            <Badge key={r} tone={i === 0 ? "brand" : "info"}>
              {ROLE_LABELS[r]}
            </Badge>
          ))}
        </div>
      ),
    },
    {
      key: "perms",
      header: t("Alohida ruxsatlar"),
      render: (u) => (u.extra_permissions.length ? <Badge tone="warning">{u.extra_permissions.length}</Badge> : "—"),
      hideOnMobile: true,
    },
    {
      key: "status",
      header: t("Holat"),
      render: (u) => <Badge tone={u.is_active ? "success" : "neutral"}>{u.is_active ? t("Faol") : t("Nofaol")}</Badge>,
      hideOnMobile: true,
    },
  ]

  return (
    <div>
      <PageHeader
        title={can("manage_roles") ? t("Foydalanuvchilar va rollar") : t("Foydalanuvchilar")}
        description={
          can("manage_roles")
            ? t("Rollar berish, ruxsatlarni boshqarish va hisoblarni faollashtirish")
            : t("Maktabingiz hisoblarini ko'rish va faollashtirish")
        }
      />

      <div className="mb-4 flex flex-wrap gap-3">
        <div className="w-full sm:w-80">
          <Input
            icon={<Search className="h-4 w-4" />}
            placeholder={t("Ism yoki login bo'yicha qidirish...")}
            value={search}
            onChange={(e) => {
              setSearch(e.target.value)
              setPage(1)
            }}
          />
        </div>
        <div className="w-full sm:w-56">
          <Select
            value={role}
            onChange={(e) => {
              setRole(e.target.value)
              setPage(1)
            }}
          >
            <option value="">{t("Barcha rollar")}</option>
            {ASSIGNABLE_ROLES.map((r) => (
              <option key={r} value={r}>
                {ROLE_LABELS[r]}
              </option>
            ))}
          </Select>
        </div>
      </div>

      <DataTable
        columns={columns}
        rows={data?.results ?? []}
        keyField={(u) => u.id}
        loading={loading}
        onRowClick={setSelected}
        emptyTitle={t("Foydalanuvchi topilmadi")}
      />
      {data && <Pagination page={page} count={data.count} pageSize={PAGE_SIZE} onChange={setPage} />}

      <AccessDrawer user={selected} onClose={() => setSelected(null)} onChanged={refetch} />
    </div>
  )
}

function AccessDrawer({
  user,
  onClose,
  onChanged,
}: {
  user: AdminUser | null
  onClose: () => void
  onChanged: () => void
}) {
  const { user: me, hasRole, can } = useAccess()
  const isSuperadmin = hasRole("SUPERADMIN")
  const isSelf = !!user && !!me && user.id === me.id
  // Roles and global permissions are the SuperAdmin's; a school admin only sees them and blocks / unblocks
  // the accounts of its own school (never another administrator's).
  const canRoles = can("manage_roles")
  const canPermissions = can("manage_permissions")
  const canDelete = can("delete_users") && !isSelf
  const targetIsAdministrator = !!user && (user.roles.includes("ADMIN") || user.roles.includes("SUPERADMIN"))
  const canBlock = !isSelf && (isSuperadmin || !targetIsAdministrator)
  const [confirmDelete, setConfirmDelete] = useState(false)

  const { data: access, loading, refetch } = useFetch<AccessInfo>(user ? `/users/${user.id}/access/` : null)
  const { data: catalogue } = useFetch<PermissionDef[]>(user && canPermissions ? "/permissions/" : null)
  const [newRole, setNewRole] = useState("")
  const [primary, setPrimary] = useState("")
  const [newPermission, setNewPermission] = useState("")
  const [busy, setBusy] = useState(false)

  // Only a SUPERADMIN may hand out the SUPERADMIN role and the system-level permissions.
  const grantableRoles = ASSIGNABLE_ROLES.filter((r) => isSuperadmin || r !== "SUPERADMIN")
  const grantablePermissions = (catalogue ?? []).filter((p) => isSuperadmin || !p.system)
  const description = new Map((catalogue ?? []).map((p) => [p.codename, p.description]))

  async function run(action: () => Promise<unknown>, success: string) {
    setBusy(true)
    try {
      await action()
      toast.success(success)
      refetch()
      onChanged()
    } catch (err) {
      toast.error(getErrorMessage(err))
    } finally {
      setBusy(false)
    }
  }

  const grantRole = (role: string, asPrimary: boolean) =>
    run(() => api.post(`/users/${user!.id}/roles/`, { role, primary: asPrimary }), t("Rol saqlandi"))
  const revokeRole = (role: string) => run(() => api.delete(`/users/${user!.id}/roles/${role}/`), t("Rol olib tashlandi"))
  const grantPermission = (code: string) =>
    run(() => api.post(`/users/${user!.id}/permissions/`, { permission: code }), t("Ruxsat berildi"))
  const revokePermission = (code: string) =>
    run(() => api.delete(`/users/${user!.id}/permissions/${code}/`), t("Ruxsat olib tashlandi"))
  const deleteAccount = async () => {
    setBusy(true)
    try {
      await api.delete(`/users/${user!.id}/`)
      toast.success(t("Hisob o'chirildi"))
      setConfirmDelete(false)
      onChanged()
      onClose()
    } catch (err) {
      toast.error(getErrorMessage(err))
    } finally {
      setBusy(false)
    }
  }
  const toggleActive = () =>
    run(
      () => api.post(`/auth/users/${user!.id}/${user!.is_active ? "deactivate" : "activate"}/`),
      user!.is_active ? t("Hisob faolsizlantirildi") : t("Hisob faollashtirildi")
    )

  const grouped = new Map<string, string[]>()
  for (const code of access?.permissions ?? []) {
    const category = catalogue?.find((p) => p.codename === code)?.category ?? "own"
    grouped.set(category, [...(grouped.get(category) ?? []), code])
  }

  return (
    <Drawer open={!!user} onClose={onClose} title={user ? fullName(user) : ""} subtitle={user ? `@${user.username}` : undefined}>
      {loading || !access || !user ? (
        <Skeleton className="h-48 w-full" />
      ) : (
        <div className="space-y-6">
          {isSelf && (
            <p className="rounded-2xl bg-amber-500/10 px-4 py-3 text-xs text-amber-600 dark:text-amber-400">
              {t("O'z rolingiz va ruxsatlaringizni o'zgartira olmaysiz.")}
            </p>
          )}

          {!canRoles && (
            <section>
              <p className="eyebrow mb-2 text-ink-400">{t("Rollar")}</p>
              <div className="flex flex-wrap gap-2">
                {access.roles.map((r, i) => (
                  <Badge key={r} tone={i === 0 ? "brand" : "info"}>
                    {ROLE_LABELS[r]}
                  </Badge>
                ))}
              </div>
              <p className="mt-2 text-xs text-ink-400">{t("Rollarni faqat SuperAdmin o'zgartira oladi.")}</p>
            </section>
          )}

          {canRoles && (
          <section>
            <p className="eyebrow mb-2 text-ink-400">{t("Asosiy rol")}</p>
            <div className="flex gap-2">
              <Select value={primary || access.primary_role} onChange={(e) => setPrimary(e.target.value)} disabled={isSelf}>
                {grantableRoles.map((r) => (
                  <option key={r} value={r}>
                    {ROLE_LABELS[r]}
                  </option>
                ))}
              </Select>
              <Button
                variant="outline"
                disabled={isSelf || busy || !primary || primary === access.primary_role}
                onClick={() => grantRole(primary, true)}
              >
                {t("Belgilash")}
              </Button>
            </div>
          </section>
          )}

          {canRoles && (
          <section>
            <p className="eyebrow mb-2 text-ink-400">{t("Qo'shimcha rollar")}</p>
            <div className="mb-3 flex flex-wrap gap-2">
              {access.extra_roles.length === 0 && <span className="text-sm text-ink-400">—</span>}
              {access.extra_roles.map((r) => (
                <Chip key={r} label={ROLE_LABELS[r]} disabled={isSelf || busy} onRemove={() => revokeRole(r)} />
              ))}
              {access.roles.includes("CLASS_TEACHER") && (
                <Badge tone="info" title={t("Sinfga rahbar sifatida biriktirilganda avtomatik hosil bo'ladi")}>
                  {ROLE_LABELS.CLASS_TEACHER} · {access.curated_classes.map((c) => c.name).join(", ")}
                </Badge>
              )}
            </div>
            <div className="flex gap-2">
              <Select value={newRole} onChange={(e) => setNewRole(e.target.value)} disabled={isSelf}>
                <option value="">{t("Rol tanlang...")}</option>
                {grantableRoles
                  .filter((r) => r !== access.primary_role && !access.extra_roles.includes(r))
                  .map((r) => (
                    <option key={r} value={r}>
                      {ROLE_LABELS[r]}
                    </option>
                  ))}
              </Select>
              <Button
                disabled={isSelf || busy || !newRole}
                onClick={() => {
                  void grantRole(newRole, false)
                  setNewRole("")
                }}
              >
                {t("Qo'shish")}
              </Button>
            </div>
          </section>
          )}

          {canPermissions && (
          <section>
            <p className="eyebrow mb-2 text-ink-400">{t("Alohida ruxsatlar")}</p>
            <p className="mb-3 text-xs text-ink-400">
              {t("Rol ruxsatlariga qo'shimcha ravishda faqat shu foydalanuvchiga beriladi.")}
            </p>
            <div className="mb-3 flex flex-wrap gap-2">
              {access.extra_permissions.length === 0 && <span className="text-sm text-ink-400">—</span>}
              {access.extra_permissions.map((p) => (
                <Chip key={p} label={p} title={description.get(p)} disabled={isSelf || busy} onRemove={() => revokePermission(p)} />
              ))}
            </div>
            <div className="flex gap-2">
              <Select value={newPermission} onChange={(e) => setNewPermission(e.target.value)} disabled={isSelf}>
                <option value="">{t("Ruxsat tanlang...")}</option>
                {grantablePermissions
                  .filter((p) => !access.permissions.includes(p.codename))
                  .map((p) => (
                    <option key={p.codename} value={p.codename}>
                      {p.description}
                    </option>
                  ))}
              </Select>
              <Button
                disabled={isSelf || busy || !newPermission}
                onClick={() => {
                  void grantPermission(newPermission)
                  setNewPermission("")
                }}
              >
                {t("Berish")}
              </Button>
            </div>
          </section>
          )}

          <section>
            <p className="eyebrow mb-2 flex items-center gap-1.5 text-ink-400">
              <ShieldCheck className="h-3.5 w-3.5" /> {t("Amaldagi ruxsatlar")} ({access.permissions.length})
            </p>
            <div className="space-y-3">
              {[...grouped.entries()].map(([category, codes]) => (
                <div key={category}>
                  <p className="mb-1 text-xs font-medium text-ink-500 dark:text-ink-400">{CATEGORY_LABELS[category] ?? category}</p>
                  <div className="flex flex-wrap gap-1.5">
                    {codes.map((c) => (
                      <span
                        key={c}
                        title={description.get(c)}
                        className="rounded-full bg-ink-100 px-2.5 py-1 text-[11px] text-ink-600 dark:bg-ink-800 dark:text-ink-300"
                      >
                        {c}
                      </span>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </section>

          {!canBlock && !isSelf && (
            <p className="rounded-2xl bg-ink-100 px-4 py-3 text-xs text-ink-500 dark:bg-ink-800 dark:text-ink-300">
              {t("Adminlarni faqat SuperAdmin boshqara oladi.")}
            </p>
          )}

          <Button variant={user.is_active ? "danger" : "primary"} className="w-full" disabled={!canBlock || busy} onClick={toggleActive}>
            {user.is_active ? t("Hisobni faolsizlantirish") : t("Hisobni faollashtirish")}
          </Button>

          {canDelete && !access.roles.includes("SUPERADMIN") && (
            <Button
              variant={confirmDelete ? "danger" : "outline"}
              className="w-full"
              disabled={busy}
              onClick={() => (confirmDelete ? deleteAccount() : setConfirmDelete(true))}
              onBlur={() => setConfirmDelete(false)}
            >
              <Trash2 className="h-4 w-4" /> {confirmDelete ? t("Ishonchingiz komilmi? Hisob butunlay o'chadi") : t("Hisobni o'chirish")}
            </Button>
          )}
        </div>
      )}
    </Drawer>
  )
}

function Chip({
  label,
  title,
  disabled,
  onRemove,
}: {
  label: string
  title?: string
  disabled?: boolean
  onRemove: () => void
}) {
  return (
    <span
      title={title}
      className="inline-flex items-center gap-1.5 rounded-full bg-brand-500/15 py-1 pl-3 pr-1.5 text-xs font-medium text-brand-600 dark:text-brand-300"
    >
      {label}
      <button
        type="button"
        disabled={disabled}
        onClick={onRemove}
        aria-label={t("Olib tashlash")}
        className="flex h-5 w-5 items-center justify-center rounded-full hover:bg-brand-500/25 disabled:opacity-40"
      >
        <X className="h-3 w-3" />
      </button>
    </span>
  )
}
