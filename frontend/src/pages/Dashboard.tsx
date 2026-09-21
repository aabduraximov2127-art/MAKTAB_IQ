import { useMemo } from "react"
import { Link } from "react-router-dom"
import {
  Bar,
  BarChart,
  CartesianGrid,
  PolarAngleAxis,
  PolarGrid,
  Radar,
  RadarChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts"
import {
  BadgeCheck,
  BookOpenCheck,
  CalendarDays,
  ClipboardCheck,
  GraduationCap,
  School,
  Sparkles,
  UserRound,
  Users,
  UsersRound,
} from "lucide-react"
import { useAuthStore } from "../store/auth"
import { useFetch } from "../hooks/useFetch"
import { StatCard } from "../components/ui/StatCard"
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/Card"
import { PageHeader } from "../components/ui/PageHeader"
import { EmptyState } from "../components/ui/EmptyState"
import { Skeleton, CardSkeleton } from "../components/ui/Skeleton"
import { LessonRow, LessonRowSkeleton } from "../components/shared/LessonRow"
import { Badge } from "../components/ui/Badge"
import { todayISO, weekdayUz } from "../lib/date"
import { fullName, formatDate, gradeColor } from "../lib/format"
import type {
  AdminAnalytics,
  Announcement,
  ClassRoom,
  Grade,
  Lesson,
  Paginated,
  StudentProgress,
} from "../types"

export default function DashboardPage() {
  const user = useAuthStore((s) => s.user)
  if (!user) return null

  if (user.role === "ADMIN" || user.role === "SUPERADMIN") return <AdminDashboard />
  if (user.role === "TEACHER") return <TeacherDashboard />
  if (user.role === "STUDENT") return <StudentDashboard />
  return <ParentDashboard />
}

/* ------------------------------- ADMIN -------------------------------- */

function AdminDashboard() {
  const { data, loading } = useFetch<AdminAnalytics>("/analytics/admin/")
  const { data: announcements } = useFetch<Paginated<Announcement>>("/notifications/announcements/?page_size=4")

  // Only true percentages share this axis — average_grades is on a 0-10 scale and
  // gets its own MiniStat below instead of being squashed onto a 0-100 bar chart.
  const chartData = useMemo(
    () =>
      data
        ? [
            { name: "Davomat", value: data.attendance_percentage },
            { name: "Uy vazifasi", value: data.homework_completion },
            { name: "Test", value: data.quiz_average },
          ]
        : [],
    [data]
  )

  return (
    <div>
      <PageHeader title="Boshqaruv paneli" description="Maktabingizning umumiy holati bir qarashda" />

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {loading || !data ? (
          Array.from({ length: 4 }).map((_, i) => <CardSkeleton key={i} />)
        ) : (
          <>
            <StatCard label="Jami o'quvchilar" value={data.total_students} icon={Users} tone="brand" delay={0} />
            <StatCard label="Jami o'qituvchilar" value={data.total_teachers} icon={UsersRound} tone="accent" delay={0.05} />
            <StatCard label="Sinflar" value={data.total_classes} icon={School} tone="sky" delay={0.1} />
            <StatCard
              label="Faol foydalanuvchilar"
              value={data.active_users}
              icon={Sparkles}
              tone="emerald"
              delay={0.15}
            />
          </>
        )}
      </div>

      <div className="mt-6 grid grid-cols-1 gap-4 xl:grid-cols-3">
        <Card className="xl:col-span-2">
          <CardHeader>
            <CardTitle>Umumiy ko'rsatkichlar</CardTitle>
          </CardHeader>
          <CardContent>
            {loading || !data ? (
              <Skeleton className="h-64 w-full" />
            ) : (
              <ResponsiveContainer width="100%" height={260}>
                <BarChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} className="stroke-ink-100 dark:stroke-ink-800" />
                  <XAxis dataKey="name" tick={{ fontSize: 12, fill: "var(--color-ink-400)" }} axisLine={false} tickLine={false} />
                  <YAxis tick={{ fontSize: 12, fill: "var(--color-ink-400)" }} axisLine={false} tickLine={false} unit="%" />
                  <Tooltip
                    contentStyle={{ borderRadius: 12, border: "none", boxShadow: "var(--shadow-soft-lg)" }}
                    formatter={(v) => [`${v}%`, "Qiymat"]}
                  />
                  <Bar dataKey="value" radius={[8, 8, 0, 0]} fill="var(--color-brand-500)" maxBarSize={56} />
                </BarChart>
              </ResponsiveContainer>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>So'nggi e'lonlar</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {!announcements ? (
              <Skeleton className="h-40 w-full" />
            ) : announcements.results.length === 0 ? (
              <EmptyState title="E'lonlar yo'q" />
            ) : (
              announcements.results.map((a) => (
                <div key={a.id} className="rounded-xl border border-ink-100 p-3 dark:border-ink-800">
                  <div className="flex items-center justify-between gap-2">
                    <p className="truncate text-sm font-semibold text-ink-800 dark:text-ink-100">{a.title}</p>
                    {a.priority === "HIGH" && <Badge tone="danger">Muhim</Badge>}
                  </div>
                  <p className="mt-1 line-clamp-2 text-xs text-ink-500 dark:text-ink-400">{a.content}</p>
                </div>
              ))
            )}
            <Link to="/announcements" className="block text-center text-sm font-medium text-brand-600 dark:text-brand-400">
              Barchasini ko'rish →
            </Link>
          </CardContent>
        </Card>
      </div>

      {data && (
        <div className="mt-4 grid grid-cols-2 gap-4 sm:grid-cols-5">
          <MiniStat label="O'rtacha baho" value={`${data.average_grades} / 10`} tone="brand" />
          <MiniStat label="Bugun kelmagan" value={data.absent_students} tone="rose" />
          <MiniStat label="O'qituvchi davomati" value={`${data.teacher_attendance_percentage}%`} tone="sky" />
          <MiniStat label="Uy vazifa bajarilishi" value={`${data.homework_completion}%`} tone="emerald" />
          <MiniStat label="Test o'rtachasi" value={`${data.quiz_average}%`} tone="brand" />
        </div>
      )}
    </div>
  )
}

const MINI_STAT_TONE_CLASSES: Record<string, string> = {
  rose: "text-rose-600 dark:text-rose-400",
  sky: "text-sky-600 dark:text-sky-400",
  emerald: "text-emerald-600 dark:text-emerald-400",
  brand: "text-brand-600 dark:text-brand-400",
}

function MiniStat({ label, value, tone }: { label: string; value: string | number; tone: string }) {
  return (
    <div className="rounded-2xl border border-ink-100 bg-white p-4 dark:border-ink-800 dark:bg-ink-900">
      <p className="text-xs font-medium text-ink-500 dark:text-ink-400">{label}</p>
      <p className={`mt-1.5 font-display text-xl font-bold ${MINI_STAT_TONE_CLASSES[tone]}`}>{value}</p>
    </div>
  )
}

/* ------------------------------ TEACHER -------------------------------- */

function TeacherDashboard() {
  const { data: lessons, loading: lessonsLoading } = useFetch<Paginated<Lesson>>(
    `/lessons/?date=${todayISO()}&ordering=start_time`
  )
  const { data: classes } = useFetch<Paginated<ClassRoom>>("/classes/?page_size=8")

  return (
    <div>
      <PageHeader
        title="Xush kelibsiz 👋"
        description={`Bugun ${weekdayUz(todayISO())}, ${formatDate(todayISO())}`}
      />

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <StatCard label="Bugungi darslar" value={lessons?.count ?? "—"} icon={CalendarDays} tone="brand" />
        <StatCard label="Mening sinflarim" value={classes?.count ?? "—"} icon={School} tone="accent" />
        <StatCard
          label="Jami o'quvchilar"
          value={classes?.results.reduce((sum, c) => sum + (c.student_count ?? 0), 0) ?? "—"}
          icon={Users}
          tone="emerald"
        />
      </div>

      <div className="mt-6 grid grid-cols-1 gap-4 xl:grid-cols-3">
        <Card className="xl:col-span-2">
          <CardHeader>
            <CardTitle>Bugungi dars jadvali</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2.5">
            {lessonsLoading ? (
              Array.from({ length: 3 }).map((_, i) => <LessonRowSkeleton key={i} />)
            ) : !lessons || lessons.results.length === 0 ? (
              <EmptyState icon={CalendarDays} title="Bugun darsingiz yo'q" description="Yaxshi dam oling!" />
            ) : (
              lessons.results.map((l) => <LessonRow key={l.id} lesson={l} />)
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Sinflarim</CardTitle>
          </CardHeader>
          <CardContent>
            {!classes ? (
              <Skeleton className="h-56 w-full" />
            ) : (
              <ResponsiveContainer width="100%" height={220}>
                <BarChart data={classes.results.map((c) => ({ name: c.name, count: c.student_count }))} layout="vertical">
                  <XAxis type="number" hide />
                  <YAxis dataKey="name" type="category" width={48} tick={{ fontSize: 12, fill: "var(--color-ink-400)" }} axisLine={false} tickLine={false} />
                  <Tooltip contentStyle={{ borderRadius: 12, border: "none", boxShadow: "var(--shadow-soft-lg)" }} />
                  <Bar dataKey="count" fill="var(--color-accent-500)" radius={[0, 8, 8, 0]} maxBarSize={18} />
                </BarChart>
              </ResponsiveContainer>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

/* ------------------------------ STUDENT -------------------------------- */

function StudentDashboard() {
  const { data: progress, loading: progressLoading } = useFetch<StudentProgress>("/analytics/progress/")
  const { data: lessons, loading: lessonsLoading } = useFetch<Paginated<Lesson>>(
    `/lessons/?date=${todayISO()}&ordering=start_time`
  )
  const { data: grades } = useFetch<Paginated<Grade>>("/grades/?ordering=-created_at&page_size=5")

  const radarData = useMemo(
    () =>
      progress
        ? [
            // average_grade is 0-10 — scaled x10 here only so it shares the same
            // 0-100 axis as the percentage metrics; the tooltip below un-scales it.
            { metric: "Baho", value: progress.average_grade * 10, raw: progress.average_grade },
            { metric: "Davomat", value: progress.attendance_percentage, raw: progress.attendance_percentage },
            { metric: "Uy vazifa", value: progress.homework_completion, raw: progress.homework_completion },
            { metric: "Test", value: progress.quiz_average, raw: progress.quiz_average },
          ]
        : [],
    [progress]
  )

  return (
    <div>
      <PageHeader title="Xush kelibsiz 👋" description="Bugungi jadval va progressingiz" />

      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        {progressLoading || !progress ? (
          Array.from({ length: 4 }).map((_, i) => <CardSkeleton key={i} />)
        ) : (
          <>
            <StatCard label="O'rtacha baho" value={progress.average_grade} icon={GraduationCap} tone="brand" />
            <StatCard label="Davomat" value={`${progress.attendance_percentage}%`} icon={ClipboardCheck} tone="emerald" />
            <StatCard label="Uy vazifa" value={`${progress.homework_completion}%`} icon={BookOpenCheck} tone="accent" />
            <StatCard label="Test o'rtachasi" value={`${progress.quiz_average}%`} icon={BadgeCheck} tone="sky" />
          </>
        )}
      </div>

      <div className="mt-6 grid grid-cols-1 gap-4 xl:grid-cols-3">
        <Card>
          <CardHeader>
            <CardTitle>Umumiy progress</CardTitle>
          </CardHeader>
          <CardContent>
            {!progress ? (
              <Skeleton className="h-64 w-full" />
            ) : (
              <ResponsiveContainer width="100%" height={260}>
                <RadarChart data={radarData}>
                  <PolarGrid className="stroke-ink-100 dark:stroke-ink-800" />
                  <PolarAngleAxis dataKey="metric" tick={{ fontSize: 12, fill: "var(--color-ink-500)" }} />
                  <Radar dataKey="value" stroke="var(--color-brand-500)" fill="var(--color-brand-500)" fillOpacity={0.3} />
                  <Tooltip
                    contentStyle={{ borderRadius: 12, border: "none", boxShadow: "var(--shadow-soft-lg)" }}
                    formatter={(_value, name, props) => {
                      const point = props.payload as { metric: string; raw: number }
                      return [`${point.raw}${point.metric === "Baho" ? "/10" : "%"}`, name]
                    }}
                  />
                </RadarChart>
              </ResponsiveContainer>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Bugungi darslar</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2.5">
            {lessonsLoading ? (
              Array.from({ length: 3 }).map((_, i) => <LessonRowSkeleton key={i} />)
            ) : !lessons || lessons.results.length === 0 ? (
              <EmptyState icon={CalendarDays} title="Bugun darsingiz yo'q" />
            ) : (
              lessons.results.map((l) => <LessonRow key={l.id} lesson={l} />)
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>So'nggi baholar</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {!grades ? (
              <Skeleton className="h-56 w-full" />
            ) : grades.results.length === 0 ? (
              <EmptyState title="Hali baho yo'q" />
            ) : (
              grades.results.map((g) => (
                <div key={g.id} className="flex items-center justify-between rounded-xl border border-ink-100 px-3.5 py-2.5 dark:border-ink-800">
                  <div>
                    <p className="text-sm font-medium text-ink-800 dark:text-ink-100">{g.subject_name}</p>
                    <p className="text-xs text-ink-400">{formatDate(g.created_at)}</p>
                  </div>
                  <span className={`font-display text-lg font-bold ${gradeColor(g.value)}`}>{g.value}</span>
                </div>
              ))
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

/* ------------------------------- PARENT -------------------------------- */

function ParentDashboard() {
  const { data: students, loading } = useFetch<Paginated<{ id: number; user: { first_name: string; last_name: string }; class_room_name: string | null }>>(
    "/students/"
  )

  return (
    <div>
      <PageHeader title="Xush kelibsiz 👋" description="Farzandlaringiz progressi" />

      {loading ? (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          {Array.from({ length: 2 }).map((_, i) => (
            <CardSkeleton key={i} />
          ))}
        </div>
      ) : !students || students.results.length === 0 ? (
        <EmptyState icon={UserRound} title="Farzand topilmadi" description="Admin bilan bog'laning" />
      ) : (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-3">
          {students.results.map((child) => (
            <ChildProgressCard key={child.id} childId={child.id} name={fullName(child.user)} className={child.class_room_name} />
          ))}
        </div>
      )}
    </div>
  )
}

function ChildProgressCard({ childId, name, className }: { childId: number; name: string; className: string | null }) {
  const { data: progress, loading } = useFetch<StudentProgress>(`/analytics/progress/?student=${childId}`)

  return (
    <Card>
      <CardHeader>
        <div>
          <CardTitle>{name}</CardTitle>
          <p className="text-xs text-ink-400">{className ?? "Sinf biriktirilmagan"}</p>
        </div>
        <Link to="/grades" className="text-xs font-medium text-brand-600 dark:text-brand-400">
          Batafsil →
        </Link>
      </CardHeader>
      <CardContent className="space-y-3">
        {loading || !progress ? (
          <Skeleton className="h-32 w-full" />
        ) : (
          <>
            <ProgressBar label="O'rtacha baho" value={progress.average_grade} suffix="" max={10} />
            <ProgressBar label="Davomat" value={progress.attendance_percentage} suffix="%" max={100} />
            <ProgressBar label="Uy vazifa" value={progress.homework_completion} suffix="%" max={100} />
            <ProgressBar label="Test" value={progress.quiz_average} suffix="%" max={100} />
          </>
        )}
      </CardContent>
    </Card>
  )
}

function ProgressBar({ label, value, suffix, max }: { label: string; value: number; suffix: string; max: number }) {
  const pct = Math.min(100, (value / max) * 100)
  return (
    <div>
      <div className="mb-1 flex items-center justify-between text-xs">
        <span className="text-ink-500 dark:text-ink-400">{label}</span>
        <span className="font-semibold text-ink-700 dark:text-ink-200">
          {value}
          {suffix}
        </span>
      </div>
      <div className="h-2 overflow-hidden rounded-full bg-ink-100 dark:bg-ink-800">
        <div
          className="h-full rounded-full bg-gradient-to-r from-brand-500 to-accent-400 transition-all duration-700"
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  )
}
