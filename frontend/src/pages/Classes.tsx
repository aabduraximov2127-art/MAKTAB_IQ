import { type FormEvent, useEffect, useState } from "react"
import { motion } from "framer-motion"
import { Plus, School, Trash2, Users } from "lucide-react"
import toast from "react-hot-toast"
import { useFetch } from "../hooks/useFetch"
import { api, getErrorMessage } from "../lib/api"
import { useAccess } from "../lib/access"
import { PageHeader } from "../components/ui/PageHeader"
import { Button } from "../components/ui/Button"
import { ConfirmButton } from "../components/ui/ConfirmButton"
import { Card, CardContent } from "../components/ui/Card"
import { Field, Input } from "../components/ui/Input"
import { Select } from "../components/ui/Select"
import { Modal } from "../components/ui/Modal"
import { Drawer } from "../components/ui/Drawer"
import { EmptyState } from "../components/ui/EmptyState"
import { CardSkeleton } from "../components/ui/Skeleton"
import { Avatar } from "../components/ui/Avatar"
import { fullName } from "../lib/format"
import type { AcademicYear, ClassRoom, Paginated, School as SchoolType, StudentProfile, TeacherProfile } from "../types"
import { t } from "../i18n"

export default function ClassesPage() {
  const { can } = useAccess()
  const isAdmin = can("manage_classes")
  const [addOpen, setAddOpen] = useState(false)
  const [selected, setSelected] = useState<ClassRoom | null>(null)

  const { data, loading, refetch } = useFetch<Paginated<ClassRoom>>("/classes/?page_size=100")

  return (
    <div>
      <PageHeader
        title={t("Sinflar")}
        description={t("Maktabdagi barcha sinflar")}
        actions={
          isAdmin && (
            <Button onClick={() => setAddOpen(true)}>
              <Plus className="h-4 w-4" /> Yangi sinf
            </Button>
          )
        }
      />

      {loading ? (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <CardSkeleton key={i} />
          ))}
        </div>
      ) : !data || data.results.length === 0 ? (
        <EmptyState icon={School} title={t("Sinf topilmadi")} />
      ) : (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {data.results.map((c, i) => (
            <motion.div
              key={c.id}
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.04 }}
            >
              <Card
                className="cursor-pointer transition-transform hover:-translate-y-0.5 hover:shadow-soft-lg"
                onClick={() => setSelected(c)}
              >
                <CardContent>
                  <div className="flex items-start justify-between">
                    <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-gradient-to-br from-brand-500 to-brand-700 font-display text-lg font-bold text-white">
                      {c.name}
                    </div>
                    <span className="rounded-full bg-ink-100 px-2.5 py-1 text-xs font-medium text-ink-600 dark:bg-ink-800 dark:text-ink-300">
                      {c.grade}-sinf
                    </span>
                  </div>
                  <p className="mt-3 text-sm text-ink-500 dark:text-ink-400">
                    Curator: <span className="font-medium text-ink-700 dark:text-ink-200">{c.curator_name ?? t("Biriktirilmagan")}</span>
                  </p>
                  <div className="mt-3 flex items-center gap-1.5 text-sm text-ink-600 dark:text-ink-300">
                    <Users className="h-4 w-4 text-brand-500" /> {c.student_count} o'quvchi
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          ))}
        </div>
      )}

      <ClassDetailDrawer
        classRoom={selected}
        canManage={isAdmin}
        onClose={() => setSelected(null)}
        onChanged={() => {
          setSelected(null)
          refetch()
        }}
      />
      <AddClassModal open={addOpen} onClose={() => setAddOpen(false)} onDone={() => { setAddOpen(false); refetch() }} />
    </div>
  )
}

function ClassDetailDrawer({
  classRoom,
  canManage,
  onClose,
  onChanged,
}: {
  classRoom: ClassRoom | null
  canManage: boolean
  onClose: () => void
  onChanged: () => void
}) {
  const { data: students, loading } = useFetch<Paginated<StudentProfile>>(
    classRoom ? `/students/?class_room=${classRoom.id}&page_size=100` : null
  )

  return (
    <Drawer open={!!classRoom} onClose={onClose} title={classRoom?.name} subtitle={t("{grade}-sinf • {count} o'quvchi", { grade: classRoom?.grade ?? "", count: classRoom?.student_count ?? 0 })}>
      {loading ? (
        <div className="space-y-2">
          {Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="h-12 animate-pulse rounded-xl bg-ink-100 dark:bg-ink-800" />
          ))}
        </div>
      ) : !students || students.results.length === 0 ? (
        <>
          {canManage && classRoom && <EditClassForm classRoom={classRoom} onChanged={onChanged} />}
          <EmptyState title={t("O'quvchi yo'q")} />
        </>
      ) : (
        <div className="space-y-2">
          {canManage && classRoom && <EditClassForm classRoom={classRoom} onChanged={onChanged} />}
          {students.results.map((s) => (
            <div key={s.id} className="flex items-center gap-3 rounded-xl border border-ink-100 p-3 dark:border-ink-800">
              <Avatar name={fullName(s.user)} src={s.photo} size="sm" />
              <div>
                <p className="text-sm font-medium text-ink-800 dark:text-ink-100">{fullName(s.user)}</p>
                <p className="text-xs text-ink-400">{s.student_code}</p>
              </div>
            </div>
          ))}
        </div>
      )}
    </Drawer>
  )
}

/** Rename a class, change its grade, assign its curator (class teacher) or delete it. */
function EditClassForm({ classRoom, onChanged }: { classRoom: ClassRoom; onChanged: () => void }) {
  const { data: teachers } = useFetch<Paginated<TeacherProfile>>("/teachers/?page_size=100")
  const [form, setForm] = useState({ name: classRoom.name, grade: String(classRoom.grade), curator: classRoom.curator ? String(classRoom.curator) : "" })
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    setForm({ name: classRoom.name, grade: String(classRoom.grade), curator: classRoom.curator ? String(classRoom.curator) : "" })
  }, [classRoom])

  async function save(e: FormEvent) {
    e.preventDefault()
    setLoading(true)
    try {
      await api.patch(`/classes/${classRoom.id}/`, { name: form.name, grade: Number(form.grade), curator: form.curator ? Number(form.curator) : null })
      toast.success(t("Sinf yangilandi"))
      onChanged()
    } catch (err) {
      toast.error(getErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  async function remove() {
    setLoading(true)
    try {
      await api.delete(`/classes/${classRoom.id}/`)
      toast.success(t("Sinf o'chirildi"))
      onChanged()
    } catch (err) {
      toast.error(getErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  return (
    <form onSubmit={save} className="mb-5 space-y-3 rounded-2xl border border-ink-100 p-4 dark:border-ink-800">
      <div className="grid grid-cols-2 gap-3">
        <Field label={t("Nomi")}>
          <Input value={form.name} onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))} required />
        </Field>
        <Field label={t("Sinf raqami")}>
          <Input type="number" min={1} max={11} value={form.grade} onChange={(e) => setForm((f) => ({ ...f, grade: e.target.value }))} required />
        </Field>
      </div>
      <Field label={t("Sinf rahbari")}>
        <Select value={form.curator} onChange={(e) => setForm((f) => ({ ...f, curator: e.target.value }))}>
          <option value="">{t("Biriktirilmagan")}</option>
          {teachers?.results.map((tp) => (
            <option key={tp.id} value={tp.id}>
              {fullName(tp.user)}
            </option>
          ))}
        </Select>
      </Field>
      <Button type="submit" className="w-full" loading={loading}>
        {t("Saqlash")}
      </Button>
      <ConfirmButton
        className="w-full"
        label={t("Sinfni o'chirish")}
        confirmLabel={t("Ishonchingiz komilmi? Darslar va davomat ham o'chadi")}
        icon={<Trash2 className="h-4 w-4" />}
        disabled={loading}
        onConfirm={remove}
      />
    </form>
  )
}

function AddClassModal({ open, onClose, onDone }: { open: boolean; onClose: () => void; onDone: () => void }) {
  const { data: schools } = useFetch<Paginated<SchoolType>>(open ? "/schools/?page_size=100" : null)
  const { data: years } = useFetch<Paginated<AcademicYear>>(open ? "/classes/academic-years/?page_size=100" : null)
  const [form, setForm] = useState({ school: "", name: "", grade: "", academic_year: "" })
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setLoading(true)
    try {
      await api.post("/classes/", form)
      toast.success(t("Sinf yaratildi"))
      setForm({ school: "", name: "", grade: "", academic_year: "" })
      onDone()
    } catch (err) {
      toast.error(getErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  return (
    <Modal open={open} onClose={onClose} title={t("Yangi sinf yaratish")}>
      <form onSubmit={handleSubmit} className="space-y-4">
        <Field label={t("Maktab")}>
          <Select value={form.school} onChange={(e) => setForm((f) => ({ ...f, school: e.target.value }))} required>
            <option value="">{t("Tanlang...")}</option>
            {schools?.results.map((s) => (
              <option key={s.id} value={s.id}>
                {s.name}
              </option>
            ))}
          </Select>
        </Field>
        <div className="grid grid-cols-2 gap-4">
          <Field label={t("Nomi (masalan 9-A)")}>
            <Input value={form.name} onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))} required />
          </Field>
          <Field label={t("Sinf raqami")}>
            <Input type="number" min={1} max={11} value={form.grade} onChange={(e) => setForm((f) => ({ ...f, grade: e.target.value }))} required />
          </Field>
        </div>
        <Field label={t("O'quv yili")}>
          <Select value={form.academic_year} onChange={(e) => setForm((f) => ({ ...f, academic_year: e.target.value }))} required>
            <option value="">{t("Tanlang...")}</option>
            {years?.results.map((y) => (
              <option key={y.id} value={y.id}>
                {y.name}
              </option>
            ))}
          </Select>
        </Field>
        <Button type="submit" className="w-full" loading={loading}>
          {t("Yaratish")}
        </Button>
      </form>
    </Modal>
  )
}
