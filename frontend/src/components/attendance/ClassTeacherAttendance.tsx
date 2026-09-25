import { useMemo, useState } from "react"
import { AnimatePresence, motion } from "framer-motion"
import {
  CheckCircle2,
  ChevronDown,
  CircleHelp,
  Clock3,
  House,
  Thermometer,
  Trophy,
  XCircle,
  type LucideIcon,
} from "lucide-react"
import toast from "react-hot-toast"
import { useFetch } from "../../hooks/useFetch"
import { api, getErrorMessage } from "../../lib/api"
import { useAccess } from "../../lib/access"
import { PageHeader } from "../ui/PageHeader"
import { Select } from "../ui/Select"
import { Input } from "../ui/Input"
import { Avatar } from "../ui/Avatar"
import { Badge } from "../ui/Badge"
import { EmptyState } from "../ui/EmptyState"
import { Skeleton } from "../ui/Skeleton"
import { ABSENCE_REASON_LABELS, ATTENDANCE_COLORS, attendanceLabel, fullName } from "../../lib/format"
import { cn } from "../../lib/cn"
import type { AbsenceReason, Attendance, AttendanceStatus, Paginated, StudentProfile } from "../../types"
import { t } from "../../i18n"

/** Today's date as the school sees it (local, not UTC — the register is filled in the morning). */
function localToday() {
  const now = new Date()
  return new Date(now.getTime() - now.getTimezoneOffset() * 60000).toISOString().slice(0, 10)
}

interface Choice {
  key: string
  status: AttendanceStatus
  reason: AbsenceReason | ""
  label: string
  icon: LucideIcon
}

/** What a class teacher can record for a pupil: a state, or one of the excused reasons. */
const STATE_CHOICES: Choice[] = [
  { key: "present", status: "PRESENT", reason: "", label: t("Keldi"), icon: CheckCircle2 },
  { key: "late", status: "LATE", reason: "", label: t("Kechikdi"), icon: Clock3 },
  { key: "unexcused", status: "ABSENT", reason: "", label: t("Sababsiz"), icon: XCircle },
]

const EXCUSED_CHOICES: Choice[] = [
  { key: "sick", status: "EXCUSED", reason: "SICK", label: ABSENCE_REASON_LABELS.SICK, icon: Thermometer },
  { key: "family", status: "EXCUSED", reason: "FAMILY", label: ABSENCE_REASON_LABELS.FAMILY, icon: House },
  { key: "competition", status: "EXCUSED", reason: "COMPETITION", label: ABSENCE_REASON_LABELS.COMPETITION, icon: Trophy },
  { key: "other", status: "EXCUSED", reason: "OTHER", label: ABSENCE_REASON_LABELS.OTHER, icon: CircleHelp },
]

function isActive(record: Attendance | undefined, choice: Choice) {
  return !!record && record.status === choice.status && (record.absence_reason || "") === choice.reason
}

/**
 * The class teacher's register: the pupils of their ONE class, today (or another day). Tapping a
 * pupil opens the possible outcomes right underneath — came, late, unexcused, or excused with a
 * reason (sick, family, competition, other). Only the curated class is ever offered; the API
 * refuses any other class anyway.
 */
export function ClassTeacherAttendance() {
  const { curatedClasses } = useAccess()
  const [classId, setClassId] = useState<number | null>(curatedClasses[0]?.id ?? null)
  const [date, setDate] = useState(localToday())
  const [openId, setOpenId] = useState<number | null>(null)
  const [pending, setPending] = useState<number | null>(null)

  const className = curatedClasses.find((c) => c.id === classId)?.name ?? ""

  const { data: students, loading } = useFetch<Paginated<StudentProfile>>(
    classId ? `/students/?class_room=${classId}&page_size=100` : null,
    [classId]
  )
  const { data: records, refetch } = useFetch<Paginated<Attendance>>(
    classId ? `/attendance/?class_room=${classId}&date=${date}&page_size=100` : null,
    [classId, date]
  )

  const recordByStudent = useMemo(() => {
    const map = new Map<number, Attendance>()
    for (const record of records?.results ?? []) {
      // the daily register has no subject; ignore any per-lesson rows
      if (record.subject === null || record.subject === undefined) map.set(record.student, record)
    }
    return map
  }, [records])

  const totals = useMemo(() => {
    const counts = { present: 0, late: 0, unexcused: 0, excused: 0, unmarked: 0 }
    for (const student of students?.results ?? []) {
      const record = recordByStudent.get(student.id)
      if (!record) counts.unmarked++
      else if (record.status === "PRESENT") counts.present++
      else if (record.status === "LATE") counts.late++
      else if (record.status === "ABSENT") counts.unexcused++
      else counts.excused++
    }
    return counts
  }, [students, recordByStudent])

  async function save(student: StudentProfile, choice: Choice) {
    if (!classId) return
    const existing = recordByStudent.get(student.id)
    setPending(student.id)
    try {
      const body = { status: choice.status, absence_reason: choice.reason }
      if (existing) {
        await api.patch(`/attendance/${existing.id}/`, body)
      } else {
        await api.post("/attendance/", { student: student.id, class_room: classId, date, ...body })
      }
      await refetch()
      setOpenId(null)
    } catch (err) {
      toast.error(getErrorMessage(err))
    } finally {
      setPending(null)
    }
  }

  if (curatedClasses.length === 0) {
    return (
      <div>
        <PageHeader title={t("Davomat")} description={t("Sinf davomatini belgilash")} />
        <EmptyState title={t("Sizga sinf biriktirilmagan")} description={t("Davomat faqat sinf rahbari tomonidan belgilanadi")} />
      </div>
    )
  }

  return (
    <div>
      <PageHeader
        title={t("Davomat")}
        description={t("{name} sinfi — faqat o'z sinfingiz davomatini belgilay olasiz", { name: className })}
      />

      <div className="mb-5 flex flex-wrap items-center gap-3">
        {curatedClasses.length > 1 && (
          <Select value={classId ?? ""} onChange={(e) => setClassId(Number(e.target.value))} className="max-w-[10rem]">
            {curatedClasses.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name}
              </option>
            ))}
          </Select>
        )}
        <Input
          type="date"
          value={date}
          max={localToday()}
          onChange={(e) => {
            setDate(e.target.value || localToday())
            setOpenId(null)
          }}
          className="max-w-[12rem]"
          aria-label={t("Sana")}
        />
      </div>

      <div className="mb-5 flex flex-wrap gap-2 text-xs font-medium">
        <Badge tone="success">
          {t("Keldi")}: {totals.present}
        </Badge>
        <Badge tone="warning">
          {t("Kechikdi")}: {totals.late}
        </Badge>
        <Badge tone="danger">
          {t("Sababsiz")}: {totals.unexcused}
        </Badge>
        <Badge tone="info">
          {t("Sababli")}: {totals.excused}
        </Badge>
        <Badge tone="neutral">
          {t("Belgilanmagan")}: {totals.unmarked}
        </Badge>
      </div>

      {loading ? (
        <div className="space-y-2">
          {Array.from({ length: 6 }).map((_, i) => (
            <Skeleton key={i} className="h-16 w-full" />
          ))}
        </div>
      ) : !students || students.results.length === 0 ? (
        <EmptyState title={t("Bu sinfda o'quvchi yo'q")} />
      ) : (
        <div className="space-y-2.5">
          {students.results.map((student) => {
            const record = recordByStudent.get(student.id)
            const open = openId === student.id
            return (
              <div
                key={student.id}
                className={cn(
                  "overflow-hidden rounded-xl border bg-white transition-colors dark:bg-ink-900",
                  open ? "border-brand-400 dark:border-brand-500/60" : "border-ink-100 dark:border-ink-800"
                )}
              >
                <button
                  type="button"
                  onClick={() => setOpenId(open ? null : student.id)}
                  aria-expanded={open}
                  className="flex w-full items-center justify-between gap-3 p-3.5 text-left"
                >
                  <span className="flex min-w-0 items-center gap-3">
                    <Avatar name={fullName(student.user)} src={student.photo} size="sm" />
                    <span className="truncate text-sm font-medium text-ink-800 dark:text-ink-100">{fullName(student.user)}</span>
                  </span>
                  <span className="flex shrink-0 items-center gap-2">
                    {record ? (
                      <span
                        className={cn(
                          "rounded-full px-2.5 py-1 text-xs font-medium",
                          ATTENDANCE_COLORS[record.status]
                        )}
                      >
                        {attendanceLabel(record.status, record.absence_reason)}
                      </span>
                    ) : (
                      <Badge tone="neutral">{t("Belgilanmagan")}</Badge>
                    )}
                    <ChevronDown className={cn("h-4 w-4 text-ink-400 transition-transform", open && "rotate-180")} />
                  </span>
                </button>

                <AnimatePresence initial={false}>
                  {open && (
                    <motion.div
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: "auto", opacity: 1 }}
                      exit={{ height: 0, opacity: 0 }}
                      transition={{ duration: 0.18 }}
                      className="overflow-hidden"
                    >
                      <div className="space-y-3 border-t border-ink-100 px-3.5 pb-4 pt-3 dark:border-ink-800">
                        <ChoiceGroup
                          title={t("Holat")}
                          choices={STATE_CHOICES}
                          record={record}
                          disabled={pending === student.id}
                          onPick={(choice) => save(student, choice)}
                        />
                        <ChoiceGroup
                          title={t("Sababli")}
                          choices={EXCUSED_CHOICES}
                          record={record}
                          disabled={pending === student.id}
                          onPick={(choice) => save(student, choice)}
                        />
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}

function ChoiceGroup({
  title,
  choices,
  record,
  disabled,
  onPick,
}: {
  title: string
  choices: Choice[]
  record: Attendance | undefined
  disabled: boolean
  onPick: (choice: Choice) => void
}) {
  return (
    <div>
      <p className="mb-1.5 text-[11px] font-semibold uppercase tracking-wide text-ink-400">{title}</p>
      <div className="flex flex-wrap gap-2">
        {choices.map((choice) => {
          const active = isActive(record, choice)
          return (
            <button
              key={choice.key}
              type="button"
              disabled={disabled}
              onClick={() => onPick(choice)}
              aria-pressed={active}
              className={cn(
                "flex items-center gap-1.5 rounded-lg border px-3 py-2 text-sm font-medium transition-colors disabled:opacity-50",
                active
                  ? cn(ATTENDANCE_COLORS[choice.status], "border-transparent")
                  : "border-ink-200 text-ink-600 hover:bg-ink-50 dark:border-ink-700 dark:text-ink-300 dark:hover:bg-ink-800"
              )}
            >
              <choice.icon className="h-4 w-4" /> {choice.label}
            </button>
          )
        })}
      </div>
    </div>
  )
}
