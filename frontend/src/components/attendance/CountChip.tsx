import { ATTENDANCE_SOLID, ATTENDANCE_UNMARKED } from "../../lib/format"
import { cn } from "../../lib/cn"
import type { AttendanceStatus } from "../../types"

/** A saturated "label: number" counter — the attendance colours at a glance. `status` omitted
 * means "not marked yet" (grey). */
export function CountChip({ status, label, count }: { status?: AttendanceStatus; label: string; count: number }) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-semibold shadow-sm",
        status ? ATTENDANCE_SOLID[status] : ATTENDANCE_UNMARKED
      )}
    >
      {label}
      <span className="rounded-full bg-black/15 px-1.5 py-px text-[11px] leading-4">{count}</span>
    </span>
  )
}
