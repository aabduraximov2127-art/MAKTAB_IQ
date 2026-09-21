import { type FormEvent, useEffect, useRef, useState } from "react"
import { Bot, Send, Sparkles, TrendingDown } from "lucide-react"
import { useFetch } from "../hooks/useFetch"
import { api, getErrorMessage } from "../lib/api"
import { PageHeader } from "../components/ui/PageHeader"
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/Card"
import { EmptyState } from "../components/ui/EmptyState"
import { Skeleton } from "../components/ui/Skeleton"
import { Badge } from "../components/ui/Badge"
import toast from "react-hot-toast"

interface Exchange {
  question: string
  answer?: string
  loading?: boolean
}

interface WeakTopic {
  subject: number
  subject_name: string
  average: number
}

const SUGGESTIONS = [
  "Kvadrat tenglamani qanday yechish mumkin?",
  "Fotosintez jarayonini tushuntirib bering",
  "Present Perfect va Past Simple farqi nima?",
  "Nyutonning uchinchi qonuni haqida misol bering",
]

export default function AIAssistantPage() {
  const { data } = useFetch<{ weak_topics: WeakTopic[] }>("/ai/weak-topics/")
  const [exchanges, setExchanges] = useState<Exchange[]>([])
  const [question, setQuestion] = useState("")
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [exchanges])

  async function ask(q: string) {
    if (!q.trim()) return
    setQuestion("")
    setExchanges((prev) => [...prev, { question: q, loading: true }])
    try {
      const { data } = await api.post("/ai/ask/", { question: q })
      setExchanges((prev) => prev.map((e, i) => (i === prev.length - 1 ? { question: q, answer: data.answer } : e)))
    } catch (err) {
      toast.error(getErrorMessage(err))
      setExchanges((prev) => prev.slice(0, -1))
    }
  }

  function handleSubmit(e: FormEvent) {
    e.preventDefault()
    ask(question)
  }

  return (
    <div>
      <PageHeader title="AI Study Assistant" description="Dars bo'yicha savol bering — AI sizga yordam beradi" />

      <div className="grid grid-cols-1 gap-4 xl:grid-cols-3">
        <Card className="xl:col-span-2">
          <div className="flex h-[32rem] flex-col">
            <div className="flex-1 space-y-4 overflow-y-auto p-5">
              {exchanges.length === 0 ? (
                <div className="flex h-full flex-col items-center justify-center gap-4 text-center">
                  <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-brand-500 to-accent-500 text-white">
                    <Bot className="h-7 w-7" />
                  </div>
                  <div>
                    <p className="font-display font-semibold text-ink-800 dark:text-ink-100">Nima bo'yicha yordam kerak?</p>
                    <p className="mt-1 text-sm text-ink-500 dark:text-ink-400">Quyidagilardan birini sinab ko'ring:</p>
                  </div>
                  <div className="flex flex-wrap justify-center gap-2">
                    {SUGGESTIONS.map((s) => (
                      <button
                        key={s}
                        onClick={() => ask(s)}
                        className="rounded-full border border-ink-200 px-3.5 py-1.5 text-xs text-ink-600 transition-colors hover:border-brand-400 hover:text-brand-600 dark:border-ink-700 dark:text-ink-300"
                      >
                        {s}
                      </button>
                    ))}
                  </div>
                </div>
              ) : (
                exchanges.map((ex, i) => (
                  <div key={i} className="space-y-2">
                    <div className="flex justify-end">
                      <div className="max-w-[80%] rounded-2xl rounded-br-sm bg-brand-600 px-4 py-2.5 text-sm text-white">{ex.question}</div>
                    </div>
                    <div className="flex items-start gap-2.5">
                      <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-brand-500 to-accent-500 text-white">
                        <Bot className="h-4 w-4" />
                      </div>
                      {ex.loading ? (
                        <div className="flex items-center gap-1.5 rounded-2xl rounded-bl-sm bg-ink-100 px-4 py-3 dark:bg-ink-800">
                          {[0, 1, 2].map((d) => (
                            <span
                              key={d}
                              className="h-1.5 w-1.5 animate-bounce rounded-full bg-ink-400"
                              style={{ animationDelay: `${d * 0.15}s` }}
                            />
                          ))}
                        </div>
                      ) : (
                        <div className="max-w-[80%] whitespace-pre-wrap rounded-2xl rounded-bl-sm bg-ink-100 px-4 py-2.5 text-sm text-ink-800 dark:bg-ink-800 dark:text-ink-100">
                          {ex.answer}
                        </div>
                      )}
                    </div>
                  </div>
                ))
              )}
              <div ref={bottomRef} />
            </div>
            <form onSubmit={handleSubmit} className="flex items-center gap-2 border-t border-ink-100 p-3 dark:border-ink-800">
              <input
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                placeholder="Savolingizni yozing..."
                className="h-11 flex-1 rounded-xl border border-ink-200 bg-white px-3.5 text-sm focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/40 dark:border-ink-700 dark:bg-ink-900 dark:text-white"
              />
              <button
                type="submit"
                disabled={!question.trim()}
                className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-brand-600 text-white transition-colors hover:bg-brand-700 disabled:opacity-50"
              >
                <Send className="h-4.5 w-4.5" />
              </button>
            </form>
          </div>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Zaif mavzular</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {!data ? (
              <Skeleton className="h-40 w-full" />
            ) : data.weak_topics.length === 0 ? (
              <EmptyState icon={Sparkles} title="Ajoyib!" description="Zaif mavzu aniqlanmadi" />
            ) : (
              data.weak_topics.map((t) => (
                <div key={t.subject} className="flex items-center justify-between rounded-xl border border-amber-200 bg-amber-50 p-3 dark:border-amber-500/30 dark:bg-amber-500/10">
                  <div className="flex items-center gap-2">
                    <TrendingDown className="h-4 w-4 text-amber-600 dark:text-amber-400" />
                    <p className="text-sm font-medium text-amber-800 dark:text-amber-300">{t.subject_name}</p>
                  </div>
                  <Badge tone="warning">{t.average}%</Badge>
                </div>
              ))
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
