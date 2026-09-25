import { type FormEvent, useEffect, useMemo, useState } from "react"
import axios from "axios"
import { Plus, Search, Trash2 } from "lucide-react"
import toast from "react-hot-toast"
import { useFetch } from "../hooks/useFetch"
import { api, getErrorMessage } from "../lib/api"
import { PageHeader } from "../components/ui/PageHeader"
import { Button } from "../components/ui/Button"
import { ConfirmButton } from "../components/ui/ConfirmButton"
import { Field, Input } from "../components/ui/Input"
import { Modal } from "../components/ui/Modal"
import { PhoneInput, isPhoneComplete } from "../components/ui/PhoneInput"
import { DataTable, type Column } from "../components/ui/Table"
import type { Paginated, School, SystemAnalytics } from "../types"
import { t } from "../i18n"

interface Dependents {
  classes: number
  students: number
  teachers: number
  users: number
}

/**
 * Maktablar — the SuperAdmin's school register: add, edit and delete schools. Deleting one that still
 * has classes, pupils, teachers or accounts first shows what would be lost and needs a second,
 * explicit confirmation (the API answers 409 until ``?force=true``).
 */
export default function SchoolsPage() {
  const [search, setSearch] = useState("")
  const [editing, setEditing] = useState<School | null>(null)
  const [creating, setCreating] = useState(false)

  const { data, loading, refetch } = useFetch<Paginated<School>>(
    `/schools/?page_size=100${search ? `&search=${encodeURIComponent(search)}` : ""}`,
    [search]
  )
  const { data: stats, refetch: refetchStats } = useFetch<SystemAnalytics>("/analytics/system/")
  const statsById = useMemo(() => new Map((stats?.schools ?? []).map((s) => [s.id, s])), [stats])

  const columns: Column<School>[] = [
    {
      key: "name",
      header: t("Maktab"),
      render: (s) => (
        <div className="min-w-0">
          <p className="truncate font-medium text-ink-800 dark:text-ink-100">{s.name}</p>
          <p className="truncate text-xs text-ink-400">{s.address || "—"}</p>
        </div>
      ),
    },
    { key: "phone", header: t("Telefon"), render: (s) => s.phone || "—", hideOnMobile: true },
    { key: "email", header: t("Email"), render: (s) => s.email || "—", hideOnMobile: true },
    { key: "students", header: t("O'quvchilar"), render: (s) => statsById.get(s.id)?.students ?? "…" },
    { key: "teachers", header: t("O'qituvchilar"), render: (s) => statsById.get(s.id)?.teachers ?? "…", hideOnMobile: true },
    { key: "admins", header: t("Adminlar"), render: (s) => statsById.get(s.id)?.admins ?? "…" },
  ]

  function done() {
    setEditing(null)
    setCreating(false)
    refetch()
    refetchStats()
  }

  return (
    <div>
      <PageHeader
        title={t("Maktablar")}
        description={t("Tizimdagi barcha maktablar")}
        actions={
          <Button onClick={() => setCreating(true)}>
            <Plus className="h-4 w-4" /> {t("Yangi maktab")}
          </Button>
        }
      />

      <div className="mb-4 max-w-xs">
        <Input
          icon={<Search className="h-4 w-4" />}
          placeholder={t("Nomi yoki manzili bo'yicha qidirish...")}
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
      </div>

      <DataTable
        columns={columns}
        rows={data?.results ?? []}
        keyField={(s) => s.id}
        loading={loading}
        emptyTitle={t("Maktab topilmadi")}
        onRowClick={setEditing}
      />

      <SchoolModal school={editing} creating={creating} onClose={() => { setEditing(null); setCreating(false) }} onDone={done} />
    </div>
  )
}

function SchoolModal({
  school,
  creating,
  onClose,
  onDone,
}: {
  school: School | null
  creating: boolean
  onClose: () => void
  onDone: () => void
}) {
  const open = creating || !!school
  const [form, setForm] = useState({ name: "", address: "", phone: "", email: "" })
  const [loading, setLoading] = useState(false)
  const [dependents, setDependents] = useState<Dependents | null>(null)

  useEffect(() => {
    if (!open) return
    setForm({ name: school?.name ?? "", address: school?.address ?? "", phone: school?.phone ?? "", email: school?.email ?? "" })
    setDependents(null)
  }, [open, school])

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    if (!isPhoneComplete(form.phone)) return toast.error(t("Telefon raqami to'liq emas"))
    setLoading(true)
    try {
      if (school) await api.patch(`/schools/${school.id}/`, form)
      else await api.post("/schools/", form)
      toast.success(school ? t("Maktab yangilandi") : t("Maktab qo'shildi"))
      onDone()
    } catch (err) {
      toast.error(getErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  async function remove(force: boolean) {
    if (!school) return
    setLoading(true)
    try {
      await api.delete(`/schools/${school.id}/${force ? "?force=true" : ""}`)
      toast.success(t("Maktab o'chirildi"))
      onDone()
    } catch (err) {
      if (axios.isAxiosError(err) && err.response?.status === 409) {
        // still has data: show what would be lost and ask once more
        setDependents((err.response.data as { errors: { dependents: Dependents } }).errors.dependents)
      } else {
        toast.error(getErrorMessage(err))
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <Modal open={open} onClose={onClose} title={school ? school.name : t("Yangi maktab")}>
      <form onSubmit={handleSubmit} className="space-y-4">
        <Field label={t("Nomi")}>
          <Input value={form.name} onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))} required />
        </Field>
        <Field label={t("Manzil")}>
          <Input value={form.address} onChange={(e) => setForm((f) => ({ ...f, address: e.target.value }))} />
        </Field>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <Field label={t("Telefon")}>
            <PhoneInput value={form.phone} onChange={(phone) => setForm((f) => ({ ...f, phone }))} />
          </Field>
          <Field label={t("Email")}>
            <Input type="email" value={form.email} onChange={(e) => setForm((f) => ({ ...f, email: e.target.value }))} />
          </Field>
        </div>
        <Button type="submit" className="w-full" loading={loading && !dependents}>
          {t("Saqlash")}
        </Button>
      </form>

      {school && (
        <div className="mt-5 border-t border-ink-100 pt-4 dark:border-ink-800">
          {dependents ? (
            <div className="space-y-3 rounded-2xl bg-rose-500/10 p-4 text-sm text-rose-700 dark:text-rose-300">
              <p className="font-semibold">{t("Maktabda hali ma'lumotlar bor:")}</p>
              <p>
                {t("{classes} sinf, {students} o'quvchi, {teachers} o'qituvchi, {users} hisob", dependents as unknown as Record<string, number>)}
              </p>
              <p className="text-xs">{t("O'chirilsa sinflar va ularning darslari, davomati, baholari yo'qoladi; hisoblar maktabsiz qoladi.")}</p>
              <Button variant="danger" className="w-full" loading={loading} onClick={() => remove(true)}>
                <Trash2 className="h-4 w-4" /> {t("Baribir o'chirish")}
              </Button>
            </div>
          ) : (
            <ConfirmButton
              className="w-full"
              label={t("Maktabni o'chirish")}
              confirmLabel={t("Ishonchingiz komilmi?")}
              icon={<Trash2 className="h-4 w-4" />}
              disabled={loading}
              onConfirm={() => remove(false)}
            />
          )}
        </div>
      )}
    </Modal>
  )
}
