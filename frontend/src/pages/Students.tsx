import { type FormEvent, useState } from "react"
import { ArrowRightLeft, Pencil, Plus, Search, UserRound, Users } from "lucide-react"
import toast from "react-hot-toast"
import { useFetch } from "../hooks/useFetch"
import { api, getErrorMessage } from "../lib/api"
import { useAccess } from "../lib/access"
import { PageHeader } from "../components/ui/PageHeader"
import { Button } from "../components/ui/Button"
import { Field, Input } from "../components/ui/Input"
import { Select } from "../components/ui/Select"
import { PhoneInput, isPhoneComplete } from "../components/ui/PhoneInput"
import { DataTable, type Column } from "../components/ui/Table"
import { Pagination } from "../components/ui/Pagination"
import { Modal } from "../components/ui/Modal"
import { Drawer } from "../components/ui/Drawer"
import { Avatar } from "../components/ui/Avatar"
import { Badge } from "../components/ui/Badge"
import { EmptyState } from "../components/ui/EmptyState"
import { Skeleton } from "../components/ui/Skeleton"
import { ClassStudentPicker, type PickerSelection } from "../components/shared/ClassStudentPicker"
import { fullName, formatDate } from "../lib/format"
import type { ClassRoom, Paginated, School, StudentProfile, StudentProgress } from "../types"
import { t } from "../i18n"

const PAGE_SIZE = 10

export default function StudentsPage() {
  const { can, canAny, hasRole } = useAccess()
  // The director browses the school class by class: pick a class, then (optionally) a pupil.
  const isDirector = hasRole("DIRECTOR")
  const canManage = can("manage_students") // create / delete students
  const canTransfer = can("transfer_students")
  const canEdit = canAny("manage_students", "manage_class_students", "update_child_profile")

  const [search, setSearch] = useState("")
  const [page, setPage] = useState(1)
  const [addOpen, setAddOpen] = useState(false)
  const [selected, setSelected] = useState<StudentProfile | null>(null)
  const [transferOpen, setTransferOpen] = useState(false)
  const [editOpen, setEditOpen] = useState(false)

  const [picked, setPicked] = useState<PickerSelection>({ classRoom: null, student: null })
  const waitingForClass = isDirector && !picked.classRoom

  const query = new URLSearchParams({ page: String(page), page_size: String(PAGE_SIZE) })
  if (search) query.set("search", search)
  if (isDirector && picked.classRoom) query.set("class_room", String(picked.classRoom.id))

  const { data, loading, refetch } = useFetch<Paginated<StudentProfile>>(
    waitingForClass ? null : `/students/?${query.toString()}`,
    [page, search, picked.classRoom?.id]
  )

  const columns: Column<StudentProfile>[] = [
    {
      key: "name",
      header: t("O'quvchi"),
      render: (row) => (
        <div className="flex items-center gap-3">
          <Avatar name={fullName(row.user)} src={row.photo} size="sm" />
          <div className="min-w-0">
            <p className="truncate font-medium text-ink-800 dark:text-ink-100">{fullName(row.user)}</p>
            <p className="truncate text-xs text-ink-400">{row.student_code}</p>
          </div>
        </div>
      ),
    },
    { key: "class", header: t("Sinf"), render: (row) => row.class_room_name ?? <Badge tone="neutral">{t("Biriktirilmagan")}</Badge> },
    { key: "phone", header: t("Telefon"), render: (row) => row.user.phone || "—", hideOnMobile: true },
    { key: "email", header: t("Email"), render: (row) => row.user.email || "—", hideOnMobile: true },
    {
      key: "joined",
      header: t("Ro'yxatdan o'tgan"),
      render: (row) => formatDate(row.created_at),
      hideOnMobile: true,
    },
  ]

  return (
    <div>
      <PageHeader
        title={t("O'quvchilar")}
        description={t("Maktabdagi barcha o'quvchilar ro'yxati")}
        actions={
          canManage && (
            <Button onClick={() => setAddOpen(true)}>
              <Plus className="h-4 w-4" /> Yangi o'quvchi
            </Button>
          )
        }
      />

      {isDirector && (
        <ClassStudentPicker
          className="mb-4"
          onChange={(selection) => {
            setPicked(selection)
            setPage(1)
            setSearch("")
            if (selection.student) setSelected(selection.student)
          }}
        />
      )}

      {waitingForClass ? (
        <EmptyState
          icon={Users}
          title={t("Sinfni tanlang")}
          description={t("O'quvchilarni ko'rish uchun avval sinfni tanlang")}
        />
      ) : (
        <>
          <div className="mb-4 max-w-xs">
            <Input
              icon={<Search className="h-4 w-4" />}
              placeholder={t("Ism yoki familiya bo'yicha qidirish...")}
              value={search}
              onChange={(e) => {
                setSearch(e.target.value)
                setPage(1)
              }}
            />
          </div>

          <DataTable
            columns={columns}
            rows={data?.results ?? []}
            keyField={(r) => r.id}
            loading={loading}
            emptyTitle={t("O'quvchi topilmadi")}
            emptyDescription={t("Qidiruv shartlariga mos o'quvchi yo'q")}
            onRowClick={setSelected}
          />

          {data && <Pagination page={page} count={data.count} pageSize={PAGE_SIZE} onChange={setPage} />}
        </>
      )}

      <Drawer open={!!selected} onClose={() => setSelected(null)} title={selected ? fullName(selected.user) : ""} subtitle={selected?.student_code}>
        {selected && (
          <div className="space-y-5">
            <div className="flex justify-center">
              <Avatar name={fullName(selected.user)} src={selected.photo} size="lg" />
            </div>
            <DetailRow label={t("Sinf")} value={selected.class_room_name ?? t("Biriktirilmagan")} />
            <DetailRow label={t("Yosh")} value={selected.age ? String(selected.age) : "—"} />
            <DetailRow label={t("Telefon")} value={selected.user.phone || "—"} />
            <DetailRow label={t("Email")} value={selected.user.email || "—"} />
            <DetailRow label={t("Ro'yxatdan o'tgan")} value={formatDate(selected.created_at)} />
            {isDirector && <ProgressTiles studentId={selected.id} />}
            <div className="flex flex-col gap-2 sm:flex-row">
              {canEdit && (
                <Button variant="outline" className="w-full" onClick={() => setEditOpen(true)}>
                  <Pencil className="h-4 w-4" /> Tahrirlash
                </Button>
              )}
              {canTransfer && (
                <Button variant="outline" className="w-full" onClick={() => setTransferOpen(true)}>
                  <ArrowRightLeft className="h-4 w-4" /> Sinfga o'tkazish
                </Button>
              )}
            </div>
          </div>
        )}
      </Drawer>

      {selected && (
        <TransferModal
          student={selected}
          open={transferOpen}
          onClose={() => setTransferOpen(false)}
          onDone={() => {
            setTransferOpen(false)
            setSelected(null)
            refetch()
          }}
        />
      )}

      {selected && (
        <EditStudentModal
          student={selected}
          open={editOpen}
          onClose={() => setEditOpen(false)}
          onDone={() => {
            setEditOpen(false)
            setSelected(null)
            refetch()
          }}
        />
      )}

      <AddStudentModal
        open={addOpen}
        onClose={() => setAddOpen(false)}
        onDone={() => {
          setAddOpen(false)
          refetch()
        }}
      />
    </div>
  )
}

/** The pupil's headline numbers — average grade, attendance, homework and quizzes. */
function ProgressTiles({ studentId }: { studentId: number }) {
  const { data, loading } = useFetch<StudentProgress>(`/analytics/progress/?student=${studentId}`, [studentId])
  if (loading && !data) return <Skeleton className="h-24 w-full" />
  if (!data) return null

  const tiles = [
    { label: t("O'rtacha baho"), value: String(data.average_grade) },
    { label: t("Davomat"), value: `${data.attendance_percentage}%` },
    { label: t("Uy vazifa"), value: `${data.homework_completion}%` },
    { label: t("Test o'rtachasi"), value: `${data.quiz_average}%` },
  ]
  return (
    <div className="grid grid-cols-2 gap-2">
      {tiles.map((tile) => (
        <div key={tile.label} className="rounded-xl border border-ink-100 p-3 dark:border-ink-800">
          <p className="text-[11px] font-semibold uppercase tracking-wide text-ink-400">{tile.label}</p>
          <p className="mt-1 font-display text-xl font-bold text-ink-900 dark:text-white">{tile.value}</p>
        </div>
      ))}
    </div>
  )
}

function DetailRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between border-b border-ink-100 pb-3 text-sm dark:border-ink-800">
      <span className="text-ink-500 dark:text-ink-400">{label}</span>
      <span className="font-medium text-ink-800 dark:text-ink-100">{value}</span>
    </div>
  )
}

function TransferModal({
  student,
  open,
  onClose,
  onDone,
}: {
  student: StudentProfile
  open: boolean
  onClose: () => void
  onDone: () => void
}) {
  const { data: classes } = useFetch<Paginated<ClassRoom>>(open ? "/classes/?page_size=100" : null)
  const [newClass, setNewClass] = useState("")
  const [reason, setReason] = useState("")
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    if (!newClass) return
    setLoading(true)
    try {
      await api.post(`/students/${student.id}/transfer/`, { new_class: newClass, reason })
      toast.success(t("O'quvchi muvaffaqiyatli o'tkazildi"))
      onDone()
    } catch (err) {
      toast.error(getErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  return (
    <Modal open={open} onClose={onClose} title={t("Sinfga o'tkazish")}>
      <form onSubmit={handleSubmit} className="space-y-4">
        <Field label={t("Yangi sinf")}>
          <Select value={newClass} onChange={(e) => setNewClass(e.target.value)} required>
            <option value="">{t("Tanlang...")}</option>
            {classes?.results
              .filter((c) => c.id !== student.class_room)
              .map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name}
                </option>
              ))}
          </Select>
        </Field>
        <Field label={t("Sabab")}>
          <Input value={reason} onChange={(e) => setReason(e.target.value)} placeholder={t("Masalan: maktab ma'muriy qarori")} />
        </Field>
        <Button type="submit" className="w-full" loading={loading}>
          {t("O'tkazish")}
        </Button>
      </form>
    </Modal>
  )
}

function EditStudentModal({
  student,
  open,
  onClose,
  onDone,
}: {
  student: StudentProfile
  open: boolean
  onClose: () => void
  onDone: () => void
}) {
  const [form, setForm] = useState({
    first_name: student.user.first_name,
    last_name: student.user.last_name,
    phone: student.user.phone,
    age: student.age ? String(student.age) : "",
  })
  const [photo, setPhoto] = useState<File | null>(null)
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    if (!isPhoneComplete(form.phone)) {
      toast.error(t("Telefon raqami to'liq emas"))
      return
    }
    setLoading(true)
    try {
      const body = new FormData()
      body.append("first_name", form.first_name)
      body.append("last_name", form.last_name)
      body.append("phone", form.phone)
      if (form.age) body.append("age", form.age)
      if (photo) body.append("photo", photo)
      await api.patch(`/students/${student.id}/`, body)
      toast.success(t("Profil yangilandi"))
      onDone()
    } catch (err) {
      toast.error(getErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  return (
    <Modal open={open} onClose={onClose} title={t("Profilni tahrirlash — {code}", { code: student.student_code })}>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <Field label={t("Ism")}>
            <Input value={form.first_name} onChange={(e) => setForm((f) => ({ ...f, first_name: e.target.value }))} required />
          </Field>
          <Field label={t("Familiya")}>
            <Input value={form.last_name} onChange={(e) => setForm((f) => ({ ...f, last_name: e.target.value }))} required />
          </Field>
        </div>
        <div className="grid grid-cols-2 gap-4">
          <Field label={t("Telefon")}>
            <PhoneInput value={form.phone} onChange={(phone) => setForm((f) => ({ ...f, phone }))} />
          </Field>
          <Field label={t("Yosh")}>
            <Input type="number" min={5} max={25} value={form.age} onChange={(e) => setForm((f) => ({ ...f, age: e.target.value }))} />
          </Field>
        </div>
        <Field label={t("Rasm")}>
          <input
            type="file"
            accept="image/*"
            onChange={(e) => setPhoto(e.target.files?.[0] ?? null)}
            className="block w-full text-sm text-ink-500 file:mr-3 file:rounded-lg file:border-0 file:bg-brand-50 file:px-3.5 file:py-2 file:text-sm file:font-medium file:text-brand-700 hover:file:bg-brand-100 dark:file:bg-brand-500/15 dark:file:text-brand-300"
          />
        </Field>
        <p className="text-xs text-ink-400">
          Sinf va o'quvchi kodi bu yerdan o'zgartirilmaydi — sinf almashtirish uchun t("Sinfga o'tkazish") dan foydalaning.
        </p>
        <Button type="submit" className="w-full" loading={loading}>
          {t("Saqlash")}
        </Button>
      </form>
    </Modal>
  )
}

function AddStudentModal({ open, onClose, onDone }: { open: boolean; onClose: () => void; onDone: () => void }) {
  const { data: schools } = useFetch<Paginated<School>>(open ? "/schools/?page_size=100" : null)
  const { data: classes } = useFetch<Paginated<ClassRoom>>(open ? "/classes/?page_size=100" : null)
  const [form, setForm] = useState({
    first_name: "",
    last_name: "",
    username: "",
    password: "",
    student_code: "",
    school: "",
    class_room: "",
    phone: "",
    email: "",
  })
  const [loading, setLoading] = useState(false)

  function update<K extends keyof typeof form>(key: K, value: string) {
    setForm((f) => ({ ...f, [key]: value }))
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    if (!isPhoneComplete(form.phone)) {
      toast.error(t("Telefon raqami to'liq emas"))
      return
    }
    setLoading(true)
    try {
      await api.post("/auth/register/student/", form)
      toast.success(t("O'quvchi muvaffaqiyatli qo'shildi"))
      setForm({
        first_name: "",
        last_name: "",
        username: "",
        password: "",
        student_code: "",
        school: "",
        class_room: "",
        phone: "",
        email: "",
      })
      onDone()
    } catch (err) {
      toast.error(getErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  return (
    <Modal open={open} onClose={onClose} title={t("Yangi o'quvchi qo'shish")} size="lg">
      <form onSubmit={handleSubmit} className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <Field label={t("Ism")}>
          <Input value={form.first_name} onChange={(e) => update("first_name", e.target.value)} required />
        </Field>
        <Field label={t("Familiya")}>
          <Input value={form.last_name} onChange={(e) => update("last_name", e.target.value)} required />
        </Field>
        <Field label={t("Foydalanuvchi nomi")}>
          <Input value={form.username} onChange={(e) => update("username", e.target.value)} required />
        </Field>
        <Field label={t("Parol")}>
          <Input type="password" value={form.password} onChange={(e) => update("password", e.target.value)} required />
        </Field>
        <Field label={t("O'quvchi kodi")}>
          <Input value={form.student_code} onChange={(e) => update("student_code", e.target.value)} required />
        </Field>
        <Field label={t("Telefon")}>
          <PhoneInput value={form.phone} onChange={(phone) => update("phone", phone)} />
        </Field>
        <Field label={t("Maktab")}>
          <Select value={form.school} onChange={(e) => update("school", e.target.value)}>
            <option value="">{t("Tanlanmagan")}</option>
            {schools?.results.map((s) => (
              <option key={s.id} value={s.id}>
                {s.name}
              </option>
            ))}
          </Select>
        </Field>
        <Field label={t("Sinf")}>
          <Select value={form.class_room} onChange={(e) => update("class_room", e.target.value)}>
            <option value="">{t("Tanlanmagan")}</option>
            {classes?.results.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name}
              </option>
            ))}
          </Select>
        </Field>
        <Field label={t("Email")} className="sm:col-span-2">
          <Input type="email" value={form.email} onChange={(e) => update("email", e.target.value)} />
        </Field>
        <Button type="submit" className="sm:col-span-2" loading={loading}>
          <UserRound className="h-4 w-4" /> Qo'shish
        </Button>
      </form>
    </Modal>
  )
}
