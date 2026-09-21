import { Clock, DoorOpen } from "lucide-react"
import { shortName } from "../../lib/format"
import type { Lesson } from "../../types"

export function LessonRow({ lesson }: { lesson: Lesson }) {
  return (
    <div className="flex items-center gap-4 rounded-xl border border-ink-100 p-3.5 transition-colors hover:bg-ink-50/70 dark:border-ink-800 dark:hover:bg-ink-800/40">
      <div className="flex h-11 w-14 shrink-0 flex-col items-center justify-center rounded-lg bg-brand-50 text-brand-700 dark:bg-brand-500/10 dark:text-brand-300">
        <span className="text-xs font-bold leading-none">{lesson.start_time?.slice(0, 5)}</span>
        <span className="text-[10px] leading-none text-brand-400">{lesson.end_time?.slice(0, 5)}</span>
      </div>
      <div className="min-w-0 flex-1">
        <p className="truncate text-sm font-semibold text-ink-800 dark:text-ink-100">{lesson.subject_name}</p>
        <p className="truncate text-xs text-ink-500 dark:text-ink-400">
          {lesson.class_room_name} • {shortName(lesson.teacher_name)}
        </p>
      </div>
      <div className="flex shrink-0 items-center gap-1 text-xs text-ink-400">
        <DoorOpen className="h-3.5 w-3.5" /> {lesson.room}
      </div>
    </div>
  )
}

export function LessonRowSkeleton() {
  return (
    <div className="flex items-center gap-4 rounded-xl border border-ink-100 p-3.5 dark:border-ink-800">
      <Clock className="h-4 w-4 text-ink-300" />
      <div className="h-3 w-1/2 animate-pulse rounded bg-ink-100 dark:bg-ink-800" />
    </div>
  )
}
