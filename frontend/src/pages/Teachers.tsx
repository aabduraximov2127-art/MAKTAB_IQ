import { useState } from "react"
import { Pencil, Plus, Search, Trash2 } from "lucide-react"
import toast from "react-hot-toast"
import { useFetch } from "../hooks/useFetch"
import { api, getErrorMessage } from "../lib/api"
import { useAccess } from "../lib/access"
import { Button } from "../components/ui/Button"
import { ConfirmButton } from "../components/ui/ConfirmButton"
import { TeacherFormModal } from "../components/teachers/TeacherFormModal"
import { PageHeader } from "../components/ui/PageHeader"
import { Input } from "../components/ui/Input"
import { Select } from "../components/ui/Select"
import { Skeleton } from "../components/ui/Skeleton"
import { DataTable, type Column } from "../components/ui/Table"
import { Pagination } from "../components/ui/Pagination"
import { Drawer } from "../components/ui/Drawer"
import { Avatar } from "../components/ui/Avatar"
import { Badge } from "../components/ui/Badge"
import { ATTENDANCE_LABELS, fullName } from "../lib/format"
import { weekdayUz } from "../lib/date"
import type { Lesson, Paginated, Subject, TeacherAttendance, TeacherProfile } from "../types"
import { t } from "../i18n"

const PAGE_SIZE = 10

/** ISO date (yyyy-mm-dd) in the school's local time, ``days`` from today. */
function isoFromToday(days = 0) {
  const d = new Date()
  d.setDate(d.getDate() + days)
  return new Date(d.getTime() - d.getTimezoneOffset() * 60000).toISOString().slice(0, 10)
}

export default function TeachersPage() {
  const { hasRole, can } = useAccess()
  const canManage = can("manage_teachers") // add / edit / delete teachers
  const [formTeacher, setFormTeacher] = useState<TeacherProfile | "new" | null>(null)
  // The director can pick any teacher from a list and see how they work: subjects, the coming
  // week's lessons and the last month's attendance.
  const isDirector = hasRole("DIRECTOR")
  const { data: everyone } = useFetch<Paginated<TeacherProfile>>(isDirector ? "/teachers/?page_size=100" : null)
  const [search, setSearch] = useState("")
  const [page, setPage] = useState(1)
  const [selected, setSelected] = useState<TeacherProfile | null>(null)

  const query = new URLSearchParams({ page: String(page), page_size: String(PAGE_SIZE) })
  if (search) query.set("search", search)

  const { data, loading, refetch } = useFetch<Paginated<TeacherProfile>>(`/teachers/?${query.toString()}`, [page, search])

  async function removeTeacher(teacher: TeacherProfile) {
    try {
      await api.delete(`/teachers/${teacher.id}/`)
      toast.success(t("O'qituvchi o'chirildi"))
      setSelected(null)
      refetch()
    } catch (err) {
      toast.error(getErrorMessage(err))
    }
  }

  const columns: Column<TeacherProfile>[] = [
    {
      key: "name",
      header: t("O'qituvchi"),
      render: (row) => (
        <div className="flex items-center gap-3">
          <Avatar name={fullName(row.user)} src={row.avatar} size="sm" />
          <div className="min-w-0">
            <p className="truncate font-medium text-ink-800 dark:text-ink-100">{fullName(row.user)}</p>
            <p className="truncate text-xs text-ink-400">{row.teacher_id}</p>
          </div>
        </div>
      ),
    },
    {
      key: "experience",
      header: t("Tajriba"),
      render: (row) => <Badge tone="brand">{row.experience_years} yil</Badge>,
    },
    { key: "phone", header: t("Telefon"), render: (row) => row.user.phone || "—", hideOnMobile: true },
    { key: "email", header: t("Email"), render: (row) => row.user.email || "—", hideOnMobile: true },
  ]

  return (
    <div>
      <PageHeader
        title={t("O'qituvchilar")}
        description={t("Maktabdagi barcha o'qituvchilar ro'yxati")}
        actions={
          canManage && (
            <Button onClick={() => setFormTeacher("new")}>
              <Plus className="h-4 w-4" /> {t("Yangi o'qituvchi")}
            </Button>
          )
        }
      />

      {isDirector && (
        <div className="mb-4 max-w-xs">
          <Select
            value={selected?.id ?? ""}
            onChange={(e) => setSelected(everyone?.results.find((x) => String(x.id) === e.target.value) ?? null)}
            aria-label={t("O'qituvchini tanlang...")}
          >
            <option value="">{t("O'qituvchini tanlang...")}</option>
            {everyone?.results.map((teacher) => (
              <option key={teacher.id} value={teacher.id}>
                {fullName(teacher.user)}
              </option>
            ))}
          </Select>
        </div>
      )}

      <div className="mb-4 max-w-xs">
        <Input
          icon={<Search className="h-4 w-4" />}
          placeholder={t("Ism yoki familiya bo'yicha qidirish...")}
          value={search}
          onChange={(e) => {
            setSearch(e.target.value)
            setPage(1)
          }}
        />
      </div>

      <DataTable
        columns={columns}
        rows={data?.results ?? []}
        keyField={(r) => r.id}
        loading={loading}
        emptyTitle={t("O'qituvchi topilmadi")}
        onRowClick={setSelected}
      />

      {data && <Pagination page={page} count={data.count} pageSize={PAGE_SIZE} onChange={setPage} />}

      <Drawer open={!!selected} onClose={() => setSelected(null)} title={selected ? fullName(selected.user) : ""} subtitle={selected?.teacher_id}>
        {selected && (
          <div className="space-y-5">
            <div className="flex justify-center">
              <Avatar name={fullName(selected.user)} src={selected.avatar} size="lg" />
            </div>
            <DetailRow label={t("Tajriba")} value={t("{n} yil", { n: selected.experience_years })} />
            <DetailRow label={t("Telefon")} value={selected.user.phone || "—"} />
            <DetailRow label={t("Email")} value={selected.user.email || "—"} />
            {isDirector && <TeacherWork teacher={selected} />}
            {canManage && (
              <div className="space-y-2 border-t border-ink-100 pt-4 dark:border-ink-800">
                <Button variant="outline" className="w-full" onClick={() => setFormTeacher(selected)}>
                  <Pencil className="h-4 w-4" /> {t("Tahrirlash")}
                </Button>
                <ConfirmButton
                  className="w-full"
                  label={t("O'qituvchini o'chirish")}
                  confirmLabel={t("Ishonchingiz komilmi? Hisob butunlay o'chadi")}
                  icon={<Trash2 className="h-4 w-4" />}
                  onConfirm={() => removeTeacher(selected)}
                />
              </div>
            )}
          </div>
        )}
      </Drawer>

      <TeacherFormModal
        open={formTeacher !== null}
        teacher={formTeacher === "new" ? null : formTeacher}
        onClose={() => setFormTeacher(null)}
        onDone={() => {
          setFormTeacher(null)
          setSelected(null)
          refetch()
        }}
      />
    </div>
  )
}

function TeacherWork({ teacher }: { teacher: TeacherProfile }) {
  const { data: subjects } = useFetch<Paginated<Subject>>("/subjects/?page_size=100")
  const { data: lessons } = useFetch<Paginated<Lesson>>(
    `/lessons/?teacher=${teacher.id}&page_size=200&ordering=date,start_time`,
    [teacher.id]
  )
  const { data: attendance } = useFetch<Paginated<TeacherAttendance>>(
    `/attendance/teacher-attendance/?teacher=${teacher.id}&page_size=100`,
    [teacher.id]
  )

  const subjectNames = teacher.subjects.map((id) => subjects?.results.find((s) => s.id === id)?.name).filter(Boolean) as string[]
  const today = isoFromToday()
  const weekAhead = isoFromToday(7)
  const upcoming = (lessons?.results ?? []).filter((l) => l.date >= today && l.date <= weekAhead)

  const monthAgo = isoFromToday(-30)
  const recent = (attendance?.results ?? []).filter((r) => r.date >= monthAgo)
  const count = (status: string) => recent.filter((r) => r.status === status).length
  const came = count("PRESENT") + count("LATE")
  const pct = recent.length ? Math.round((came / recent.length) * 100) : 0

  return (
    <div className="space-y-5">
      <div>
        <p className="mb-2 text-[11px] font-semibold uppercase tracking-wide text-ink-400">{t("Fanlar")}</p>
        {subjects ? (
          subjectNames.length > 0 ? (
            <div className="flex flex-wrap gap-2">
              {subjectNames.map((name) => (
                <Badge key={name} tone="brand">
                  {name}
                </Badge>
              ))}
            </div>
          ) : (
            <p className="text-sm text-ink-400">—</p>
          )
        ) : (
          <Skeleton className="h-6 w-1/2" />
        )}
      </div>

      <div>
        <p className="mb-2 text-[11px] font-semibold uppercase tracking-wide text-ink-400">{t("Yaqin 7 kundagi darslar")}</p>
        {!lessons ? (
          <Skeleton className="h-16 w-full" />
        ) : upcoming.length === 0 ? (
          <p className="text-sm text-ink-400">{t("Dars yo'q")}</p>
        ) : (
          <ul className="space-y-1.5">
            {upcoming.slice(0, 8).map((l) => (
              <li key={l.id} className="flex items-center justify-between gap-3 rounded-lg bg-ink-50 px-3 py-2 text-sm dark:bg-ink-800/60">
                <span className="truncate text-ink-800 dark:text-ink-100">
                  {l.subject_name} · {l.class_room_name}
                </span>
                <span className="shrink-0 text-xs text-ink-500 dark:text-ink-400">
                  {weekdayUz(l.date)} {l.start_time.slice(0, 5)}
                </span>
              </li>
            ))}
          </ul>
        )}
      </div>

      <div>
        <p className="mb-2 text-[11px] font-semibold uppercase tracking-wide text-ink-400">{t("Ish davomati (30 kun)")}</p>
        {!attendance ? (
          <Skeleton className="h-10 w-full" />
        ) : recent.length === 0 ? (
          <p className="text-sm text-ink-400">{t("Belgilanmagan")}</p>
        ) : (
          <div className="flex flex-wrap gap-2">
            <Badge tone="success">
              {ATTENDANCE_LABELS.PRESENT}: {count("PRESENT")}
            </Badge>
            <Badge tone="warning">
              {ATTENDANCE_LABELS.LATE}: {count("LATE")}
            </Badge>
            <Badge tone="danger">
              {ATTENDANCE_LABELS.ABSENT}: {count("ABSENT")}
            </Badge>
            <Badge tone="info">
              {ATTENDANCE_LABELS.EXCUSED}: {count("EXCUSED")}
            </Badge>
            <Badge tone="brand">{pct}%</Badge>
          </div>
        )}
      </div>
    </div>
  )
}

function DetailRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between border-b border-ink-100 pb-3 text-sm dark:border-ink-800">
      <span className="text-ink-500 dark:text-ink-400">{label}</span>
      <span className="font-medium text-ink-800 dark:text-ink-100">{value}</span>
    </div>
  )
}
