import { useMemo } from "react"
import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts"
import {
  Activity,
  AlertOctagon,
  BadgeCheck,
  BookOpenCheck,
  ClipboardCheck,
  GraduationCap,
  School,
  UserCheck,
  Users,
  UsersRound,
} from "lucide-react"
import { useFetch } from "../hooks/useFetch"
import { PageHeader } from "../components/ui/PageHeader"
import { StatCard } from "../components/ui/StatCard"
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/Card"
import { CardSkeleton, Skeleton } from "../components/ui/Skeleton"
import type { AdminAnalytics } from "../types"
import { t } from "../i18n"

const PIE_COLORS = ["var(--color-emerald-500, #10b981)", "var(--color-rose-500, #f43f5e)"]

export default function AnalyticsPage() {
  const { data, loading } = useFetch<AdminAnalytics>("/analytics/admin/")

  const pieData = useMemo(
    () =>
      data
        ? [
            { name: t("Kelganlar"), value: data.attendance_percentage },
            { name: t("Kelmaganlar"), value: Math.max(0, 100 - data.attendance_percentage) },
          ]
        : [],
    [data]
  )

  return (
    <div>
      <PageHeader title={t("Statistika")} description={t("Maktab bo'yicha to'liq analitik ko'rsatkichlar")} />

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-3">
        {loading || !data ? (
          Array.from({ length: 6 }).map((_, i) => <CardSkeleton key={i} />)
        ) : (
          <>
            <StatCard label={t("Jami o'quvchilar")} value={data.total_students} icon={Users} tone="brand" />
            <StatCard label={t("Jami o'qituvchilar")} value={data.total_teachers} icon={UsersRound} tone="accent" />
            <StatCard label={t("Sinflar")} value={data.total_classes} icon={School} tone="sky" />
            <StatCard label={t("Faol foydalanuvchilar")} value={data.active_users} icon={Activity} tone="emerald" />
            <StatCard label={t("Bugun kelmaganlar")} value={data.absent_students} icon={AlertOctagon} tone="rose" />
            <StatCard label={t("O'qituvchi davomati")} value={`${data.teacher_attendance_percentage}%`} icon={UserCheck} tone="brand" />
          </>
        )}
      </div>

      <div className="mt-6 grid grid-cols-1 gap-4 xl:grid-cols-3">
        <Card>
          <CardHeader>
            <CardTitle>{t("Davomat taqsimoti")}</CardTitle>
          </CardHeader>
          <CardContent>
            {loading || !data ? (
              <Skeleton className="h-56 w-full" />
            ) : (
              <ResponsiveContainer width="100%" height={220}>
                <PieChart>
                  <Pie data={pieData} dataKey="value" innerRadius={55} outerRadius={80} paddingAngle={3}>
                    {pieData.map((_, i) => (
                      <Cell key={i} fill={PIE_COLORS[i]} />
                    ))}
                  </Pie>
                  <Tooltip contentStyle={{ borderRadius: 12, border: "none", boxShadow: "var(--shadow-soft-lg)" }} formatter={(v) => `${v}%`} />
                </PieChart>
              </ResponsiveContainer>
            )}
            <div className="mt-2 flex justify-center gap-4 text-xs">
              <span className="flex items-center gap-1.5">
                <span className="h-2.5 w-2.5 rounded-full bg-emerald-500" /> Kelganlar
              </span>
              <span className="flex items-center gap-1.5">
                <span className="h-2.5 w-2.5 rounded-full bg-rose-500" /> Kelmaganlar
              </span>
            </div>
          </CardContent>
        </Card>

        <Card className="xl:col-span-2">
          <CardHeader>
            <CardTitle>{t("Batafsil ko'rsatkichlar")}</CardTitle>
          </CardHeader>
          <CardContent className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            {loading || !data ? (
              <Skeleton className="h-56 w-full sm:col-span-2" />
            ) : (
              <>
                <MetricRow icon={GraduationCap} label={t("O'rtacha baho")} value={data.average_grades} />
                <MetricRow icon={ClipboardCheck} label={t("Davomat")} value={`${data.attendance_percentage}%`} />
                <MetricRow icon={BookOpenCheck} label={t("Uy vazifa bajarilishi")} value={`${data.homework_completion}%`} />
                <MetricRow icon={BadgeCheck} label={t("Test o'rtachasi")} value={`${data.quiz_average}%`} />
              </>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

function MetricRow({ icon: Icon, label, value }: { icon: typeof GraduationCap; label: string; value: string | number }) {
  return (
    <div className="flex items-center justify-between rounded-xl border border-ink-100 p-3.5 dark:border-ink-800">
      <div className="flex items-center gap-2.5 text-sm text-ink-600 dark:text-ink-300">
        <Icon className="h-4 w-4 text-brand-500" /> {label}
      </div>
      <span className="font-display font-bold text-ink-900 dark:text-white">{value}</span>
    </div>
  )
}
