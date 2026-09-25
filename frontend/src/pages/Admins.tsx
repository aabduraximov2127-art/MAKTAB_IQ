import { type FormEvent, useEffect, useMemo, useState } from "react"
import { Plus, Search, Trash2 } from "lucide-react"
import toast from "react-hot-toast"
import { useFetch } from "../hooks/useFetch"
import { api, getErrorMessage } from "../lib/api"
import { fullName } from "../lib/format"
import { PageHeader } from "../components/ui/PageHeader"
import { Avatar } from "../components/ui/Avatar"
import { Badge } from "../components/ui/Badge"
import { Button } from "../components/ui/Button"
import { ConfirmButton } from "../components/ui/ConfirmButton"
import { Drawer } from "../components/ui/Drawer"
import { Field, Input } from "../components/ui/Input"
import { Modal } from "../components/ui/Modal"
import { Pagination } from "../components/ui/Pagination"
import { PhoneInput, isPhoneComplete } from "../components/ui/PhoneInput"
import { Select } from "../components/ui/Select"
import { DataTable, type Column } from "../components/ui/Table"
import type { AdminAccount, Paginated, School } from "../types"
import { t } from "../i18n"

const PAGE_SIZE = 15

/**
 * Adminlar — the SuperAdmin creates, edits, blocks and deletes school administrators and assigns
 * each one to a school. (The API only accepts administrator accounts here and never lets a role,
 * login or password be edited through it.)
 */
export default function AdminsPage() {
  const [search, setSearch] = useState("")
  const [school, setSchool] = useState("")
  const [page, setPage] = useState(1)
  const [selected, setSelected] = useState<AdminAccount | null>(null)
  const [creating, setCreating] = useState(false)

  const { data: schools } = useFetch<Paginated<School>>("/schools/?page_size=100")
  const schoolName = useMemo(() => new Map((schools?.results ?? []).map((s) => [s.id, s.name])), [schools])

  const query = new URLSearchParams({ role: "ADMIN", page: String(page), page_size: String(PAGE_SIZE) })
  if (search) query.set("search", search)
  if (school) query.set("school", school)
  const { data, loading, refetch } = useFetch<Paginated<AdminAccount>>(`/users/?${query.toString()}`, [page, search, school])

  const columns: Column<AdminAccount>[] = [
    {
      key: "admin",
      header: t("Admin"),
      render: (a) => (
        <div className="flex items-center gap-3">
          <Avatar name={fullName(a)} size="sm" />
          <div className="min-w-0">
            <p className="truncate font-medium text-ink-800 dark:text-ink-100">{fullName(a)}</p>
            <p className="truncate text-xs text-ink-400">@{a.username}</p>
          </div>
        </div>
      ),
    },
    { key: "school", header: t("Maktab"), render: (a) => (a.school ? schoolName.get(a.school) ?? "…" : <Badge tone="warning">{t("Biriktirilmagan")}</Badge>) },
    { key: "phone", header: t("Telefon"), render: (a) => a.phone || "—", hideOnMobile: true },
    { key: "email", header: t("Email"), render: (a) => a.email || "—", hideOnMobile: true },
    {
      key: "status",
      header: t("Holat"),
      render: (a) => <Badge tone={a.is_active ? "success" : "danger"}>{a.is_active ? t("Faol") : t("Bloklangan")}</Badge>,
    },
  ]

  return (
    <div>
      <PageHeader
        title={t("Adminlar")}
        description={t("Maktab adminlarini yaratish, tahrirlash, bloklash va maktabga biriktirish")}
        actions={
          <Button onClick={() => setCreating(true)}>
            <Plus className="h-4 w-4" /> {t("Yangi admin")}
          </Button>
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
            value={school}
            onChange={(e) => {
              setSchool(e.target.value)
              setPage(1)
            }}
          >
            <option value="">{t("Barcha maktablar")}</option>
            {schools?.results.map((s) => (
              <option key={s.id} value={s.id}>
                {s.name}
              </option>
            ))}
          </Select>
        </div>
      </div>

      <DataTable
        columns={columns}
        rows={data?.results ?? []}
        keyField={(a) => a.id}
        loading={loading}
        emptyTitle={t("Admin topilmadi")}
        onRowClick={setSelected}
      />
      {data && <Pagination page={page} count={data.count} pageSize={PAGE_SIZE} onChange={setPage} />}

      <CreateAdminModal
        open={creating}
        schools={schools?.results ?? []}
        onClose={() => setCreating(false)}
        onDone={() => {
          setCreating(false)
          refetch()
        }}
      />
      <AdminDrawer
        admin={selected}
        schools={schools?.results ?? []}
        onClose={() => setSelected(null)}
        onChanged={() => {
          refetch()
        }}
        onDeleted={() => {
          setSelected(null)
          refetch()
        }}
      />
    </div>
  )
}

/* --------------------------------- create --------------------------------- */

function CreateAdminModal({ open, schools, onClose, onDone }: { open: boolean; schools: School[]; onClose: () => void; onDone: () => void }) {
  const empty = { username: "", password: "", first_name: "", last_name: "", phone: "", email: "", school: "" }
  const [form, setForm] = useState(empty)
  const [loading, setLoading] = useState(false)
  const set = (key: keyof typeof empty, value: string) => setForm((f) => ({ ...f, [key]: value }))

  useEffect(() => {
    if (open) setForm(empty)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open])

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    if (!isPhoneComplete(form.phone)) return toast.error(t("Telefon raqami to'liq emas"))
    setLoading(true)
    try {
      await api.post("/users/", form)
      toast.success(t("Admin yaratildi"))
      onDone()
    } catch (err) {
      toast.error(getErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  return (
    <Modal open={open} onClose={onClose} title={t("Yangi admin")} size="lg">
      <form onSubmit={handleSubmit} className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <Field label={t("Ism")}>
          <Input value={form.first_name} onChange={(e) => set("first_name", e.target.value)} required />
        </Field>
        <Field label={t("Familiya")}>
          <Input value={form.last_name} onChange={(e) => set("last_name", e.target.value)} required />
        </Field>
        <Field label={t("Login")}>
          <Input value={form.username} onChange={(e) => set("username", e.target.value)} autoComplete="off" required />
        </Field>
        <Field label={t("Parol")}>
          <Input type="password" value={form.password} onChange={(e) => set("password", e.target.value)} autoComplete="new-password" required />
        </Field>
        <Field label={t("Telefon")}>
          <PhoneInput value={form.phone} onChange={(phone) => set("phone", phone)} />
        </Field>
        <Field label={t("Email")}>
          <Input type="email" value={form.email} onChange={(e) => set("email", e.target.value)} />
        </Field>
        <Field label={t("Maktab")} className="sm:col-span-2">
          <Select value={form.school} onChange={(e) => set("school", e.target.value)} required>
            <option value="">{t("Tanlang...")}</option>
            {schools.map((s) => (
              <option key={s.id} value={s.id}>
                {s.name}
              </option>
            ))}
          </Select>
        </Field>
        <Button type="submit" className="sm:col-span-2" loading={loading}>
          {t("Yaratish")}
        </Button>
      </form>
    </Modal>
  )
}

/* ---------------------------------- edit ---------------------------------- */

function AdminDrawer({
  admin,
  schools,
  onClose,
  onChanged,
  onDeleted,
}: {
  admin: AdminAccount | null
  schools: School[]
  onClose: () => void
  onChanged: () => void
  onDeleted: () => void
}) {
  const [form, setForm] = useState({ first_name: "", last_name: "", phone: "", email: "", school: "" })
  const [active, setActive] = useState(true)
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    if (!admin) return
    setForm({ first_name: admin.first_name, last_name: admin.last_name, phone: admin.phone, email: admin.email, school: admin.school ? String(admin.school) : "" })
    setActive(admin.is_active)
  }, [admin])

  async function save(e: FormEvent) {
    e.preventDefault()
    if (!admin) return
    if (!isPhoneComplete(form.phone)) return toast.error(t("Telefon raqami to'liq emas"))
    setBusy(true)
    try {
      await api.patch(`/users/${admin.id}/`, form)
      toast.success(t("Admin yangilandi"))
      onChanged()
    } catch (err) {
      toast.error(getErrorMessage(err))
    } finally {
      setBusy(false)
    }
  }

  async function toggleBlock() {
    if (!admin) return
    setBusy(true)
    try {
      await api.post(`/auth/users/${admin.id}/${active ? "deactivate" : "activate"}/`)
      toast.success(active ? t("Admin bloklandi") : t("Admin faollashtirildi"))
      setActive(!active)
      onChanged()
    } catch (err) {
      toast.error(getErrorMessage(err))
    } finally {
      setBusy(false)
    }
  }

  async function remove() {
    if (!admin) return
    setBusy(true)
    try {
      await api.delete(`/users/${admin.id}/`)
      toast.success(t("Hisob o'chirildi"))
      onDeleted()
    } catch (err) {
      toast.error(getErrorMessage(err))
    } finally {
      setBusy(false)
    }
  }

  return (
    <Drawer open={!!admin} onClose={onClose} title={admin ? fullName(admin) : ""} subtitle={admin ? `@${admin.username}` : undefined}>
      {admin && (
        <div className="space-y-6">
          <form onSubmit={save} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <Field label={t("Ism")}>
                <Input value={form.first_name} onChange={(e) => setForm((f) => ({ ...f, first_name: e.target.value }))} required />
              </Field>
              <Field label={t("Familiya")}>
                <Input value={form.last_name} onChange={(e) => setForm((f) => ({ ...f, last_name: e.target.value }))} required />
              </Field>
            </div>
            <Field label={t("Telefon")}>
              <PhoneInput value={form.phone} onChange={(phone) => setForm((f) => ({ ...f, phone }))} />
            </Field>
            <Field label={t("Email")}>
              <Input type="email" value={form.email} onChange={(e) => setForm((f) => ({ ...f, email: e.target.value }))} />
            </Field>
            <Field label={t("Maktab")}>
              <Select value={form.school} onChange={(e) => setForm((f) => ({ ...f, school: e.target.value }))} required>
                <option value="">{t("Tanlang...")}</option>
                {schools.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.name}
                  </option>
                ))}
              </Select>
            </Field>
            <Button type="submit" className="w-full" loading={busy}>
              {t("Saqlash")}
            </Button>
          </form>

          <div className="space-y-3 border-t border-ink-100 pt-5 dark:border-ink-800">
            <Button variant={active ? "danger" : "primary"} className="w-full" disabled={busy} onClick={toggleBlock}>
              {active ? t("Adminni bloklash") : t("Adminni faollashtirish")}
            </Button>
            <ConfirmButton
              className="w-full"
              label={t("Adminni o'chirish")}
              confirmLabel={t("Ishonchingiz komilmi? Hisob butunlay o'chadi")}
              icon={<Trash2 className="h-4 w-4" />}
              disabled={busy}
              onConfirm={remove}
            />
          </div>
        </div>
      )}
    </Drawer>
  )
}
