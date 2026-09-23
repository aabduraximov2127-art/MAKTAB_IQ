import { type FormEvent, useState } from "react"
import { motion } from "framer-motion"
import { BookOpen, CheckCircle2, Clock, Plus, Trash2, Trophy } from "lucide-react"
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
import { Badge } from "../components/ui/Badge"
import { EmptyState } from "../components/ui/EmptyState"
import { CardSkeleton, Skeleton } from "../components/ui/Skeleton"
import { formatDateTime } from "../lib/format"
import type { ClassRoom, Paginated, Quiz, QuizAttempt, Subject } from "../types"
import { t } from "../i18n"

export default function QuizzesPage() {
  const user = useAuthStore((s) => s.user)
  const isTeacher = user?.role === "TEACHER" || user?.role === "ADMIN" || user?.role === "SUPERADMIN"
  const isStudent = user?.role === "STUDENT"

  const [addOpen, setAddOpen] = useState(false)
  const [takeQuiz, setTakeQuiz] = useState<Quiz | null>(null)
  const [resultsQuiz, setResultsQuiz] = useState<Quiz | null>(null)

  const { data, loading, refetch } = useFetch<Paginated<Quiz>>("/quizzes/?ordering=-created_at&page_size=50")

  return (
    <div>
      <PageHeader
        title={t("Testlar")}
        description={isStudent ? t("Sizga tayinlangan testlar") : t("Yaratilgan testlar ro'yxati")}
        actions={
          isTeacher && (
            <Button onClick={() => setAddOpen(true)}>
              <Plus className="h-4 w-4" /> Yangi test
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
        <EmptyState icon={BookOpen} title={t("Test topilmadi")} />
      ) : (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {data.results.map((q, i) => (
            <motion.div key={q.id} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.04 }}>
              <Card className="h-full">
                <CardContent className="flex h-full flex-col">
                  <div className="flex items-start justify-between gap-2">
                    <p className="font-display font-semibold text-ink-800 dark:text-ink-100">{q.title}</p>
                    <Badge tone="brand">{q.questions.length} savol</Badge>
                  </div>
                  <div className="mt-2 flex items-center gap-3 text-xs text-ink-400">
                    <span className="flex items-center gap-1">
                      <Clock className="h-3.5 w-3.5" /> {q.time_limit_minutes} daqiqa
                    </span>
                    <span>{q.total_points} ball</span>
                  </div>
                  <p className="mt-1 text-xs text-ink-400">{t("Muddat: {date}", { date: formatDateTime(q.deadline) })}</p>
                  <div className="mt-auto pt-4">
                    {isStudent ? (
                      <Button className="w-full" onClick={() => setTakeQuiz(q)}>
                        {t("Testni boshlash")}
                      </Button>
                    ) : (
                      <Button variant="outline" className="w-full" onClick={() => setResultsQuiz(q)}>
                        <Trophy className="h-4 w-4" /> Natijalar
                      </Button>
                    )}
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          ))}
        </div>
      )}

      <TakeQuizModal
        key={takeQuiz?.id ?? "none"}
        quiz={takeQuiz}
        onClose={() => setTakeQuiz(null)}
        nextQuiz={(() => {
          if (!takeQuiz || !data) return null
          const index = data.results.findIndex((q) => q.id === takeQuiz.id)
          return index >= 0 ? (data.results[index + 1] ?? null) : null
        })()}
        onNext={(next) => setTakeQuiz(next)}
      />
      <ResultsModal quiz={resultsQuiz} onClose={() => setResultsQuiz(null)} />
      <CreateQuizModal open={addOpen} onClose={() => setAddOpen(false)} onDone={() => { setAddOpen(false); refetch() }} />
    </div>
  )
}

function TakeQuizModal({
  quiz,
  onClose,
  nextQuiz,
  onNext,
}: {
  quiz: Quiz | null
  onClose: () => void
  nextQuiz: Quiz | null
  onNext: (next: Quiz) => void
}) {
  const [answers, setAnswers] = useState<Record<number, number>>({})
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<QuizAttempt | null>(null)

  async function handleSubmit() {
    if (!quiz) return
    setLoading(true)
    try {
      const { data } = await api.post(`/quizzes/${quiz.id}/submit/`, { answers })
      setResult(data)
      toast.success(t("Test yakunlandi!"))
    } catch (err) {
      toast.error(getErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  function handleClose() {
    setAnswers({})
    setResult(null)
    onClose()
  }

  return (
    <Modal open={!!quiz} onClose={handleClose} title={quiz?.title} size="lg">
      {quiz &&
        (result ? (
          <div className="flex flex-col items-center gap-3 py-6 text-center">
            <div className="flex h-16 w-16 items-center justify-center rounded-full bg-emerald-100 text-emerald-600 dark:bg-emerald-500/15 dark:text-emerald-400">
              <Trophy className="h-8 w-8" />
            </div>
            <p className="font-display text-2xl font-bold text-ink-900 dark:text-white">
              {result.score} / {result.max_score}
            </p>
            <p className="text-sm text-ink-500 dark:text-ink-400">{t("Natijangiz muvaffaqiyatli saqlandi")}</p>
            <div className="flex gap-2">
              <Button variant="outline" onClick={handleClose}>
                {t("Yopish")}
              </Button>
              {nextQuiz && (
                <Button
                  onClick={() => {
                    setAnswers({})
                    setResult(null)
                    onNext(nextQuiz)
                  }}
                >
                  Keyingi test: {nextQuiz.title} →
                </Button>
              )}
            </div>
          </div>
        ) : (
          <div className="space-y-5">
            {quiz.questions.map((q, i) => (
              <div key={q.id}>
                <p className="mb-2 text-sm font-semibold text-ink-800 dark:text-ink-100">
                  {i + 1}. {q.question}
                </p>
                <div className="space-y-1.5">
                  {q.options.map((opt, idx) => (
                    <label
                      key={idx}
                      className="flex cursor-pointer items-center gap-2.5 rounded-xl border border-ink-100 px-3.5 py-2.5 text-sm transition-colors hover:bg-ink-50 has-[:checked]:border-brand-500 has-[:checked]:bg-brand-50 dark:border-ink-800 dark:hover:bg-ink-800 dark:has-[:checked]:bg-brand-500/10"
                    >
                      <input
                        type="radio"
                        name={`q-${q.id}`}
                        checked={answers[q.id] === idx}
                        onChange={() => setAnswers((a) => ({ ...a, [q.id]: idx }))}
                        className="accent-brand-600"
                      />
                      {opt}
                    </label>
                  ))}
                </div>
              </div>
            ))}
            <Button className="w-full" onClick={handleSubmit} loading={loading} disabled={Object.keys(answers).length < quiz.questions.length}>
              {t("Yakunlash va topshirish")}
            </Button>
          </div>
        ))}
    </Modal>
  )
}

function ResultsModal({ quiz, onClose }: { quiz: Quiz | null; onClose: () => void }) {
  const { data, loading } = useFetch<Paginated<QuizAttempt>>(quiz ? `/quizzes/attempts/?quiz=${quiz.id}` : null)

  return (
    <Modal open={!!quiz} onClose={onClose} title={quiz ? t("{title} — natijalar", { title: quiz.title }) : ""}>
      {loading ? (
        <Skeleton className="h-40 w-full" />
      ) : !data || data.results.length === 0 ? (
        <EmptyState title={t("Hali hech kim topshirmagan")} />
      ) : (
        <div className="space-y-2">
          {data.results
            .sort((a, b) => b.score - a.score)
            .map((r, i) => (
              <div key={r.id} className="flex items-center justify-between rounded-xl border border-ink-100 px-3.5 py-2.5 dark:border-ink-800">
                <div className="flex items-center gap-2.5">
                  <span className="flex h-6 w-6 items-center justify-center rounded-full bg-ink-100 text-xs font-bold text-ink-500 dark:bg-ink-800">
                    {i + 1}
                  </span>
                  <p className="text-sm font-medium text-ink-800 dark:text-ink-100">{r.student_name}</p>
                </div>
                <Badge tone={r.score / r.max_score >= 0.7 ? "success" : "warning"}>
                  {r.score}/{r.max_score}
                </Badge>
              </div>
            ))}
        </div>
      )}
    </Modal>
  )
}

interface DraftQuestion {
  question: string
  options: string[]
  correct_answer: number
  points: number
}

function CreateQuizModal({ open, onClose, onDone }: { open: boolean; onClose: () => void; onDone: () => void }) {
  const { data: classes } = useFetch<Paginated<ClassRoom>>(open ? "/classes/?page_size=100" : null)
  const { data: subjects } = useFetch<Paginated<Subject>>(open ? "/subjects/?page_size=100" : null)

  const [form, setForm] = useState({ title: "", subject: "", class_room: "", deadline: "", time_limit_minutes: "30" })
  const [questions, setQuestions] = useState<DraftQuestion[]>([
    { question: "", options: ["", ""], correct_answer: 0, points: 1 },
  ])
  const [loading, setLoading] = useState(false)

  function updateQuestion(i: number, patch: Partial<DraftQuestion>) {
    setQuestions((qs) => qs.map((q, idx) => (idx === i ? { ...q, ...patch } : q)))
  }

  function updateOption(qi: number, oi: number, value: string) {
    setQuestions((qs) =>
      qs.map((q, idx) => (idx === qi ? { ...q, options: q.options.map((o, j) => (j === oi ? value : o)) } : q))
    )
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setLoading(true)
    try {
      const { data: quiz } = await api.post("/quizzes/", form)
      for (const q of questions) {
        await api.post("/quizzes/questions/", { ...q, quiz: quiz.id })
      }
      toast.success(t("Test yaratildi"))
      setForm({ title: "", subject: "", class_room: "", deadline: "", time_limit_minutes: "30" })
      setQuestions([{ question: "", options: ["", ""], correct_answer: 0, points: 1 }])
      onDone()
    } catch (err) {
      toast.error(getErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  return (
    <Modal open={open} onClose={onClose} title={t("Yangi test yaratish")} size="lg">
      <form onSubmit={handleSubmit} className="space-y-5">
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <Field label={t("Sarlavha")} className="sm:col-span-2">
            <Input value={form.title} onChange={(e) => setForm((f) => ({ ...f, title: e.target.value }))} required />
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
          <Field label={t("Sinf")}>
            <Select value={form.class_room} onChange={(e) => setForm((f) => ({ ...f, class_room: e.target.value }))} required>
              <option value="">{t("Tanlang...")}</option>
              {classes?.results.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name}
                </option>
              ))}
            </Select>
          </Field>
          <Field label={t("Muddat")}>
            <Input type="datetime-local" value={form.deadline} onChange={(e) => setForm((f) => ({ ...f, deadline: e.target.value }))} required />
          </Field>
          <Field label={t("Vaqt limiti (daqiqa)")}>
            <Input
              type="number"
              min={1}
              value={form.time_limit_minutes}
              onChange={(e) => setForm((f) => ({ ...f, time_limit_minutes: e.target.value }))}
            />
          </Field>
        </div>

        <div className="space-y-4">
          <p className="text-sm font-semibold text-ink-700 dark:text-ink-200">{t("Savollar")}</p>
          {questions.map((q, qi) => (
            <div key={qi} className="space-y-2.5 rounded-xl border border-ink-100 p-3.5 dark:border-ink-800">
              <div className="flex items-center gap-2">
                <Input
                  placeholder={t("Savol {n}", { n: qi + 1 })}
                  value={q.question}
                  onChange={(e) => updateQuestion(qi, { question: e.target.value })}
                  required
                />
                {questions.length > 1 && (
                  <button
                    type="button"
                    onClick={() => setQuestions((qs) => qs.filter((_, i) => i !== qi))}
                    className="shrink-0 rounded-lg p-2 text-ink-400 hover:bg-rose-50 hover:text-rose-600 dark:hover:bg-rose-500/10"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                )}
              </div>
              {q.options.map((opt, oi) => (
                <div key={oi} className="flex items-center gap-2 pl-2">
                  <input
                    type="radio"
                    checked={q.correct_answer === oi}
                    onChange={() => updateQuestion(qi, { correct_answer: oi })}
                    className="accent-brand-600"
                  />
                  <Input placeholder={t("Variant {n}", { n: oi + 1 })} value={opt} onChange={(e) => updateOption(qi, oi, e.target.value)} required />
                </div>
              ))}
              <div className="flex items-center justify-between pl-2">
                <button
                  type="button"
                  onClick={() => updateQuestion(qi, { options: [...q.options, ""] })}
                  className="text-xs font-medium text-brand-600 dark:text-brand-400"
                >
                  + Variant qo'shish
                </button>
                <div className="flex items-center gap-1.5 text-xs text-ink-500">
                  {t("Ball:")}
                  <input
                    type="number"
                    min={1}
                    value={q.points}
                    onChange={(e) => updateQuestion(qi, { points: Number(e.target.value) })}
                    className="h-7 w-14 rounded-md border border-ink-200 px-1.5 dark:border-ink-700 dark:bg-ink-900"
                  />
                </div>
              </div>
            </div>
          ))}
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={() => setQuestions((qs) => [...qs, { question: "", options: ["", ""], correct_answer: 0, points: 1 }])}
          >
            <Plus className="h-4 w-4" /> Savol qo'shish
          </Button>
        </div>

        <Button type="submit" className="w-full" loading={loading}>
          <CheckCircle2 className="h-4 w-4" /> Testni yaratish
        </Button>
      </form>
    </Modal>
  )
}
