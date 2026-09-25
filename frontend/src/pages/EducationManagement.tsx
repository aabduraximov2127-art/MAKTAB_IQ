import { type FormEvent, useState } from "react"
import { CalendarPlus, ClipboardCheck, GraduationCap, Trash2, UsersRound } from "lucide-react"
import toast from "react-hot-toast"
import { useFetch } from "../hooks/useFetch"
import { api, getErrorMessage } from "../lib/api"
import { useAccess } from "../lib/access"
import { todayISO } from "../lib/date"
import { PageHeader } from "../components/ui/PageHeader"
import { Button } from "../components/ui/Button"
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/Card"
import { StatCard } from "../components/ui/StatCard"
import { Field, Input } from "../components/ui/Input"
import { Select } from "../components/ui/Select"
import { Modal } from "../components/ui/Modal"
import { Drawer } from "../components/ui/Drawer"
import { Badge } from "../components/ui/Badge"
import { DataTable, type Column } from "../components/ui/Table"
import { EmptyState } from "../components/ui/EmptyState"
import { Skeleton } from "../components/ui/Skeleton"
import type { AdminAnalytics, ClassRoom, Lesson, Paginated, Subject, TeacherProfile } from "../types"
import { t } from "../i18n"

interface ClassReport {
  class_room: number
  class_name: string
  student_count: number
  average_grade: number
  attendance_percentage: number
  homework_completion: number
  quiz_average: number
  students: {
    student: number
    name: string
    student_code: string
    average_grade: number
    attendance_percentage: number
    homework_completion: number
    quiz_average: number
  }[]
}

interface TeacherAttendanceRow {
  id: number
  teacher_name: string
  status: string
  reason?: string
}

const TEACHER_STATUS_TONE: Record<string, "success" | "danger" | "warning" | "info"> = {
  PRESENT: "success",
  ABSENT: "danger",
  LATE: "warning",
  EXCUSED: "info",
}

/**
 * Education Management — for the director and the deputy director. Read access to the
 * whole school (classes, teachers' attendance, progress) plus the timetable. Both roles
 * are supervisors: they hold no grade/attendance-writing or user-administration permission,
 * so those actions simply are not offered here (and the API would refuse them anyway).
 */
export default function EducationManagementPage() {
  const { can } = useAccess()
  const canManageSchedule = can("manage_schedule")
  const [openClass, setOpenClass] = useState<ClassRoom | null>(null)
  const [lessonOpen, setLessonOpen] = useState(false)
  const [date, setDate] = useState(todayISO())

  const { data: stats, loading: statsLoading } = useFetch<AdminAnalytics>("/analytics/admin/")
  const { data: classes, loading: classesLoading } = useFetch<Paginated<ClassRoom>>("/classes/?page_size=100")
  const { data: teacherAttendance } = useFetch<Paginated<TeacherAttendanceRow>>(
    `/attendance/teacher-attendance/?date=${todayISO()}&page_size=100`
  )
  const {
    data: lessons,
    loading: lessonsLoading,
    refetch: refetchLessons,
  } = useFetch<Paginated<Lesson>>(`/lessons/?date=${date}&ordering=start_time&page_size=100`)

  const classColumns: Column<ClassRoom>[] = [
    { key: "name", header: t("Sinf"), render: (c) => <span className="font-medium text-ink-800 dark:text-ink-100">{c.name}</span> },
    { key: "curator", header: t("Sinf rahbari"), render: (c) => c.curator_name || "—", hideOnMobile: true },
    { key: "students", header: t("O'quvchilar"), render: (c) => c.student_count },
  ]

  async function removeLesson(lesson: Lesson) {
    try {
      await api.delete(`/lessons/${lesson.id}/`)
      toast.success(t("Dars o'chirildi"))
      refetchLessons()
    } catch (err) {
      toast.error(getErrorMessage(err))
    }
  }

  return (
    <div>
      <PageHeader
        title={t("O'quv jarayoni")}
        description={t("Maktab bo'yicha o'quv jarayonini nazorat qilish va dars jadvali")}
        actions={
          canManageSchedule && (
            <Button onClick={() => setLessonOpen(true)}>
              <CalendarPlus className="h-4 w-4" /> {t("Yangi dars")}
            </Button>
          )
        }
      />

      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        {statsLoading || !stats ? (
          Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-24 w-full" />)
        ) : (
          <>
            <StatCard label={t("O'rtacha baho")} value={`${stats.average_grades} / 10`} icon={GraduationCap} tone="brand" />
            <StatCard label={t("Davomat")} value={`${stats.attendance_percentage}%`} icon={ClipboardCheck} tone="emerald" />
            <StatCard label={t("Uy vazifa bajarilishi")} value={`${stats.homework_completion}%`} icon={UsersRound} tone="accent" />
            <StatCard label={t("O'qituvchi davomati")} value={`${stats.teacher_attendance_percentage}%`} icon={UsersRound} tone="sky" />
          </>
        )}
      </div>

      <div className="mt-6 grid grid-cols-1 gap-4 xl:grid-cols-3">
        <Card className="xl:col-span-2">
          <CardHeader>
            <CardTitle>{t("Sinflar")}</CardTitle>
            <span className="text-xs text-ink-400">{t("Hisobot uchun sinfni bosing")}</span>
          </CardHeader>
          <CardContent>
            <DataTable
              columns={classColumns}
              rows={classes?.results ?? []}
              keyField={(c) => c.id}
              loading={classesLoading}
              onRowClick={(c) => setOpenClass(c)}
              emptyTitle={t("Sinf topilmadi")}
            />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>{t("O'qituvchilar bugungi davomati")}</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {!teacherAttendance ? (
              <Skeleton className="h-24 w-full" />
            ) : teacherAttendance.results.length === 0 ? (
              <p className="text-sm text-ink-400">{t("Bugun davomat hali belgilanmagan")}</p>
            ) : (
              teacherAttendance.results.map((row) => (
                <div key={row.id} className="flex items-center justify-between gap-2 text-sm">
                  <span className="truncate font-medium text-ink-800 dark:text-ink-100">{row.teacher_name}</span>
                  <Badge tone={TEACHER_STATUS_TONE[row.status] ?? "neutral"}>{row.status}</Badge>
                </div>
              ))
            )}
          </CardContent>
        </Card>
      </div>

      <Card className="mt-4">
        <CardHeader>
          <CardTitle>{t("Dars jadvali")}</CardTitle>
          <Input type="date" value={date} onChange={(e) => setDate(e.target.value)} className="h-10 w-44" />
        </CardHeader>
        <CardContent>
          {lessonsLoading ? (
            <Skeleton className="h-24 w-full" />
          ) : !lessons || lessons.results.length === 0 ? (
            <EmptyState title={t("Dars yo'q")} description={t("Hozircha darslar kiritilmagan")} />
          ) : (
            <div className="space-y-2">
              {lessons.results.map((l) => (
                <div
                  key={l.id}
                  className="flex items-center justify-between gap-3 rounded-2xl border border-ink-100 px-4 py-3 dark:border-ink-800"
                >
                  <div className="min-w-0">
                    <p className="truncate text-sm font-medium text-ink-800 dark:text-ink-100">
                      {l.subject_name} · {l.class_room_name}
                    </p>
                    <p className="text-xs text-ink-400">
                      {l.start_time.slice(0, 5)}–{l.end_time.slice(0, 5)} · {l.teacher_name} · {l.room}
                    </p>
                  </div>
                  {canManageSchedule && (
                    <Button variant="ghost" size="icon" onClick={() => removeLesson(l)} aria-label={t("O'chirish")}>
                      <Trash2 className="h-4 w-4 text-rose-500" />
                    </Button>
                  )}
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      <ClassReportDrawer classRoom={openClass} onClose={() => setOpenClass(null)} />
      <LessonModal
        open={lessonOpen}
        defaultDate={date}
        onClose={() => setLessonOpen(false)}
        onDone={() => {
          setLessonOpen(false)
          refetchLessons()
        }}
      />
    </div>
  )
}

function ClassReportDrawer({ classRoom, onClose }: { classRoom: ClassRoom | null; onClose: () => void }) {
  const { data, loading } = useFetch<ClassReport>(classRoom ? `/analytics/class/?class_room=${classRoom.id}` : null)
  return (
    <Drawer
      open={!!classRoom}
      onClose={onClose}
      title={classRoom?.name}
      subtitle={classRoom ? t("{n} o'quvchi", { n: classRoom.student_count }) : undefined}
    >
      {loading || !data ? (
        <Skeleton className="h-40 w-full" />
      ) : (
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <Summary label={t("O'rtacha baho")} value={data.average_grade} />
            <Summary label={t("Davomat")} value={`${data.attendance_percentage}%`} />
            <Summary label={t("Uy vazifa bajarilishi")} value={`${data.homework_completion}%`} />
            <Summary label={t("Test o'rtachasi")} value={`${data.quiz_average}%`} />
          </div>
          <div className="space-y-2">
            {data.students.map((s) => (
              <div key={s.student} className="flex items-center justify-between rounded-xl border border-ink-100 px-3 py-2 text-sm dark:border-ink-800">
                <div>
                  <p className="font-medium text-ink-800 dark:text-ink-100">{s.name}</p>
                  <p className="text-xs text-ink-400">{s.student_code}</p>
                </div>
                <div className="text-right text-xs text-ink-500 dark:text-ink-400">
                  <p>
                    {t("Baho")}: <b className="text-ink-800 dark:text-ink-100">{s.average_grade}</b>
                  </p>
                  <p>
                    {t("Davomat")}: {s.attendance_percentage}%
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </Drawer>
  )
}

function Summary({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="rounded-2xl border border-ink-100 p-3 dark:border-ink-800">
      <p className="text-xs text-ink-400">{label}</p>
      <p className="mt-1 font-display text-xl text-ink-900 dark:text-white">{value}</p>
    </div>
  )
}

function LessonModal({
  open,
  defaultDate,
  onClose,
  onDone,
}: {
  open: boolean
  defaultDate: string
  onClose: () => void
  onDone: () => void
}) {
  const { data: classes } = useFetch<Paginated<ClassRoom>>(open ? "/classes/?page_size=100" : null)
  const { data: subjects } = useFetch<Paginated<Subject>>(open ? "/subjects/?page_size=100" : null)
  const { data: teachers } = useFetch<Paginated<TeacherProfile>>(open ? "/teachers/?page_size=100" : null)
  const [form, setForm] = useState({
    class_room: "",
    subject: "",
    teacher: "",
    room: "",
    date: defaultDate,
    start_time: "09:00",
    end_time: "09:45",
  })
  const [loading, setLoading] = useState(false)
  const set = (key: keyof typeof form, value: string) => setForm((f) => ({ ...f, [key]: value }))

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setLoading(true)
    try {
      await api.post("/lessons/", form)
      toast.success(t("Dars qo'shildi"))
      onDone()
    } catch (err) {
      // the API reports teacher / room / class double-booking here
      toast.error(getErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  return (
    <Modal open={open} onClose={onClose} title={t("Yangi dars")} size="lg">
      <form onSubmit={handleSubmit} className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <Field label={t("Sinf")}>
          <Select value={form.class_room} onChange={(e) => set("class_room", e.target.value)} required>
            <option value="">{t("Tanlang...")}</option>
            {classes?.results.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name}
              </option>
            ))}
          </Select>
        </Field>
        <Field label={t("Fan")}>
          <Select value={form.subject} onChange={(e) => set("subject", e.target.value)} required>
            <option value="">{t("Tanlang...")}</option>
            {subjects?.results.map((s) => (
              <option key={s.id} value={s.id}>
                {s.name}
              </option>
            ))}
          </Select>
        </Field>
        <Field label={t("O'qituvchi")}>
          <Select value={form.teacher} onChange={(e) => set("teacher", e.target.value)} required>
            <option value="">{t("Tanlang...")}</option>
            {teachers?.results.map((tp) => (
              <option key={tp.id} value={tp.id}>
                {tp.user.first_name} {tp.user.last_name}
              </option>
            ))}
          </Select>
        </Field>
        <Field label={t("Xona")}>
          <Input value={form.room} onChange={(e) => set("room", e.target.value)} required />
        </Field>
        <Field label={t("Sana")}>
          <Input type="date" value={form.date} onChange={(e) => set("date", e.target.value)} required />
        </Field>
        <div className="grid grid-cols-2 gap-3">
          <Field label={t("Boshlanishi")}>
            <Input type="time" value={form.start_time} onChange={(e) => set("start_time", e.target.value)} required />
          </Field>
          <Field label={t("Tugashi")}>
            <Input type="time" value={form.end_time} onChange={(e) => set("end_time", e.target.value)} required />
          </Field>
        </div>
        <Button type="submit" className="sm:col-span-2" loading={loading}>
          {t("Saqlash")}
        </Button>
      </form>
    </Modal>
  )
}
