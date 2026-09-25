import { type FormEvent, useMemo, useState } from "react"
import { ChevronLeft, ChevronRight, MessageSquareText } from "lucide-react"
import toast from "react-hot-toast"
import { useFetch } from "../../hooks/useFetch"
import { api, getErrorMessage } from "../../lib/api"
import { useAccess } from "../../lib/access"
import { Card, CardContent, CardHeader, CardTitle } from "../ui/Card"
import { Button } from "../ui/Button"
import { Field, Input } from "../ui/Input"
import { Modal } from "../ui/Modal"
import { EmptyState } from "../ui/EmptyState"
import { Skeleton } from "../ui/Skeleton"
import { ATTENDANCE_COLORS, ATTENDANCE_LABELS, attendanceLabel } from "../../lib/format"
import { cn } from "../../lib/cn"
import type { Attendance, AttendanceStatus, Paginated } from "../../types"
import { t } from "../../i18n"

/** A pupil's month at a glance (+ the reason dialog for an absent day). Shared by the family
 * view (student / parent) and the director's per-pupil view. */
export const MONTHS_UZ = [
  t("Yanvar"), t("Fevral"), t("Mart"), t("Aprel"), t("May"), t("Iyun"),
  t("Iyul"), t("Avgust"), t("Sentabr"), t("Oktabr"), t("Noyabr"), t("Dekabr"),
]

export function AttendanceCalendar({ studentId }: { studentId: number }) {
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
                    title={record ? attendanceLabel(record.status, record.absence_reason) : undefined}
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
  const { can } = useAccess()
  const canSubmit = can("submit_absence_reason")

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    if (!record) return
    setLoading(true)
    try {
      await api.patch(`/attendance/${record.id}/submit_reason/`, { parent_reason: reason })
      toast.success(t("Sabab yuborildi"))
      onDone()
    } catch (err) {
      toast.error(getErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  return (
    <Modal open={!!target} onClose={onClose} title={target ? t("{date} — kelmagan sabab", { date: target.date }) : ""}>
      {record?.parent_reason && !canSubmit ? (
        <p className="rounded-xl bg-ink-50 p-3 text-sm text-ink-700 dark:bg-ink-800 dark:text-ink-200">{record.parent_reason}</p>
      ) : canSubmit ? (
        <form onSubmit={handleSubmit} className="space-y-4">
          <Field label={t("Sababni kiriting")}>
            <Input value={reason} onChange={(e) => setReason(e.target.value)} placeholder={t("Masalan: farzandim kasal edi")} required />
          </Field>
          <Button type="submit" className="w-full" loading={loading}>
            {t("Yuborish")}
          </Button>
        </form>
      ) : (
        <EmptyState title={t("Sabab kiritilmagan")} description={t("Ota-ona hali sabab yubormagan")} />
      )}
    </Modal>
  )
}
