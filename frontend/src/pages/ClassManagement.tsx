import { type FormEvent, useState } from "react"
import { Link } from "react-router-dom"
import { BookOpenCheck, ClipboardCheck, Megaphone, UsersRound } from "lucide-react"
import toast from "react-hot-toast"
import { useFetch } from "../hooks/useFetch"
import { api, getErrorMessage } from "../lib/api"
import { useAccess } from "../lib/access"
import { formatDate, fullName } from "../lib/format"
import { todayISO } from "../lib/date"
import { PageHeader } from "../components/ui/PageHeader"
import { Button } from "../components/ui/Button"
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/Card"
import { StatCard } from "../components/ui/StatCard"
import { Field, Input } from "../components/ui/Input"
import { Select } from "../components/ui/Select"
import { Modal } from "../components/ui/Modal"
import { Tabs } from "../components/ui/Tabs"
import { Badge } from "../components/ui/Badge"
import { DataTable, type Column } from "../components/ui/Table"
import { EmptyState } from "../components/ui/EmptyState"
import { Skeleton } from "../components/ui/Skeleton"
import type { Paginated, TeacherProfile } from "../types"
import { t } from "../i18n"

interface StudentRow {
  student: number
  name: string
  student_code: string
  average_grade: number
  attendance_percentage: number
  homework_completion: number
  quiz_average: number
}

interface ClassReport {
  class_room: number
  class_name: string
  student_count: number
  average_grade: number
  attendance_percentage: number
  homework_completion: number
  quiz_average: number
  students: StudentRow[]
}

interface AttendanceRow {
  id: number
  status: "PRESENT" | "ABSENT" | "LATE" | "EXCUSED"
}

/**
 * Class Management — the class teacher's (curator's) workspace. Everything here is scoped by
 * the backend to the classes this user curates: the report endpoint answers 403 for any other
 * class, and the announcement endpoint refuses any target other than the own class.
 */
export default function ClassManagementPage() {
  const { user, can } = useAccess()
  const classes = user?.curated_classes ?? []
  const [activeId, setActiveId] = useState<number | null>(null)
  const [announceOpen, setAnnounceOpen] = useState(false)
  const selected = classes.find((c) => c.id === activeId) ?? classes[0]

  const { data: report, loading } = useFetch<ClassReport>(
    selected ? `/analytics/class/?class_room=${selected.id}` : null
  )
  const { data: attendance } = useFetch<Paginated<AttendanceRow>>(
    selected ? `/attendance/?class_room=${selected.id}&date=${todayISO()}&page_size=200` : null
  )
  const { data: teachers } = useFetch<Paginated<TeacherProfile>>(
    selected && can("view_class_teachers") ? "/teachers/?page_size=50" : null
  )

  if (!selected) {
    return (
      <div>
        <PageHeader title={t("Sinf boshqaruvi")} />
        <EmptyState icon={UsersRound} title={t("Sizga sinf rahbarligi biriktirilmagan")} />
      </div>
    )
  }

  const counts = { PRESENT: 0, ABSENT: 0, LATE: 0, EXCUSED: 0 }
  attendance?.results.forEach((a) => {
    counts[a.status] += 1
  })

  const columns: Column<StudentRow>[] = [
    {
      key: "name",
      header: t("O'quvchi"),
      render: (r) => (
        <div>
          <p className="font-medium text-ink-800 dark:text-ink-100">{r.name}</p>
          <p className="text-xs text-ink-400">{r.student_code}</p>
        </div>
      ),
    },
    { key: "grade", header: t("O'rtacha baho"), render: (r) => r.average_grade },
    { key: "att", header: t("Davomat"), render: (r) => `${r.attendance_percentage}%`, hideOnMobile: true },
    { key: "hw", header: t("Uy vazifa"), render: (r) => `${r.homework_completion}%`, hideOnMobile: true },
    { key: "quiz", header: t("Test"), render: (r) => `${r.quiz_average}%`, hideOnMobile: true },
  ]

  return (
    <div>
      <PageHeader
        title={t("Sinf boshqaruvi")}
        description={t("{name} sinfi — o'quvchilar, davomat va hisobot", { name: selected.name })}
        actions={
          can("send_class_announcement") && (
            <Button onClick={() => setAnnounceOpen(true)}>
              <Megaphone className="h-4 w-4" /> {t("Sinfga e'lon")}
            </Button>
          )
        }
      />

      {classes.length > 1 && (
        <div className="mb-4">
          <Tabs
            tabs={classes.map((c) => ({ key: String(c.id), label: c.name }))}
            active={String(selected.id)}
            onChange={(k) => setActiveId(Number(k))}
          />
        </div>
      )}

      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        {loading || !report ? (
          Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-24 w-full" />)
        ) : (
          <>
            <StatCard label={t("O'quvchilar")} value={report.student_count} icon={UsersRound} tone="brand" />
            <StatCard label={t("O'rtacha baho")} value={report.average_grade} icon={BookOpenCheck} tone="accent" />
            <StatCard label={t("Davomat")} value={`${report.attendance_percentage}%`} icon={ClipboardCheck} tone="emerald" />
            <StatCard label={t("Uy vazifa bajarilishi")} value={`${report.homework_completion}%`} icon={BookOpenCheck} tone="sky" />
          </>
        )}
      </div>

      <div className="mt-6 grid grid-cols-1 gap-4 xl:grid-cols-3">
        <Card className="xl:col-span-2">
          <CardHeader>
            <CardTitle>{t("O'quvchilar hisoboti")}</CardTitle>
          </CardHeader>
          <CardContent>
            <DataTable
              columns={columns}
              rows={report?.students ?? []}
              keyField={(r) => r.student}
              loading={loading}
              emptyTitle={t("Bu sinfda o'quvchi yo'q")}
            />
          </CardContent>
        </Card>

        <div className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>{t("Bugungi davomat")}</CardTitle>
              <span className="text-xs text-ink-400">{formatDate(todayISO())}</span>
            </CardHeader>
            <CardContent>
              {!attendance || attendance.count === 0 ? (
                <p className="text-sm text-ink-400">{t("Bugun davomat hali belgilanmagan")}</p>
              ) : (
                <div className="flex flex-wrap gap-2">
                  <Badge tone="success">
                    {t("Keldi")}: {counts.PRESENT}
                  </Badge>
                  <Badge tone="danger">
                    {t("Kelmadi")}: {counts.ABSENT}
                  </Badge>
                  <Badge tone="warning">
                    {t("Kechikdi")}: {counts.LATE}
                  </Badge>
                  <Badge tone="info">
                    {t("Sababli")}: {counts.EXCUSED}
                  </Badge>
                </div>
              )}
              <div className="mt-4 flex flex-wrap gap-2">
                <Link to="/attendance">
                  <Button size="sm" variant="outline">
                    {t("Davomat")}
                  </Button>
                </Link>
                <Link to="/homework">
                  <Button size="sm" variant="outline">
                    {t("Uy vazifalari")}
                  </Button>
                </Link>
                <Link to="/students">
                  <Button size="sm" variant="outline">
                    {t("O'quvchilar")}
                  </Button>
                </Link>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>{t("Sinf o'qituvchilari")}</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              {!teachers ? (
                <Skeleton className="h-16 w-full" />
              ) : teachers.results.length === 0 ? (
                <p className="text-sm text-ink-400">{t("O'qituvchi topilmadi")}</p>
              ) : (
                teachers.results.map((tp) => (
                  <div key={tp.id} className="flex items-center justify-between text-sm">
                    <span className="font-medium text-ink-800 dark:text-ink-100">{fullName(tp.user)}</span>
                    <span className="text-xs text-ink-400">{tp.teacher_id}</span>
                  </div>
                ))
              )}
            </CardContent>
          </Card>
        </div>
      </div>

      <ClassAnnouncementModal
        open={announceOpen}
        classId={selected.id}
        className={selected.name}
        onClose={() => setAnnounceOpen(false)}
      />
    </div>
  )
}

function ClassAnnouncementModal({
  open,
  classId,
  className,
  onClose,
}: {
  open: boolean
  classId: number
  className: string
  onClose: () => void
}) {
  const [form, setForm] = useState({ title: "", content: "", priority: "NORMAL" })
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setLoading(true)
    try {
      await api.post("/notifications/announcements/", { ...form, target: "CLASS", target_class: classId })
      toast.success(t("E'lon yuborildi"))
      setForm({ title: "", content: "", priority: "NORMAL" })
      onClose()
    } catch (err) {
      toast.error(getErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  return (
    <Modal open={open} onClose={onClose} title={t("{name} sinfiga e'lon", { name: className })}>
      <form onSubmit={handleSubmit} className="space-y-4">
        <Field label={t("Sarlavha")}>
          <Input value={form.title} onChange={(e) => setForm((f) => ({ ...f, title: e.target.value }))} required />
        </Field>
        <Field label={t("Matn")}>
          <textarea
            value={form.content}
            onChange={(e) => setForm((f) => ({ ...f, content: e.target.value }))}
            rows={4}
            required
            className="w-full rounded-2xl border border-ink-200 bg-white p-3 text-sm focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/40 dark:border-ink-700 dark:bg-ink-950 dark:text-white"
          />
        </Field>
        <Field label={t("Muhimlik")}>
          <Select value={form.priority} onChange={(e) => setForm((f) => ({ ...f, priority: e.target.value }))}>
            <option value="LOW">{t("Past")}</option>
            <option value="NORMAL">{t("O'rtacha")}</option>
            <option value="HIGH">{t("Yuqori")}</option>
          </Select>
        </Field>
        <Button type="submit" className="w-full" loading={loading}>
          {t("Yuborish")}
        </Button>
      </form>
    </Modal>
  )
}
