import { useMemo, useState } from "react"
import { ChevronLeft, ChevronRight } from "lucide-react"
import { useFetch } from "../hooks/useFetch"
import { PageHeader } from "../components/ui/PageHeader"
import { Button } from "../components/ui/Button"
import { EmptyState } from "../components/ui/EmptyState"
import { Tabs } from "../components/ui/Tabs"
import { DeputySchedule } from "../components/schedule/DeputySchedule"
import { LessonsBoard } from "../components/schedule/LessonsBoard"
import { Select } from "../components/ui/Select"
import { ClassStudentPicker, type PickerSelection } from "../components/shared/ClassStudentPicker"
import { useAccess } from "../lib/access"
import { fullName } from "../lib/format"
import type { Paginated, TeacherProfile } from "../types"
import { localeTag, t } from "../i18n"

function startOfWeek(offset: number) {
  const now = new Date()
  const day = (now.getDay() + 6) % 7 // 0 = Monday
  const monday = new Date(now)
  monday.setDate(now.getDate() - day + offset * 7)
  monday.setHours(0, 0, 0, 0)
  return monday
}

export default function SchedulePage() {
  const { hasRole } = useAccess()
  const [weekOffset, setWeekOffset] = useState(0)

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

      {hasRole("DIRECTOR") ? (
        <DirectorSchedule weekDays={weekDays} />
      ) : hasRole("DEPUTY_DIRECTOR") ? (
        <DeputySchedule weekDays={weekDays} />
      ) : hasRole("CLASS_TEACHER") ? (
        <ClassTeacherSchedule weekDays={weekDays} />
      ) : (
        <LessonsBoard query="" weekDays={weekDays} />
      )}
    </div>
  )
}

/**
 * The director browses the timetable in two tabs: one teacher's week, or a class's week (pick
 * the class, then optionally a pupil — a pupil follows the timetable of their class).
 */
function DirectorSchedule({ weekDays }: { weekDays: Date[] }) {
  const [tab, setTab] = useState<"teachers" | "students">("teachers")
  const [teacherId, setTeacherId] = useState("")
  const [picked, setPicked] = useState<PickerSelection>({ classRoom: null, student: null })
  const { data: teachers } = useFetch<Paginated<TeacherProfile>>("/teachers/?page_size=100")

  return (
    <>
      <div className="mb-5 flex flex-wrap items-center gap-3">
        <Tabs
          tabs={[
            { key: "teachers", label: t("O'qituvchilar") },
            { key: "students", label: t("O'quvchilar") },
          ]}
          active={tab}
          onChange={(key) => setTab(key as "teachers" | "students")}
        />
        {tab === "teachers" ? (
          <Select value={teacherId} onChange={(e) => setTeacherId(e.target.value)} className="min-w-[14rem]" aria-label={t("O'qituvchini tanlang...")}>
            <option value="">{t("O'qituvchini tanlang...")}</option>
            {teachers?.results.map((teacher) => (
              <option key={teacher.id} value={teacher.id}>
                {fullName(teacher.user)}
              </option>
            ))}
          </Select>
        ) : (
          <ClassStudentPicker onChange={setPicked} />
        )}
      </div>

      {tab === "teachers" ? (
        teacherId ? (
          <LessonsBoard key={`teacher-${teacherId}`} query={`&teacher=${teacherId}`} weekDays={weekDays} />
        ) : (
          <EmptyState title={t("O'qituvchini tanlang...")} description={t("Dars jadvalini ko'rish uchun o'qituvchini tanlang")} />
        )
      ) : picked.classRoom ? (
        <>
          <p className="mb-3 text-sm text-ink-500 dark:text-ink-400">
            {picked.student && <span className="font-semibold text-ink-800 dark:text-ink-100">{fullName(picked.student.user)} · </span>}
            {picked.classRoom.name}
          </p>
          <LessonsBoard key={`class-${picked.classRoom.id}`} query={`&class_room=${picked.classRoom.id}`} weekDays={weekDays} />
        </>
      ) : (
        <EmptyState title={t("Sinfni tanlang")} description={t("Dars jadvalini ko'rish uchun avval sinfni, keyin o'quvchini tanlang")} />
      )}
    </>
  )
}

/**
 * A class teacher gets two tabs: their own lessons, and the timetable of their ONE class —
 * nothing else (the API scopes the lessons the same way).
 */
function ClassTeacherSchedule({ weekDays }: { weekDays: Date[] }) {
  const { curatedClasses } = useAccess()
  const { data: me } = useFetch<TeacherProfile>("/teachers/me/")
  const [tab, setTab] = useState<"mine" | "class">("mine")
  const [classId, setClassId] = useState<number | null>(curatedClasses[0]?.id ?? null)

  const hasOwnLessons = !!me
  const active = hasOwnLessons ? tab : "class"
  const className = curatedClasses.find((c) => c.id === classId)?.name ?? ""

  const tabs = [
    ...(hasOwnLessons ? [{ key: "mine", label: t("Mening darslarim") }] : []),
    { key: "class", label: className ? `${t("Mening sinfim")} · ${className}` : t("Mening sinfim") },
  ]

  return (
    <>
      <div className="mb-5 flex flex-wrap items-center gap-3">
        <Tabs tabs={tabs} active={active} onChange={(key) => setTab(key as "mine" | "class")} />
        {active === "class" && curatedClasses.length > 1 && (
          <select
            value={classId ?? ""}
            onChange={(e) => setClassId(Number(e.target.value))}
            className="h-10 rounded-xl border border-ink-200 bg-white px-3 text-sm dark:border-ink-700 dark:bg-ink-900 dark:text-white"
          >
            {curatedClasses.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name}
              </option>
            ))}
          </select>
        )}
      </div>

      {active === "mine" && me ? (
        <LessonsBoard key="mine" query={`&teacher=${me.id}`} weekDays={weekDays} />
      ) : classId ? (
        <LessonsBoard key={`class-${classId}`} query={`&class_room=${classId}`} weekDays={weekDays} />
      ) : (
        <EmptyState title={t("Sizga sinf biriktirilmagan")} />
      )}
    </>
  )
}
