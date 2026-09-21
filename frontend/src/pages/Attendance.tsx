import { type FormEvent, useMemo, useState } from "react"
import { Check, CheckCircle2, ChevronLeft, ChevronRight, Clock3, MessageSquareText, XCircle } from "lucide-react"
import toast from "react-hot-toast"
import { useFetch } from "../hooks/useFetch"
import { api, getErrorMessage } from "../lib/api"
import { useAuthStore } from "../store/auth"
import { PageHeader } from "../components/ui/PageHeader"
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/Card"
import { Button } from "../components/ui/Button"
import { Select } from "../components/ui/Select"
import { Field, Input } from "../components/ui/Input"
import { Modal } from "../components/ui/Modal"
import { EmptyState } from "../components/ui/EmptyState"
import { Skeleton } from "../components/ui/Skeleton"
import { Tabs } from "../components/ui/Tabs"
import { Avatar } from "../components/ui/Avatar"
import { ATTENDANCE_COLORS, ATTENDANCE_LABELS, fullName } from "../lib/format"
import { todayISO } from "../lib/date"
import { cn } from "../lib/cn"
import type { Attendance, AttendanceStatus, ClassRoom, Paginated, StudentProfile } from "../types"

export default function AttendancePage() {
  const user = useAuthStore((s) => s.user)
  const canMark = user?.role === "ADMIN" || user?.role === "SUPERADMIN" || user?.role === "TEACHER"
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
      <PageHeader title="Davomat" description="Oylik davomat kalendari" />
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

const MONTHS_UZ = [
  "Yanvar", "Fevral", "Mart", "Aprel", "May", "Iyun",
  "Iyul", "Avgust", "Sentabr", "Oktabr", "Noyabr", "Dekabr",
]

function AttendanceCalendar({ studentId }: { studentId: number }) {
  const now = new Date()
  const [month, setMonth] = useState(now.getMonth() + 1)
  const [year, setYear] = useState(now.getFullYear())
  const [reasonTarget, setReasonTarget] = useState<{ date: string } | null>(null)

  const { data, loading, refetch } = useFetch<{ days: { day: number; status: AttendanceStatus | null }[] }>(
    `/attendance/calendar/?student=${studentId}&month=${month}&year=${year}`,
    [studentId, month, year]
  )

  const { data: records } = useFetch<Paginated<Attendance>>(
    `/attendance/?student=${studentId}&year=${year}&page_size=100`,
    [studentId, year]
  )

  function changeMonth(delta: number) {
    let m = month + delta
    let y = year
    if (m > 12) { m = 1; y++ }
    if (m < 1) { m = 12; y-- }
    setMonth(m)
    setYear(y)
  }

  function recordFor(day: number) {
    const iso = `${year}-${String(month).padStart(2, "0")}-${String(day).padStart(2, "0")}`
    return records?.results.find((r) => r.date === iso)
  }

  const summary = useMemo(() => {
    const days = data?.days ?? []
    const present = days.filter((d) => d.status === "PRESENT" || d.status === "LATE").length
    const marked = days.filter((d) => d.status).length
    return { present, marked, pct: marked ? Math.round((present / marked) * 100) : 0 }
  }, [data])

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle>
            {MONTHS_UZ[month - 1]} {year}
          </CardTitle>
          <div className="flex items-center gap-2">
            <span className="hidden rounded-full bg-emerald-100 px-3 py-1 text-xs font-semibold text-emerald-700 dark:bg-emerald-500/15 dark:text-emerald-400 sm:inline">
              Davomat: {summary.pct}%
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
          {loading || !data ? (
            <Skeleton className="h-64 w-full" />
          ) : (
            <div className="grid grid-cols-4 gap-2">
              {data.days.map((d) => {
                const record = recordFor(d.day)
                return (
                  <button
                    key={d.day}
                    disabled={!record || record.status !== "ABSENT"}
                    onClick={() => record && setReasonTarget({ date: record.date })}
                    className={cn(
                      "flex h-11 flex-col items-center justify-center gap-0.5 rounded-lg border text-xs font-medium transition-transform",
                      d.status
                        ? cn(ATTENDANCE_COLORS[d.status], "border-transparent")
                        : "border-dashed border-ink-200 text-ink-300 dark:border-ink-800",
                      record?.status === "ABSENT" && "cursor-pointer hover:scale-105"
                    )}
                  >
                    <span className="font-display font-semibold leading-none">{d.day}</span>
                    {record?.parent_reason && <MessageSquareText className="h-2.5 w-2.5 opacity-70" />}
                  </button>
                )
              })}
            </div>
          )}

          <div className="mt-5 flex flex-wrap gap-3 text-xs">
            {(["PRESENT", "ABSENT", "LATE", "EXCUSED"] as AttendanceStatus[]).map((s) => (
              <div key={s} className="flex items-center gap-1.5">
                <span className={cn("h-3 w-3 rounded-full", ATTENDANCE_COLORS[s].split(" ")[0])} />
                {ATTENDANCE_LABELS[s]}
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      <ReasonModal
        target={reasonTarget}
        record={reasonTarget ? records?.results.find((r) => r.date === reasonTarget.date) : undefined}
        onClose={() => setReasonTarget(null)}
        onDone={() => {
          setReasonTarget(null)
          refetch()
        }}
      />
    </div>
  )
}

function ReasonModal({
  target,
  record,
  onClose,
  onDone,
}: {
  target: { date: string } | null
  record?: Attendance
  onClose: () => void
  onDone: () => void
}) {
  const [reason, setReason] = useState(record?.parent_reason ?? "")
  const [loading, setLoading] = useState(false)
  const user = useAuthStore((s) => s.user)
  const canSubmit = user?.role === "PARENT"

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    if (!record) return
    setLoading(true)
    try {
      await api.patch(`/attendance/${record.id}/submit_reason/`, { parent_reason: reason })
      toast.success("Sabab yuborildi")
      onDone()
    } catch (err) {
      toast.error(getErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  return (
    <Modal open={!!target} onClose={onClose} title={target ? `${target.date} — kelmagan sabab` : ""}>
      {record?.parent_reason && !canSubmit ? (
        <p className="rounded-xl bg-ink-50 p-3 text-sm text-ink-700 dark:bg-ink-800 dark:text-ink-200">{record.parent_reason}</p>
      ) : canSubmit ? (
        <form onSubmit={handleSubmit} className="space-y-4">
          <Field label="Sababni kiriting">
            <Input value={reason} onChange={(e) => setReason(e.target.value)} placeholder="Masalan: farzandim kasal edi" required />
          </Field>
          <Button type="submit" className="w-full" loading={loading}>
            Yuborish
          </Button>
        </form>
      ) : (
        <EmptyState title="Sabab kiritilmagan" description="Ota-ona hali sabab yubormagan" />
      )}
    </Modal>
  )
}

/* ------------------------------------ Teacher/Admin ------------------------------------ */

const STATUS_OPTIONS: { status: AttendanceStatus; icon: typeof Check; label: string }[] = [
  { status: "PRESENT", icon: CheckCircle2, label: "Keldi" },
  { status: "ABSENT", icon: XCircle, label: "Kelmadi" },
  { status: "LATE", icon: Clock3, label: "Kechikdi" },
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
      <PageHeader title="Davomat belgilash" description="Sinf va sanani tanlab, o'quvchilar davomatini belgilang" />

      <div className="mb-5 flex flex-wrap gap-3">
        <Select value={classRoom} onChange={(e) => setClassRoom(e.target.value)} className="max-w-xs">
          <option value="">Sinfni tanlang...</option>
          {classes?.results.map((c) => (
            <option key={c.id} value={c.id}>
              {c.name}
            </option>
          ))}
        </Select>
        <Input type="date" value={date} onChange={(e) => setDate(e.target.value)} className="max-w-xs" />
      </div>

      {!classRoom ? (
        <EmptyState title="Sinfni tanlang" description="Davomat belgilash uchun avval sinfni tanlang" />
      ) : studentsLoading || recordsLoading ? (
        <div className="space-y-2">
          {Array.from({ length: 5 }).map((_, i) => (
            <Skeleton key={i} className="h-16 w-full" />
          ))}
        </div>
      ) : !students || students.results.length === 0 ? (
        <EmptyState title="Bu sinfda o'quvchi yo'q" />
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
                          ? cn(ATTENDANCE_COLORS[opt.status], "border-transparent")
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
