import { useMemo, useState } from "react"
import { ChevronLeft, ChevronRight, Clock } from "lucide-react"
import { useFetch } from "../hooks/useFetch"
import { PageHeader } from "../components/ui/PageHeader"
import { Button } from "../components/ui/Button"
import { Card } from "../components/ui/Card"
import { EmptyState } from "../components/ui/EmptyState"
import { Skeleton } from "../components/ui/Skeleton"
import { cn } from "../lib/cn"
import { shortName } from "../lib/format"
import type { Lesson, Paginated } from "../types"
import { localeTag, t } from "../i18n"

const DAY_LABELS = [t("Dushanba"), t("Seshanba"), t("Chorshanba"), t("Payshanba"), t("Juma"), t("Shanba"), t("Yakshanba")]

function startOfWeek(offset: number) {
  const now = new Date()
  const day = (now.getDay() + 6) % 7 // 0 = Monday
  const monday = new Date(now)
  monday.setDate(now.getDate() - day + offset * 7)
  monday.setHours(0, 0, 0, 0)
  return monday
}

function toISO(d: Date) {
  return d.toISOString().slice(0, 10)
}

export default function SchedulePage() {
  const [weekOffset, setWeekOffset] = useState(0)
  const { data, loading } = useFetch<Paginated<Lesson>>("/lessons/?page_size=500&ordering=date,start_time")

  const monday = startOfWeek(weekOffset)
  const weekDays = useMemo(
    () =>
      Array.from({ length: 7 }, (_, i) => {
        const d = new Date(monday)
        d.setDate(monday.getDate() + i)
        return d
      }),
    [monday]
  )

  const todayISO = toISO(new Date())
  const lessonsByDate = useMemo(() => {
    const map = new Map<string, Lesson[]>()
    for (const lesson of data?.results ?? []) {
      const list = map.get(lesson.date) ?? []
      list.push(lesson)
      map.set(lesson.date, list)
    }
    return map
  }, [data])

  return (
    <div>
      <PageHeader
        title={t("Dars jadvali")}
        description={`${weekDays[0]!.toLocaleDateString(localeTag())} — ${weekDays[6]!.toLocaleDateString(localeTag())}`}
        actions={
          <div className="flex items-center gap-2">
            <Button variant="outline" size="icon" onClick={() => setWeekOffset((w) => w - 1)}>
              <ChevronLeft className="h-4 w-4" />
            </Button>
            <Button variant="outline" size="sm" onClick={() => setWeekOffset(0)}>
              {t("Shu hafta")}
            </Button>
            <Button variant="outline" size="icon" onClick={() => setWeekOffset((w) => w + 1)}>
              <ChevronRight className="h-4 w-4" />
            </Button>
          </div>
        }
      />

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-7">
        {weekDays.map((d, i) => {
          const iso = toISO(d)
          const lessons = (lessonsByDate.get(iso) ?? []).sort((a, b) => a.start_time.localeCompare(b.start_time))
          const isToday = iso === todayISO

          return (
            <Card key={iso} className={cn("flex flex-col", isToday && "ring-2 ring-brand-500")}>
              <div
                className={cn(
                  "flex items-center justify-between rounded-t-2xl px-4 py-3",
                  isToday ? "bg-brand-600 text-white" : "bg-ink-50 dark:bg-ink-800/60"
                )}
              >
                <div>
                  <p className={cn("text-xs font-semibold uppercase tracking-wide", isToday ? "text-brand-100" : "text-ink-400")}>
                    {DAY_LABELS[i]}
                  </p>
                  <p className={cn("font-display text-sm font-bold", isToday ? "text-white" : "text-ink-800 dark:text-ink-100")}>
                    {d.getDate()}.{d.getMonth() + 1}
                  </p>
                </div>
                {isToday && <span className="rounded-full bg-white/20 px-2 py-0.5 text-[10px] font-bold">BUGUN</span>}
              </div>

              <div className="flex-1 space-y-2 p-3">
                {loading ? (
                  <Skeleton className="h-16 w-full" />
                ) : lessons.length === 0 ? (
                  <p className="py-6 text-center text-xs text-ink-400">{t("Dars yo'q")}</p>
                ) : (
                  lessons.map((lesson) => (
                    <div key={lesson.id} className="rounded-xl border border-ink-100 p-2.5 dark:border-ink-800">
                      <div className="flex items-center gap-1 text-[11px] font-semibold text-brand-600 dark:text-brand-400">
                        <Clock className="h-3 w-3" /> {lesson.start_time.slice(0, 5)}–{lesson.end_time.slice(0, 5)}
                      </div>
                      <p className="mt-1 truncate text-sm font-medium text-ink-800 dark:text-ink-100">{lesson.subject_name}</p>
                      <p className="truncate text-xs text-ink-400">
                        {lesson.class_room_name} • {lesson.room}
                      </p>
                      <p className="mt-0.5 truncate text-xs font-medium text-brand-600 dark:text-brand-400">
                        {shortName(lesson.teacher_name)}
                      </p>
                    </div>
                  ))
                )}
              </div>
            </Card>
          )
        })}
      </div>

      {!loading && data?.results.length === 0 && (
        <div className="mt-6">
          <EmptyState title={t("Dars jadvali bo'sh")} description={t("Hozircha darslar kiritilmagan")} />
        </div>
      )}
    </div>
  )
}
