import { useEffect, useMemo, useState } from "react"
import { CalendarPlus, Search, Trash2 } from "lucide-react"
import toast from "react-hot-toast"
import { useFetch } from "../../hooks/useFetch"
import { api, getErrorMessage } from "../../lib/api"
import { useAccess } from "../../lib/access"
import { matchesQuery } from "../../lib/search"
import { cn } from "../../lib/cn"
import { Button } from "../ui/Button"
import { EmptyState } from "../ui/EmptyState"
import { Input } from "../ui/Input"
import { Select } from "../ui/Select"
import { Skeleton } from "../ui/Skeleton"
import { Tabs } from "../ui/Tabs"
import { LessonRow } from "../shared/LessonRow"
import { AddLessonModal } from "./AddLessonModal"
import { LessonsBoard } from "./LessonsBoard"
import type { ClassRoom, Lesson, Paginated } from "../../types"
import { t } from "../../i18n"

/** Today's date as the school sees it (local, not UTC). */
function localToday() {
  const now = new Date()
  return new Date(now.getTime() - now.getTimezoneOffset() * 60000).toISOString().slice(0, 10)
}

/**
 * The deputy director's timetable. Pick a class and a day, narrow the lessons with the search box
 * ("ma" finds Matematika), and add or remove lessons; the "Hafta" tab is the familiar weekly board
 * for the same class and search. Everything is confined to the deputy's own school by the API.
 */
export function DeputySchedule({ weekDays }: { weekDays: Date[] }) {
  const { can } = useAccess()
  const canManage = can("manage_schedule")
  const [view, setView] = useState<"day" | "week">("day")
  const [classId, setClassId] = useState("")
  const [date, setDate] = useState(localToday())
  const [search, setSearch] = useState("")
  const [addOpen, setAddOpen] = useState(false)
  const [refresh, setRefresh] = useState(0) // bumped after a lesson is added so the day list reloads

  const { data: classes } = useFetch<Paginated<ClassRoom>>("/classes/?page_size=100&ordering=name")
  const classQuery = classId ? `&class_room=${classId}` : ""

  const filter = useMemo(
    () => (lesson: Lesson) => matchesQuery(search, lesson.subject_name, lesson.teacher_name, lesson.room),
    [search]
  )

  return (
    <>
      <div className="mb-5 flex flex-wrap items-center gap-3">
        <Tabs
          tabs={[
            { key: "day", label: t("Kunlik") },
            { key: "week", label: t("Haftalik") },
          ]}
          active={view}
          onChange={(key) => setView(key as "day" | "week")}
        />
        {canManage && (
          <Button className="ml-auto" onClick={() => setAddOpen(true)}>
            <CalendarPlus className="h-4 w-4" /> {t("Yangi dars")}
          </Button>
        )}
      </div>

      <div className="mb-5 flex flex-wrap items-center gap-3">
        <Select value={classId} onChange={(e) => setClassId(e.target.value)} className="min-w-[12rem]" aria-label={t("Sinfni tanlang...")}>
          <option value="">{t("Barcha sinflar")}</option>
          {classes?.results.map((c) => (
            <option key={c.id} value={c.id}>
              {c.name}
            </option>
          ))}
        </Select>
        {view === "day" && (
          <Input type="date" value={date} onChange={(e) => setDate(e.target.value || localToday())} className="max-w-[12rem]" aria-label={t("Kun")} />
        )}
        <div className="min-w-[14rem] flex-1 sm:max-w-xs">
          <Input
            icon={<Search className="h-4 w-4" />}
            placeholder={t("Fan, o'qituvchi yoki xona bo'yicha qidirish...")}
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            aria-label={t("Qidirish")}
          />
        </div>
      </div>

      {view === "day" ? (
        <DayLessons date={date} classQuery={classQuery} filter={filter} canManage={canManage} searching={!!search.trim()} refresh={refresh} />
      ) : (
        <LessonsBoard key={`week-${classId}`} query={classQuery} weekDays={weekDays} filter={filter} />
      )}

      <AddLessonModal
        open={addOpen}
        defaultClassId={classId}
        defaultDate={date}
        onClose={() => setAddOpen(false)}
        onDone={() => {
          setAddOpen(false)
          setRefresh((n) => n + 1)
        }}
      />
    </>
  )
}

/** The lessons of one day (of one class, or of the whole school), newest-first search applied. */
function DayLessons({
  date,
  classQuery,
  filter,
  canManage,
  searching,
  refresh,
}: {
  date: string
  classQuery: string
  filter: (lesson: Lesson) => boolean
  canManage: boolean
  searching: boolean
  refresh: number
}) {
  const { data, loading, refetch } = useFetch<Paginated<Lesson>>(
    `/lessons/?date=${date}&ordering=start_time&page_size=200${classQuery}`,
    [refresh]
  )
  const [confirmId, setConfirmId] = useState<number | null>(null)
  const lessons = useMemo(() => (data?.results ?? []).filter(filter), [data, filter])

  // the "are you sure?" state lapses on its own
  useEffect(() => {
    if (confirmId === null) return
    const timer = setTimeout(() => setConfirmId(null), 4000)
    return () => clearTimeout(timer)
  }, [confirmId])

  async function remove(lesson: Lesson) {
    if (confirmId !== lesson.id) {
      setConfirmId(lesson.id)
      return
    }
    try {
      await api.delete(`/lessons/${lesson.id}/`)
      toast.success(t("Dars o'chirildi"))
      setConfirmId(null)
      refetch()
    } catch (err) {
      toast.error(getErrorMessage(err))
    }
  }

  if (loading && !data) {
    return (
      <div className="space-y-2">
        {Array.from({ length: 4 }).map((_, i) => (
          <Skeleton key={i} className="h-16 w-full" />
        ))}
      </div>
    )
  }
  if (!data || data.results.length === 0) {
    return (
      <EmptyState
        title={t("Bu kunda dars yo'q")}
        description={canManage ? t("«Yangi dars» tugmasi bilan dars qo'shing") : undefined}
      />
    )
  }
  if (lessons.length === 0) {
    return <EmptyState title={t("Hech narsa topilmadi")} description={searching ? t("Qidiruv so'zini o'zgartirib ko'ring") : undefined} />
  }

  return (
    <div className="space-y-2.5">
      {lessons.map((lesson) => (
        <div key={lesson.id} className="flex items-center gap-2">
          <div className="min-w-0 flex-1">
            <LessonRow lesson={lesson} />
          </div>
          {canManage && (
            <Button
              variant={confirmId === lesson.id ? "danger" : "outline"}
              size={confirmId === lesson.id ? "sm" : "icon"}
              onClick={() => remove(lesson)}
              aria-label={t("Darsni o'chirish")}
              className={cn(confirmId !== lesson.id && "h-10 w-10 shrink-0 text-ink-500 hover:text-rose-600")}
            >
              <Trash2 className="h-4 w-4" />
              {confirmId === lesson.id && t("Ishonchingiz komilmi?")}
            </Button>
          )}
        </div>
      ))}
    </div>
  )
}
