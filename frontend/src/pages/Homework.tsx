import { type FormEvent, useState } from "react"
import { motion } from "framer-motion"
import { CalendarClock, CheckCircle2, ListChecks, Paperclip, Plus, Send } from "lucide-react"
import toast from "react-hot-toast"
import { useFetch } from "../hooks/useFetch"
import { api, getErrorMessage } from "../lib/api"
import { useAuthStore } from "../store/auth"
import { PageHeader } from "../components/ui/PageHeader"
import { Button } from "../components/ui/Button"
import { Card, CardContent } from "../components/ui/Card"
import { Field, Input } from "../components/ui/Input"
import { Select } from "../components/ui/Select"
import { Modal } from "../components/ui/Modal"
import { Drawer } from "../components/ui/Drawer"
import { Badge } from "../components/ui/Badge"
import { EmptyState } from "../components/ui/EmptyState"
import { CardSkeleton } from "../components/ui/Skeleton"
import { formatDateTime } from "../lib/format"
import { cn } from "../lib/cn"
import type { Assignment, AssignmentSubmission, Lesson, Paginated } from "../types"

export default function HomeworkPage() {
  const user = useAuthStore((s) => s.user)
  const isTeacher = user?.role === "TEACHER" || user?.role === "ADMIN" || user?.role === "SUPERADMIN"
  const isStudent = user?.role === "STUDENT"

  const [addOpen, setAddOpen] = useState(false)
  const [selected, setSelected] = useState<Assignment | null>(null)

  const { data, loading, refetch } = useFetch<Paginated<Assignment>>("/assignments/?ordering=-created_at&page_size=50")

  return (
    <div>
      <PageHeader
        title="Uy vazifalari"
        description={isStudent ? "Sizga berilgan vazifalar" : "Berilgan uy vazifalari ro'yxati"}
        actions={
          isTeacher && (
            <Button onClick={() => setAddOpen(true)}>
              <Plus className="h-4 w-4" /> Yangi vazifa
            </Button>
          )
        }
      />

      {loading ? (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <CardSkeleton key={i} />
          ))}
        </div>
      ) : !data || data.results.length === 0 ? (
        <EmptyState icon={ListChecks} title="Uy vazifasi yo'q" />
      ) : (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {data.results.map((a, i) => {
            const overdue = new Date(a.deadline) < new Date()
            return (
              <motion.div key={a.id} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.04 }}>
                <Card
                  className="h-full cursor-pointer transition-transform hover:-translate-y-0.5 hover:shadow-soft-lg"
                  onClick={() => setSelected(a)}
                >
                  <CardContent className="flex h-full flex-col">
                    <div className="flex items-start justify-between gap-2">
                      <p className="font-display font-semibold text-ink-800 dark:text-ink-100">{a.title}</p>
                      <Badge tone={overdue ? "danger" : "warning"}>{overdue ? "Muddat o'tgan" : "Faol"}</Badge>
                    </div>
                    <p className="mt-2 line-clamp-2 flex-1 text-sm text-ink-500 dark:text-ink-400">{a.description || "Tavsif kiritilmagan"}</p>
                    <div className="mt-3 flex items-center gap-1.5 text-xs text-ink-400">
                      <CalendarClock className="h-3.5 w-3.5" /> {formatDateTime(a.deadline)}
                    </div>
                  </CardContent>
                </Card>
              </motion.div>
            )
          })}
        </div>
      )}

      <AssignmentDrawer assignment={selected} onClose={() => setSelected(null)} />
      <AddAssignmentModal open={addOpen} onClose={() => setAddOpen(false)} onDone={() => { setAddOpen(false); refetch() }} />
    </div>
  )
}

function AssignmentDrawer({ assignment, onClose }: { assignment: Assignment | null; onClose: () => void }) {
  const user = useAuthStore((s) => s.user)
  const isStudent = user?.role === "STUDENT"
  const isTeacher = user?.role === "TEACHER" || user?.role === "ADMIN" || user?.role === "SUPERADMIN"

  return (
    <Drawer open={!!assignment} onClose={onClose} title={assignment?.title} subtitle={assignment ? `Muddat: ${formatDateTime(assignment.deadline)}` : ""}>
      {assignment && (
        <div className="space-y-5">
          <p className="text-sm text-ink-600 dark:text-ink-300">{assignment.description || "Tavsif kiritilmagan"}</p>
          {assignment.attachment && (
            <a
              href={assignment.attachment}
              target="_blank"
              rel="noreferrer"
              className="flex items-center gap-2 rounded-xl border border-ink-100 p-3 text-sm text-brand-600 hover:bg-ink-50 dark:border-ink-800 dark:text-brand-400 dark:hover:bg-ink-800"
            >
              <Paperclip className="h-4 w-4" /> Biriktirilgan fayl
            </a>
          )}
          {isStudent && <SubmitForm assignment={assignment} />}
          {isTeacher && <SubmissionsList assignment={assignment} />}
        </div>
      )}
    </Drawer>
  )
}

function SubmitForm({ assignment }: { assignment: Assignment }) {
  const [answer, setAnswer] = useState("")
  const [loading, setLoading] = useState(false)
  const [submitted, setSubmitted] = useState(false)

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setLoading(true)
    try {
      await api.post(`/assignments/${assignment.id}/submit/`, { answer })
      setSubmitted(true)
      toast.success("Javobingiz yuborildi")
    } catch (err) {
      toast.error(getErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  if (submitted) {
    return (
      <div className="flex items-center gap-2 rounded-xl bg-emerald-50 p-4 text-sm font-medium text-emerald-700 dark:bg-emerald-500/10 dark:text-emerald-400">
        <CheckCircle2 className="h-5 w-5" /> Javobingiz muvaffaqiyatli yuborildi
      </div>
    )
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-3 border-t border-ink-100 pt-4 dark:border-ink-800">
      <Field label="Javobingiz">
        <textarea
          value={answer}
          onChange={(e) => setAnswer(e.target.value)}
          rows={4}
          required
          className="w-full rounded-xl border border-ink-200 bg-white p-3 text-sm text-ink-900 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/40 dark:border-ink-700 dark:bg-ink-900 dark:text-white"
          placeholder="Javobingizni shu yerga yozing..."
        />
      </Field>
      <Button type="submit" className="w-full" loading={loading}>
        <Send className="h-4 w-4" /> Topshirish
      </Button>
    </form>
  )
}

function SubmissionsList({ assignment }: { assignment: Assignment }) {
  const { data, loading, refetch } = useFetch<Paginated<AssignmentSubmission>>(`/submissions/?assignment=${assignment.id}`)
  const [scoring, setScoring] = useState<number | null>(null)
  const [score, setScore] = useState("")

  async function handleGrade(id: number) {
    try {
      await api.post(`/submissions/${id}/grade/`, { score: Number(score) })
      toast.success("Baholandi")
      setScoring(null)
      setScore("")
      refetch()
    } catch (err) {
      toast.error(getErrorMessage(err))
    }
  }

  return (
    <div className="border-t border-ink-100 pt-4 dark:border-ink-800">
      <p className="mb-3 text-sm font-semibold text-ink-700 dark:text-ink-200">Topshirilgan javoblar</p>
      {loading ? (
        <div className="h-24 animate-pulse rounded-xl bg-ink-100 dark:bg-ink-800" />
      ) : !data || data.results.length === 0 ? (
        <EmptyState title="Hali hech kim topshirmagan" />
      ) : (
        <div className="space-y-2.5">
          {data.results.map((s) => (
            <div key={s.id} className="rounded-xl border border-ink-100 p-3 dark:border-ink-800">
              <div className="flex items-center justify-between gap-2">
                <p className="text-sm font-medium text-ink-800 dark:text-ink-100">{s.student_name}</p>
                <Badge tone={s.status === "GRADED" ? "success" : s.status === "LATE" ? "warning" : "info"}>{s.status}</Badge>
              </div>
              <p className="mt-1.5 line-clamp-2 text-xs text-ink-500 dark:text-ink-400">{s.answer}</p>
              {s.score !== null ? (
                <p className="mt-1.5 text-sm font-bold text-brand-600 dark:text-brand-400">Baho: {s.score}</p>
              ) : scoring === s.id ? (
                <div className="mt-2 flex gap-2">
                  <Input type="number" min={0} max={100} value={score} onChange={(e) => setScore(e.target.value)} className="h-9" />
                  <Button size="sm" onClick={() => handleGrade(s.id)}>
                    Saqlash
                  </Button>
                </div>
              ) : (
                <button onClick={() => setScoring(s.id)} className="mt-2 text-xs font-medium text-brand-600 dark:text-brand-400">
                  Baholash
                </button>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

function AddAssignmentModal({ open, onClose, onDone }: { open: boolean; onClose: () => void; onDone: () => void }) {
  const { data: lessons } = useFetch<Paginated<Lesson>>(open ? "/lessons/?page_size=100&ordering=-date" : null)
  const [form, setForm] = useState({ lesson: "", title: "", description: "", deadline: "" })
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setLoading(true)
    try {
      await api.post("/assignments/", form)
      toast.success("Uy vazifasi yaratildi")
      setForm({ lesson: "", title: "", description: "", deadline: "" })
      onDone()
    } catch (err) {
      toast.error(getErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  return (
    <Modal open={open} onClose={onClose} title="Yangi uy vazifasi" size="lg">
      <form onSubmit={handleSubmit} className="space-y-4">
        <Field label="Dars">
          <Select value={form.lesson} onChange={(e) => setForm((f) => ({ ...f, lesson: e.target.value }))} required>
            <option value="">Tanlang...</option>
            {lessons?.results.map((l) => (
              <option key={l.id} value={l.id}>
                {l.class_room_name} • {l.subject_name} • {l.date}
              </option>
            ))}
          </Select>
        </Field>
        <Field label="Sarlavha">
          <Input value={form.title} onChange={(e) => setForm((f) => ({ ...f, title: e.target.value }))} required />
        </Field>
        <Field label="Tavsif">
          <textarea
            value={form.description}
            onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))}
            rows={3}
            className={cn(
              "w-full rounded-xl border border-ink-200 bg-white p-3 text-sm text-ink-900",
              "focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/40 dark:border-ink-700 dark:bg-ink-900 dark:text-white"
            )}
          />
        </Field>
        <Field label="Muddat">
          <Input type="datetime-local" value={form.deadline} onChange={(e) => setForm((f) => ({ ...f, deadline: e.target.value }))} required />
        </Field>
        <Button type="submit" className="w-full" loading={loading}>
          Yaratish
        </Button>
      </form>
    </Modal>
  )
}
