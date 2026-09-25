import { useState } from "react"
import { Check, CheckCircle2, Clock3, XCircle } from "lucide-react"
import toast from "react-hot-toast"
import { useFetch } from "../hooks/useFetch"
import { api, getErrorMessage } from "../lib/api"
import { useAccess } from "../lib/access"
import { PageHeader } from "../components/ui/PageHeader"
import { Select } from "../components/ui/Select"
import { Input } from "../components/ui/Input"
import { EmptyState } from "../components/ui/EmptyState"
import { Skeleton } from "../components/ui/Skeleton"
import { Tabs } from "../components/ui/Tabs"
import { Avatar } from "../components/ui/Avatar"
import { AttendanceCalendar } from "../components/attendance/AttendanceCalendar"
import { ClassTeacherAttendance } from "../components/attendance/ClassTeacherAttendance"
import { DirectorAttendance } from "../components/attendance/DirectorAttendance"
import { ATTENDANCE_SOLID, fullName } from "../lib/format"
import { todayISO } from "../lib/date"
import { cn } from "../lib/cn"
import type { Attendance, AttendanceStatus, ClassRoom, Paginated, StudentProfile } from "../types"
import { t } from "../i18n"

export default function AttendancePage() {
  const { canAny, hasRole } = useAccess()
  const canMark = canAny("mark_attendance", "manage_class_attendance")
  // The director reads attendance in two tabs: teachers, and pupils picked class by class.
  if (hasRole("DIRECTOR")) return <DirectorAttendance />
  // A class teacher keeps the register of their own class only (with the reason for each absence).
  if (hasRole("CLASS_TEACHER")) return <ClassTeacherAttendance />
  return canMark ? <MarkAttendanceView /> : <MyAttendanceView />
}

/* -------------------------------- Student/Parent -------------------------------- */

function MyAttendanceView() {
  const { data: students } = useFetch<Paginated<StudentProfile>>("/students/")
  const [activeChild, setActiveChild] = useState<number | null>(null)
  const children = students?.results ?? []
  const selectedId = activeChild ?? children[0]?.id ?? null

  return (
    <div>
      <PageHeader title={t("Davomat")} description={t("Oylik davomat kalendari")} />
      {children.length > 1 && (
        <div className="mb-4">
          <Tabs
            tabs={children.map((c) => ({ key: String(c.id), label: fullName(c.user) }))}
            active={String(selectedId)}
            onChange={(k) => setActiveChild(Number(k))}
          />
        </div>
      )}
      {selectedId && <AttendanceCalendar studentId={selectedId} />}
    </div>
  )
}

/* ------------------------------------ Teacher/Admin ------------------------------------ */

const STATUS_OPTIONS: { status: AttendanceStatus; icon: typeof Check; label: string }[] = [
  { status: "PRESENT", icon: CheckCircle2, label: t("Keldi") },
  { status: "ABSENT", icon: XCircle, label: t("Kelmadi") },
  { status: "LATE", icon: Clock3, label: t("Kechikdi") },
]

function MarkAttendanceView() {
  const { data: classes } = useFetch<Paginated<ClassRoom>>("/classes/?page_size=100")
  const [classRoom, setClassRoom] = useState("")
  const [date, setDate] = useState(todayISO())

  const { data: students, loading: studentsLoading } = useFetch<Paginated<StudentProfile>>(
    classRoom ? `/students/?class_room=${classRoom}&page_size=100` : null,
    [classRoom]
  )
  const { data: records, loading: recordsLoading, refetch } = useFetch<Paginated<Attendance>>(
    classRoom ? `/attendance/?class_room=${classRoom}&date=${date}&page_size=100` : null,
    [classRoom, date]
  )

  const [pending, setPending] = useState<number | null>(null)

  function recordFor(studentId: number) {
    return records?.results.find((r) => r.student === studentId)
  }

  async function setStatus(studentId: number, status: AttendanceStatus) {
    const existing = recordFor(studentId)
    setPending(studentId)
    try {
      if (existing) {
        await api.patch(`/attendance/${existing.id}/`, { status })
      } else {
        await api.post("/attendance/", { student: studentId, class_room: classRoom, date, status })
      }
      refetch()
    } catch (err) {
      toast.error(getErrorMessage(err))
    } finally {
      setPending(null)
    }
  }

  return (
    <div>
      <PageHeader title={t("Davomat belgilash")} description={t("Sinf va sanani tanlab, o'quvchilar davomatini belgilang")} />

      <div className="mb-5 flex flex-wrap gap-3">
        <Select value={classRoom} onChange={(e) => setClassRoom(e.target.value)} className="max-w-xs">
          <option value="">{t("Sinfni tanlang...")}</option>
          {classes?.results.map((c) => (
            <option key={c.id} value={c.id}>
              {c.name}
            </option>
          ))}
        </Select>
        <Input type="date" value={date} onChange={(e) => setDate(e.target.value)} className="max-w-xs" />
      </div>

      {!classRoom ? (
        <EmptyState title={t("Sinfni tanlang")} description={t("Davomat belgilash uchun avval sinfni tanlang")} />
      ) : studentsLoading || recordsLoading ? (
        <div className="space-y-2">
          {Array.from({ length: 5 }).map((_, i) => (
            <Skeleton key={i} className="h-16 w-full" />
          ))}
        </div>
      ) : !students || students.results.length === 0 ? (
        <EmptyState title={t("Bu sinfda o'quvchi yo'q")} />
      ) : (
        <div className="space-y-2.5">
          {students.results.map((s) => {
            const record = recordFor(s.id)
            return (
              <div
                key={s.id}
                className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-ink-100 bg-white p-3.5 dark:border-ink-800 dark:bg-ink-900"
              >
                <div className="flex items-center gap-3">
                  <Avatar name={fullName(s.user)} src={s.photo} size="sm" />
                  <p className="text-sm font-medium text-ink-800 dark:text-ink-100">{fullName(s.user)}</p>
                </div>
                <div className="flex gap-1.5">
                  {STATUS_OPTIONS.map((opt) => (
                    <button
                      key={opt.status}
                      disabled={pending === s.id}
                      onClick={() => setStatus(s.id, opt.status)}
                      className={cn(
                        "flex items-center gap-1.5 rounded-lg border px-2.5 py-1.5 text-xs font-medium transition-colors disabled:opacity-50",
                        record?.status === opt.status
                          ? cn(ATTENDANCE_SOLID[opt.status], "border-transparent shadow-sm")
                          : "border-ink-200 text-ink-500 hover:bg-ink-50 dark:border-ink-700 dark:text-ink-400 dark:hover:bg-ink-800"
                      )}
                    >
                      <opt.icon className="h-3.5 w-3.5" /> {opt.label}
                    </button>
                  ))}
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
