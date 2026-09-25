import { useMemo, useState } from "react"
import { ChevronLeft, ChevronRight, ClipboardCheck } from "lucide-react"
import { useFetch } from "../../hooks/useFetch"
import { PageHeader } from "../ui/PageHeader"
import { Button } from "../ui/Button"
import { Select } from "../ui/Select"
import { Input } from "../ui/Input"
import { Tabs } from "../ui/Tabs"
import { Avatar } from "../ui/Avatar"
import { CountChip } from "./CountChip"
import { Card, CardContent, CardHeader, CardTitle } from "../ui/Card"
import { EmptyState } from "../ui/EmptyState"
import { Skeleton } from "../ui/Skeleton"
import { ClassStudentPicker, type PickerSelection } from "../shared/ClassStudentPicker"
import { AttendanceCalendar, MONTHS_UZ } from "./AttendanceCalendar"
import { ATTENDANCE_LABELS, ATTENDANCE_SOLID, ATTENDANCE_UNMARKED, fullName } from "../../lib/format"
import { cn } from "../../lib/cn"
import type { AttendanceStatus, Paginated, TeacherAttendance, TeacherProfile } from "../../types"
import { t } from "../../i18n"

/** Today's date as the school sees it (local, not UTC). */
function localToday() {
  const now = new Date()
  return new Date(now.getTime() - now.getTimezoneOffset() * 60000).toISOString().slice(0, 10)
}

/**
 * The director's attendance page, read-only, in two tabs:
 *  1. teachers — who came to work on a given day, or one teacher's month;
 *  2. pupils   — pick a class, then a pupil, and see their month.
 */
export function DirectorAttendance() {
  const [tab, setTab] = useState<"teachers" | "students">("teachers")
  return (
    <div>
      <PageHeader title={t("Davomat")} description={t("O'qituvchilar va o'quvchilar davomati")} />
      <div className="mb-5">
        <Tabs
          tabs={[
            { key: "teachers", label: t("O'qituvchilar") },
            { key: "students", label: t("O'quvchilar") },
          ]}
          active={tab}
          onChange={(key) => setTab(key as "teachers" | "students")}
        />
      </div>
      {tab === "teachers" ? <TeachersAttendance /> : <StudentsAttendance />}
    </div>
  )
}

/* --------------------------------- teachers --------------------------------- */

function TeachersAttendance() {
  const [date, setDate] = useState(localToday())
  const [teacherId, setTeacherId] = useState("")
  const { data: teachers } = useFetch<Paginated<TeacherProfile>>("/teachers/?page_size=100")

  return (
    <div>
      <div className="mb-5 flex flex-wrap items-center gap-3">
        <Select value={teacherId} onChange={(e) => setTeacherId(e.target.value)} className="min-w-[14rem]" aria-label={t("O'qituvchini tanlang...")}>
          <option value="">{t("Barcha o'qituvchilar")}</option>
          {teachers?.results.map((teacher) => (
            <option key={teacher.id} value={teacher.id}>
              {fullName(teacher.user)}
            </option>
          ))}
        </Select>
        {!teacherId && (
          <Input type="date" value={date} max={localToday()} onChange={(e) => setDate(e.target.value || localToday())} className="max-w-[12rem]" aria-label={t("Sana")} />
        )}
      </div>

      {teacherId ? (
        <TeacherMonth teacherId={Number(teacherId)} name={fullName(teachers?.results.find((x) => String(x.id) === teacherId)?.user)} />
      ) : (
        <TeachersOnDate date={date} teachers={teachers?.results ?? []} onOpen={(id) => setTeacherId(String(id))} />
      )}
    </div>
  )
}

function StatusPill({ status, note }: { status: AttendanceStatus; note?: string }) {
  return (
    <span className={cn("rounded-full px-2.5 py-1 text-xs font-semibold", ATTENDANCE_SOLID[status])} title={note || undefined}>
      {ATTENDANCE_LABELS[status]}
    </span>
  )
}

function TeachersOnDate({ date, teachers, onOpen }: { date: string; teachers: TeacherProfile[]; onOpen: (teacherId: number) => void }) {
  const { data, loading } = useFetch<Paginated<TeacherAttendance>>(
    `/attendance/teacher-attendance/?date=${date}&page_size=200`,
    [date]
  )
  const byTeacher = useMemo(() => new Map((data?.results ?? []).map((r) => [r.teacher, r])), [data])

  const totals = useMemo(() => {
    const counts = { PRESENT: 0, LATE: 0, ABSENT: 0, EXCUSED: 0, unmarked: 0 }
    for (const teacher of teachers) {
      const record = byTeacher.get(teacher.id)
      if (record) counts[record.status]++
      else counts.unmarked++
    }
    return counts
  }, [teachers, byTeacher])

  if (loading && !data) {
    return (
      <div className="space-y-2">
        {Array.from({ length: 5 }).map((_, i) => (
          <Skeleton key={i} className="h-16 w-full" />
        ))}
      </div>
    )
  }
  if (teachers.length === 0) return <EmptyState title={t("O'qituvchi topilmadi")} />

  return (
    <>
      <div className="mb-5 flex flex-wrap gap-2">
        <CountChip status="PRESENT" label={ATTENDANCE_LABELS.PRESENT} count={totals.PRESENT} />
        <CountChip status="LATE" label={ATTENDANCE_LABELS.LATE} count={totals.LATE} />
        <CountChip status="ABSENT" label={ATTENDANCE_LABELS.ABSENT} count={totals.ABSENT} />
        <CountChip status="EXCUSED" label={ATTENDANCE_LABELS.EXCUSED} count={totals.EXCUSED} />
        <CountChip label={t("Belgilanmagan")} count={totals.unmarked} />
      </div>

      <div className="space-y-2.5">
        {teachers.map((teacher) => {
          const record = byTeacher.get(teacher.id)
          return (
            <button
              key={teacher.id}
              type="button"
              onClick={() => onOpen(teacher.id)}
              className="flex w-full items-center justify-between gap-3 rounded-xl border border-ink-100 bg-white p-3.5 text-left transition-colors hover:border-brand-200 dark:border-ink-800 dark:bg-ink-900 dark:hover:border-brand-500/40"
            >
              <span className="flex min-w-0 items-center gap-3">
                <Avatar name={fullName(teacher.user)} src={teacher.avatar} size="sm" />
                <span className="min-w-0">
                  <span className="block truncate text-sm font-medium text-ink-800 dark:text-ink-100">{fullName(teacher.user)}</span>
                  {record?.reason && <span className="block truncate text-xs text-ink-400">{record.reason}</span>}
                </span>
              </span>
              {record ? (
                <StatusPill status={record.status} note={record.reason} />
              ) : (
                <span className={cn("rounded-full px-2.5 py-1 text-xs font-semibold", ATTENDANCE_UNMARKED)}>{t("Belgilanmagan")}</span>
              )}
            </button>
          )
        })}
      </div>
    </>
  )
}

/** One teacher's month, day by day. */
function TeacherMonth({ teacherId, name }: { teacherId: number; name: string }) {
  const now = new Date()
  const [month, setMonth] = useState(now.getMonth() + 1)
  const [year, setYear] = useState(now.getFullYear())
  const { data, loading } = useFetch<Paginated<TeacherAttendance>>(
    `/attendance/teacher-attendance/?teacher=${teacherId}&page_size=200`,
    [teacherId]
  )

  const daysInMonth = new Date(year, month, 0).getDate()
  const byDay = useMemo(() => {
    const map = new Map<number, TeacherAttendance>()
    for (const record of data?.results ?? []) {
      const [y, m, d] = record.date.split("-").map(Number)
      if (y === year && m === month && d) map.set(d, record)
    }
    return map
  }, [data, month, year])

  const marked = [...byDay.values()]
  const came = marked.filter((r) => r.status === "PRESENT" || r.status === "LATE").length
  const pct = marked.length ? Math.round((came / marked.length) * 100) : 0

  function changeMonth(delta: number) {
    let m = month + delta
    let y = year
    if (m > 12) { m = 1; y++ }
    if (m < 1) { m = 12; y-- }
    setMonth(m)
    setYear(y)
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>
          {name} · {MONTHS_UZ[month - 1]} {year}
        </CardTitle>
        <div className="flex items-center gap-2">
          <span className={cn("hidden rounded-full px-3 py-1 text-xs font-semibold sm:inline", ATTENDANCE_SOLID.PRESENT)}>
            {t("Davomat")}: {pct}%
          </span>
          <Button variant="outline" size="icon" onClick={() => changeMonth(-1)}>
            <ChevronLeft className="h-4 w-4" />
          </Button>
          <Button variant="outline" size="icon" onClick={() => changeMonth(1)}>
            <ChevronRight className="h-4 w-4" />
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        {loading && !data ? (
          <Skeleton className="h-64 w-full" />
        ) : (
          <div className="grid grid-cols-4 gap-2">
            {Array.from({ length: daysInMonth }, (_, i) => i + 1).map((day) => {
              const record = byDay.get(day)
              return (
                <div
                  key={day}
                  title={record ? `${ATTENDANCE_LABELS[record.status]}${record.reason ? ` — ${record.reason}` : ""}` : undefined}
                  className={cn(
                    "flex h-11 items-center justify-center rounded-lg border text-xs font-semibold",
                    record ? cn(ATTENDANCE_SOLID[record.status], "border-transparent shadow-sm") : "border-dashed border-ink-300 text-ink-500 dark:border-ink-600 dark:text-ink-400"
                  )}
                >
                  <span className="font-display font-semibold leading-none">{day}</span>
                </div>
              )
            })}
          </div>
        )}
        <div className="mt-5 flex flex-wrap gap-3 text-xs">
          {(["PRESENT", "ABSENT", "LATE", "EXCUSED"] as AttendanceStatus[]).map((s) => (
            <div key={s} className="flex items-center gap-1.5 font-medium text-ink-700 dark:text-ink-200">
              <span className={cn("h-3.5 w-3.5 rounded-full", ATTENDANCE_SOLID[s].split(" ")[0])} />
              {ATTENDANCE_LABELS[s]}
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}

/* --------------------------------- pupils --------------------------------- */

function StudentsAttendance() {
  const [picked, setPicked] = useState<PickerSelection>({ classRoom: null, student: null })

  return (
    <div>
      <ClassStudentPicker className="mb-5" onChange={setPicked} />
      {picked.student ? (
        <>
          <p className="mb-3 text-sm text-ink-500 dark:text-ink-400">
            <span className="font-semibold text-ink-800 dark:text-ink-100">{fullName(picked.student.user)}</span>
            {picked.classRoom && ` · ${picked.classRoom.name}`}
          </p>
          <AttendanceCalendar key={picked.student.id} studentId={picked.student.id} />
        </>
      ) : (
        <EmptyState
          icon={ClipboardCheck}
          title={picked.classRoom ? t("O'quvchini tanlang") : t("Sinfni tanlang")}
          description={t("Davomatini ko'rish uchun avval sinfni, keyin o'quvchini tanlang")}
        />
      )}
    </div>
  )
}
