import { Link } from "react-router-dom"
import { Building2, GraduationCap, School, ShieldCheck, Sparkles, Users, UsersRound } from "lucide-react"
import { useFetch } from "../../hooks/useFetch"
import { StatCard } from "../ui/StatCard"
import { Card, CardContent, CardHeader, CardTitle } from "../ui/Card"
import { PageHeader } from "../ui/PageHeader"
import { Button } from "../ui/Button"
import { CardSkeleton } from "../ui/Skeleton"
import { DataTable, type Column } from "../ui/Table"
import type { SchoolStats, SystemAnalytics } from "../../types"
import { t } from "../../i18n"

/** The SuperAdmin's home: figures for the whole system and one row per school. */
export function SystemDashboard() {
  const { data, loading } = useFetch<SystemAnalytics>("/analytics/system/")

  const columns: Column<SchoolStats>[] = [
    { key: "name", header: t("Maktab"), render: (s) => <span className="font-medium text-ink-800 dark:text-ink-100">{s.name}</span> },
    { key: "students", header: t("O'quvchilar"), render: (s) => s.students },
    { key: "teachers", header: t("O'qituvchilar"), render: (s) => s.teachers, hideOnMobile: true },
    { key: "classes", header: t("Sinflar"), render: (s) => s.classes, hideOnMobile: true },
    { key: "admins", header: t("Adminlar"), render: (s) => s.admins },
    { key: "attendance", header: t("Davomat"), render: (s) => `${s.attendance_percentage}%`, hideOnMobile: true },
    { key: "grades", header: t("O'rtacha baho"), render: (s) => s.average_grades, hideOnMobile: true },
  ]

  return (
    <div>
      <PageHeader
        title={t("Tizim paneli")}
        description={t("Butun tizim va barcha maktablar bir qarashda")}
        actions={
          <Link to="/schools">
            <Button variant="outline">
              <Building2 className="h-4 w-4" /> {t("Maktablar")}
            </Button>
          </Link>
        }
      />

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-3">
        {loading || !data ? (
          Array.from({ length: 6 }).map((_, i) => <CardSkeleton key={i} />)
        ) : (
          <>
            <StatCard label={t("Maktablar")} value={data.total_schools} icon={Building2} tone="brand" delay={0} />
            <StatCard label={t("Adminlar")} value={data.total_admins} icon={ShieldCheck} tone="accent" delay={0.05} />
            <StatCard label={t("Jami o'quvchilar")} value={data.total_students} icon={Users} tone="sky" delay={0.1} />
            <StatCard label={t("Jami o'qituvchilar")} value={data.total_teachers} icon={UsersRound} tone="emerald" delay={0.15} />
            <StatCard label={t("Sinflar")} value={data.total_classes} icon={School} tone="rose" delay={0.2} />
            <StatCard label={t("Faol foydalanuvchilar")} value={data.active_users} icon={Sparkles} tone="brand" delay={0.25} />
          </>
        )}
      </div>

      <Card className="mt-6">
        <CardHeader>
          <CardTitle>{t("Maktablar bo'yicha")}</CardTitle>
          {data && (
            <span className="inline-flex items-center gap-1.5 text-xs text-ink-400">
              <GraduationCap className="h-3.5 w-3.5" /> {t("O'rtacha baho")}: {data.average_grades} / 10 · {t("Davomat")}: {data.attendance_percentage}%
            </span>
          )}
        </CardHeader>
        <CardContent>
          <DataTable
            columns={columns}
            rows={data?.schools ?? []}
            keyField={(s) => s.id}
            loading={loading}
            emptyTitle={t("Maktab topilmadi")}
          />
        </CardContent>
      </Card>
    </div>
  )
}
