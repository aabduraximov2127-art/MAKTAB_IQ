import { type FormEvent, type ReactNode, useState } from "react"
import { ChevronRight, GraduationCap, Plus, School } from "lucide-react"
import toast from "react-hot-toast"
import { useFetch } from "../hooks/useFetch"
import { api, getErrorMessage } from "../lib/api"
import { useAuthStore } from "../store/auth"
import { PageHeader } from "../components/ui/PageHeader"
import { Button } from "../components/ui/Button"
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/Card"
import { Field, Input } from "../components/ui/Input"
import { Select } from "../components/ui/Select"
import { Modal } from "../components/ui/Modal"
import { DataTable, type Column } from "../components/ui/Table"
import { EmptyState } from "../components/ui/EmptyState"
import { Skeleton } from "../components/ui/Skeleton"
import { Tabs } from "../components/ui/Tabs"
import { Avatar } from "../components/ui/Avatar"
import { formatDate, fullName, gradeCellClasses, gradeColor } from "../lib/format"
import type {
  AcademicYear,
  ClassRoom,
  Grade,
  Paginated,
  Quarter,
  StudentProfile,
  Subject,
} from "../types"
import { t } from "../i18n"

export default function GradesPage() {
  const user = useAuthStore((s) => s.user)
  if (user?.role === "SUPERADMIN") return <DrillDownGradesView />
  const isStaffOrTeacher = user?.role === "ADMIN" || user?.role === "TEACHER"
  return isStaffOrTeacher ? <ManageGradesView /> : <MyGradesView />
}

/* ------------------------------ Student/Parent ------------------------------- */

function MyGradesView() {
  const { data: students } = useFetch<Paginated<StudentProfile>>("/students/")
  const [activeChild, setActiveChild] = useState<number | null>(null)

  const children = students?.results ?? []
  const selectedId = activeChild ?? children[0]?.id ?? null

  return (
    <div>
      <PageHeader title={t("Baholar")} description={t("Fanlar bo'yicha baholar va yillik natijalar")} />

      {children.length > 1 && (
        <div className="mb-4">
          <Tabs
            tabs={children.map((c) => ({ key: String(c.id), label: fullName(c.user) }))}
            active={String(selectedId)}
            onChange={(k) => setActiveChild(Number(k))}
          />
        </div>
      )}

      {selectedId && <StudentGradeDetail studentId={selectedId} />}
    </div>
  )
}

interface AnnualSubjectResult {
  subject: number
  subject_name: string
  quarter_averages: Record<string, number>
  annual_average: number
}

function StudentGradeDetail({ studentId }: { studentId: number }) {
  const { data: years } = useFetch<Paginated<AcademicYear>>("/classes/academic-years/?page_size=1&is_active=true")
  const activeYear = years?.results[0]

  const { data: annual, loading: annualLoading } = useFetch<{ results: AnnualSubjectResult[] }>(
    activeYear ? `/grades/annual/?student=${studentId}&academic_year=${activeYear.id}` : null,
    [studentId, activeYear?.id]
  )
  const { data: recent, loading: recentLoading } = useFetch<Paginated<Grade>>(
    `/grades/?student=${studentId}&ordering=-created_at&page_size=10`,
    [studentId]
  )

  const columns: Column<Grade>[] = [
    { key: "subject", header: t("Fan"), render: (r) => r.subject_name },
    { key: "quarter", header: t("Chorak"), render: (r) => t("{q}-chorak", { q: r.quarter }) },
    { key: "type", header: t("Turi"), render: (r) => r.grade_type, hideOnMobile: true },
    {
      key: "value",
      header: t("Baho"),
      render: (r) => <span className={`font-display text-base font-bold ${gradeColor(r.value)}`}>{r.value}</span>,
    },
    { key: "date", header: t("Sana"), render: (r) => formatDate(r.created_at), hideOnMobile: true },
  ]

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle>{t("Choraklik baholar")}</CardTitle>
        </CardHeader>
        <CardContent>
          {annualLoading ? (
            <Skeleton className="h-56 w-full" />
          ) : !annual || annual.results.length === 0 ? (
            <EmptyState icon={GraduationCap} title={t("Hali baho yo'q")} />
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full min-w-[480px] border-separate border-spacing-1.5 text-sm">
                <thead>
                  <tr>
                    <th className="px-2 pb-1 text-left text-xs font-semibold uppercase tracking-wide text-ink-400">{t("Fan")}</th>
                    {[1, 2, 3, 4].map((q) => (
                      <th key={q} className="pb-1 text-center text-xs font-semibold uppercase tracking-wide text-ink-400">
                        {t("{q}-chorak", { q })}
                      </th>
                    ))}
                    <th className="pb-1 text-center text-xs font-semibold uppercase tracking-wide text-brand-500">{t("Natija")}</th>
                  </tr>
                </thead>
                <tbody>
                  {annual.results.map((row) => (
                    <tr key={row.subject}>
                      <td className="px-2 py-1 text-sm font-medium text-ink-800 dark:text-ink-100">{row.subject_name}</td>
                      {[1, 2, 3, 4].map((q) => {
                        const value = row.quarter_averages[String(q)] ?? null
                        return (
                          <td key={q} className="p-0 text-center">
                            <div className={`mx-auto flex h-10 w-10 items-center justify-center rounded-lg font-display text-sm font-bold ${gradeCellClasses(value)}`}>
                              {value ?? "–"}
                            </div>
                          </td>
                        )
                      })}
                      <td className="p-0 text-center">
                        <div className={`mx-auto flex h-10 w-12 items-center justify-center rounded-lg font-display text-sm font-bold ring-2 ring-brand-400/40 ${gradeCellClasses(row.annual_average)}`}>
                          {row.annual_average}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>{t("So'nggi baholar")}</CardTitle>
        </CardHeader>
        <CardContent>
          <DataTable columns={columns} rows={recent?.results ?? []} keyField={(r) => r.id} loading={recentLoading} emptyTitle={t("Baho yo'q")} />
        </CardContent>
      </Card>
    </div>
  )
}

/* --------------------------------- Teacher/Admin --------------------------------- */

function ManageGradesView() {
  const [tab, setTab] = useState<"table" | "browse">("table")
  const [subjectFilter, setSubjectFilter] = useState("")
  const [addOpen, setAddOpen] = useState(false)

  const query = new URLSearchParams({ page_size: "50", ordering: "-created_at" })
  if (subjectFilter) query.set("subject", subjectFilter)

  const { data: subjects } = useFetch<Paginated<Subject>>("/subjects/?page_size=100")
  const { data: grades, loading, refetch } = useFetch<Paginated<Grade>>(`/grades/?${query.toString()}`, [subjectFilter])

  const columns: Column<Grade>[] = [
    { key: "student", header: t("O'quvchi"), render: (r) => r.student_name },
    { key: "subject", header: t("Fan"), render: (r) => r.subject_name },
    { key: "quarter", header: t("Chorak"), render: (r) => t("{q}-chorak", { q: r.quarter }), hideOnMobile: true },
    { key: "type", header: t("Turi"), render: (r) => r.grade_type, hideOnMobile: true },
    {
      key: "value",
      header: t("Baho"),
      render: (r) => <span className={`font-display text-base font-bold ${gradeColor(r.value)}`}>{r.value}</span>,
    },
    { key: "date", header: t("Sana"), render: (r) => formatDate(r.created_at), hideOnMobile: true },
  ]

  return (
    <div>
      <PageHeader
        title={t("Baholar")}
        description={t("O'quvchilarga baho qo'yish va nazorat qilish")}
        actions={
          tab === "table" && (
            <Button onClick={() => setAddOpen(true)}>
              <Plus className="h-4 w-4" /> Baho qo'yish
            </Button>
          )
        }
      />

      <div className="mb-4">
        <Tabs
          tabs={[
            { key: "table", label: t("Jadval") },
            { key: "browse", label: t("Sinf bo'yicha ko'rish") },
          ]}
          active={tab}
          onChange={(k) => setTab(k as "table" | "browse")}
        />
      </div>

      {tab === "table" ? (
        <>
          <div className="mb-4 max-w-xs">
            <Select value={subjectFilter} onChange={(e) => setSubjectFilter(e.target.value)}>
              <option value="">{t("Barcha fanlar")}</option>
              {subjects?.results.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.name}
                </option>
              ))}
            </Select>
          </div>

          <DataTable columns={columns} rows={grades?.results ?? []} keyField={(r) => r.id} loading={loading} emptyTitle={t("Baho topilmadi")} />

          <AddGradeModal open={addOpen} onClose={() => setAddOpen(false)} onDone={() => { setAddOpen(false); refetch() }} />
        </>
      ) : (
        <DrillDownGradesView embedded />
      )}
    </div>
  )
}

/* ------------------------- Class -> Student -> Subject drill-down ------------------------- */

function DrillDownGradesView({ embedded = false }: { embedded?: boolean }) {
  const [selectedClass, setSelectedClass] = useState<ClassRoom | null>(null)
  const [selectedStudent, setSelectedStudent] = useState<StudentProfile | null>(null)
  const [selectedSubject, setSelectedSubject] = useState<Subject | null>(null)

  const { data: classes, loading: classesLoading } = useFetch<Paginated<ClassRoom>>("/classes/?page_size=100")
  const { data: students, loading: studentsLoading } = useFetch<Paginated<StudentProfile>>(
    selectedClass ? `/students/?class_room=${selectedClass.id}&page_size=100` : null,
    [selectedClass?.id]
  )
  const { data: subjects, loading: subjectsLoading } = useFetch<Paginated<Subject>>(
    selectedStudent ? "/subjects/?page_size=100" : null,
    [selectedStudent?.id]
  )

  return (
    <div>
      {!embedded && <PageHeader title={t("Baholar")} description={t("Sinf, o'quvchi va fanni tanlab bahoni ko'ring")} />}

      <div className="mb-4 flex flex-wrap items-center gap-1.5 text-sm">
        <Crumb label={t("Sinf")} value={selectedClass?.name} onClick={() => { setSelectedClass(null); setSelectedStudent(null); setSelectedSubject(null) }} active={!selectedClass} />
        {selectedClass && (
          <>
            <ChevronRight className="h-3.5 w-3.5 text-ink-300" />
            <Crumb label={t("O'quvchi")} value={selectedStudent ? fullName(selectedStudent.user) : undefined} onClick={() => { setSelectedStudent(null); setSelectedSubject(null) }} active={!selectedStudent} />
          </>
        )}
        {selectedStudent && (
          <>
            <ChevronRight className="h-3.5 w-3.5 text-ink-300" />
            <Crumb label={t("Fan")} value={selectedSubject?.name} onClick={() => setSelectedSubject(null)} active={!selectedSubject} />
          </>
        )}
      </div>

      {!selectedClass ? (
        <PickerGrid loading={classesLoading} empty={!classes?.results.length} emptyTitle={t("Sinf topilmadi")}>
          {classes?.results.map((c) => (
            <PickerCard key={c.id} onClick={() => setSelectedClass(c)}>
              <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-gradient-to-br from-brand-500 to-brand-700 font-display text-sm font-bold text-white">
                {c.name}
              </div>
              <div className="min-w-0">
                <p className="truncate font-medium text-ink-800 dark:text-ink-100">{c.name}</p>
                <p className="text-xs text-ink-400">{c.student_count} o'quvchi</p>
              </div>
            </PickerCard>
          ))}
        </PickerGrid>
      ) : !selectedStudent ? (
        <PickerGrid loading={studentsLoading} empty={!students?.results.length} emptyTitle={t("Bu sinfda o'quvchi yo'q")}>
          {students?.results.map((s) => (
            <PickerCard key={s.id} onClick={() => setSelectedStudent(s)}>
              <Avatar name={fullName(s.user)} src={s.photo} size="sm" />
              <div className="min-w-0">
                <p className="truncate font-medium text-ink-800 dark:text-ink-100">{fullName(s.user)}</p>
                <p className="truncate text-xs text-ink-400">{s.student_code}</p>
              </div>
            </PickerCard>
          ))}
        </PickerGrid>
      ) : !selectedSubject ? (
        <PickerGrid loading={subjectsLoading} empty={!subjects?.results.length} emptyTitle={t("Fan topilmadi")}>
          {subjects?.results.map((s) => (
            <PickerCard key={s.id} onClick={() => setSelectedSubject(s)}>
              <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-brand-50 text-lg dark:bg-brand-500/10">
                {s.icon || <GraduationCap className="h-4 w-4 text-brand-500" />}
              </div>
              <p className="truncate font-medium text-ink-800 dark:text-ink-100">{s.name}</p>
            </PickerCard>
          ))}
        </PickerGrid>
      ) : (
        <SubjectGradeView studentId={selectedStudent.id} subject={selectedSubject} />
      )}
    </div>
  )
}

function Crumb({ label, value, onClick, active }: { label: string; value?: string; onClick: () => void; active: boolean }) {
  return (
    <button
      onClick={onClick}
      disabled={active}
      className={`rounded-lg px-2.5 py-1 font-medium transition-colors ${
        active
          ? "bg-brand-50 text-brand-700 dark:bg-brand-500/10 dark:text-brand-300"
          : "text-ink-500 hover:bg-ink-100 dark:text-ink-400 dark:hover:bg-ink-800"
      }`}
    >
      {label}
      {value ? `: ${value}` : ""}
    </button>
  )
}

function PickerGrid({
  loading,
  empty,
  emptyTitle,
  children,
}: {
  loading: boolean
  empty: boolean
  emptyTitle: string
  children: ReactNode
}) {
  if (loading) return <Skeleton className="h-40 w-full" />
  if (empty) return <EmptyState icon={School} title={emptyTitle} />
  return <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">{children}</div>
}

function PickerCard({ onClick, children }: { onClick: () => void; children: ReactNode }) {
  return (
    <button
      onClick={onClick}
      className="flex items-center gap-3 rounded-2xl border border-ink-100 bg-white p-4 text-left transition-all hover:-translate-y-0.5 hover:border-brand-200 hover:shadow-soft-lg dark:border-ink-800 dark:bg-ink-900 dark:hover:border-brand-500/40"
    >
      {children}
    </button>
  )
}

function SubjectGradeView({ studentId, subject }: { studentId: number; subject: Subject }) {
  const { data: years } = useFetch<Paginated<AcademicYear>>("/classes/academic-years/?page_size=1&is_active=true")
  const activeYear = years?.results[0]

  const { data: annual, loading: annualLoading } = useFetch<{ results: AnnualSubjectResult[] }>(
    activeYear ? `/grades/annual/?student=${studentId}&academic_year=${activeYear.id}` : null,
    [studentId, activeYear?.id]
  )
  const { data: history, loading: historyLoading } = useFetch<Paginated<Grade>>(
    `/grades/?student=${studentId}&subject=${subject.id}&ordering=-created_at&page_size=30`,
    [studentId, subject.id]
  )

  const row = annual?.results.find((r) => r.subject === subject.id)

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle>{subject.name} — choraklar</CardTitle>
        </CardHeader>
        <CardContent>
          {annualLoading ? (
            <Skeleton className="h-20 w-full" />
          ) : !row ? (
            <EmptyState icon={GraduationCap} title={t("Bu fandan hali baho yo'q")} />
          ) : (
            <div className="flex flex-wrap items-center gap-3">
              {[1, 2, 3, 4].map((q) => {
                const value = row.quarter_averages[String(q)] ?? null
                return (
                  <div key={q} className="text-center">
                    <div className={`flex h-14 w-14 items-center justify-center rounded-xl font-display text-lg font-bold ${gradeCellClasses(value)}`}>
                      {value ?? "–"}
                    </div>
                    <p className="mt-1 text-xs text-ink-400">{q}-chorak</p>
                  </div>
                )
              })}
              <div className="text-center">
                <div className={`flex h-14 w-16 items-center justify-center rounded-xl font-display text-lg font-bold ring-2 ring-brand-400/40 ${gradeCellClasses(row.annual_average)}`}>
                  {row.annual_average}
                </div>
                <p className="mt-1 text-xs font-semibold text-brand-500">{t("Natija")}</p>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>{t("Barcha baholar tarixi")}</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          {historyLoading ? (
            <Skeleton className="h-32 w-full" />
          ) : !history || history.results.length === 0 ? (
            <EmptyState title={t("Baho topilmadi")} />
          ) : (
            history.results.map((g) => (
              <div key={g.id} className="flex items-center justify-between rounded-xl border border-ink-100 px-3.5 py-2.5 dark:border-ink-800">
                <div>
                  <p className="text-sm font-medium text-ink-800 dark:text-ink-100">
                    {t("{q}-chorak", { q: g.quarter })} · {g.grade_type}
                  </p>
                  <p className="text-xs text-ink-400">{formatDate(g.created_at)}</p>
                </div>
                <span className={`font-display text-lg font-bold ${gradeColor(g.value)}`}>{g.value}</span>
              </div>
            ))
          )}
        </CardContent>
      </Card>
    </div>
  )
}

function AddGradeModal({ open, onClose, onDone }: { open: boolean; onClose: () => void; onDone: () => void }) {
  const { data: classes } = useFetch<Paginated<ClassRoom>>(open ? "/classes/?page_size=100" : null)
  const { data: subjects } = useFetch<Paginated<Subject>>(open ? "/subjects/?page_size=100" : null)
  const { data: years } = useFetch<Paginated<AcademicYear>>(open ? "/classes/academic-years/?page_size=100" : null)

  const [classRoom, setClassRoom] = useState("")
  const { data: students } = useFetch<Paginated<StudentProfile>>(classRoom ? `/students/?class_room=${classRoom}&page_size=100` : null, [classRoom])
  const [academicYear, setAcademicYear] = useState("")
  const { data: quarters } = useFetch<Paginated<Quarter>>(academicYear ? `/classes/quarters/?academic_year=${academicYear}` : null, [academicYear])

  const [form, setForm] = useState({ student: "", subject: "", quarter: "", value: "", grade_type: "DAILY", comment: "" })
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setLoading(true)
    try {
      await api.post("/grades/", { ...form, academic_year: academicYear })
      toast.success(t("Baho qo'yildi"))
      setForm({ student: "", subject: "", quarter: "", value: "", grade_type: "DAILY", comment: "" })
      onDone()
    } catch (err) {
      toast.error(getErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  return (
    <Modal open={open} onClose={onClose} title={t("Baho qo'yish")} size="lg">
      <form onSubmit={handleSubmit} className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <Field label={t("Sinf")}>
          <Select value={classRoom} onChange={(e) => setClassRoom(e.target.value)} required>
            <option value="">{t("Tanlang...")}</option>
            {classes?.results.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name}
              </option>
            ))}
          </Select>
        </Field>
        <Field label={t("O'quvchi")}>
          <Select value={form.student} onChange={(e) => setForm((f) => ({ ...f, student: e.target.value }))} required disabled={!classRoom}>
            <option value="">{t("Tanlang...")}</option>
            {students?.results.map((s) => (
              <option key={s.id} value={s.id}>
                {fullName(s.user)}
              </option>
            ))}
          </Select>
        </Field>
        <Field label={t("Fan")}>
          <Select value={form.subject} onChange={(e) => setForm((f) => ({ ...f, subject: e.target.value }))} required>
            <option value="">{t("Tanlang...")}</option>
            {subjects?.results.map((s) => (
              <option key={s.id} value={s.id}>
                {s.name}
              </option>
            ))}
          </Select>
        </Field>
        <Field label={t("O'quv yili")}>
          <Select value={academicYear} onChange={(e) => setAcademicYear(e.target.value)} required>
            <option value="">{t("Tanlang...")}</option>
            {years?.results.map((y) => (
              <option key={y.id} value={y.id}>
                {y.name}
              </option>
            ))}
          </Select>
        </Field>
        <Field label={t("Chorak")}>
          <Select value={form.quarter} onChange={(e) => setForm((f) => ({ ...f, quarter: e.target.value }))} required disabled={!academicYear}>
            <option value="">{t("Tanlang...")}</option>
            {quarters?.results.map((q) => (
              <option key={q.id} value={q.id}>
                {t("{q}-chorak", { q: q.number })}
              </option>
            ))}
          </Select>
        </Field>
        <Field label={t("Baho turi")}>
          <Select value={form.grade_type} onChange={(e) => setForm((f) => ({ ...f, grade_type: e.target.value }))}>
            <option value="DAILY">{t("Kundalik")}</option>
            <option value="HOMEWORK">{t("Uy vazifasi")}</option>
            <option value="QUIZ">{t("Test")}</option>
            <option value="QUARTER">{t("Chorak")}</option>
            <option value="EXAM">{t("Imtihon")}</option>
          </Select>
        </Field>
        <Field label={t("Baho (0-10)")}>
          <Input type="number" min={0} max={10} value={form.value} onChange={(e) => setForm((f) => ({ ...f, value: e.target.value }))} required />
        </Field>
        <Field label={t("Izoh")}>
          <Input value={form.comment} onChange={(e) => setForm((f) => ({ ...f, comment: e.target.value }))} />
        </Field>
        <Button type="submit" className="sm:col-span-2" loading={loading}>
          {t("Saqlash")}
        </Button>
      </form>
    </Modal>
  )
}
