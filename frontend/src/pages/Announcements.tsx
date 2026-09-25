import { type FormEvent, useState } from "react"
import { motion } from "framer-motion"
import { AlertTriangle, Megaphone, Plus, Siren } from "lucide-react"
import toast from "react-hot-toast"
import { useFetch } from "../hooks/useFetch"
import { api, getErrorMessage } from "../lib/api"
import { useAccess } from "../lib/access"
import { PageHeader } from "../components/ui/PageHeader"
import { Button } from "../components/ui/Button"
import { Card, CardContent } from "../components/ui/Card"
import { Field, Input } from "../components/ui/Input"
import { Select } from "../components/ui/Select"
import { Modal } from "../components/ui/Modal"
import { Badge } from "../components/ui/Badge"
import { EmptyState } from "../components/ui/EmptyState"
import { Tabs } from "../components/ui/Tabs"
import { CardSkeleton } from "../components/ui/Skeleton"
import { formatRelative } from "../lib/format"
import type { Announcement, ClassRoom, Paginated } from "../types"
import { t } from "../i18n"

const TARGET_LABELS: Record<Announcement["target"], string> = {
  ALL: t("Barcha maktab"),
  TEACHERS: t("O'qituvchilar"),
  STUDENTS: t("O'quvchilar"),
  PARENTS: t("Ota-onalar"),
  CLASS: t("Ma'lum sinf"),
}

export default function AnnouncementsPage() {
  const { can, canAny } = useAccess()
  const canSendAll = can("send_announcements") // whole school / any audience + emergency messages
  const canSend = canAny("send_announcements", "send_class_announcement") // a class teacher: own class only
  const [tab, setTab] = useState<"normal" | "emergency">("normal")
  const [addOpen, setAddOpen] = useState(false)
  const [emergencyOpen, setEmergencyOpen] = useState(false)

  const { data, loading, refetch } = useFetch<Paginated<Announcement>>("/notifications/announcements/?page_size=50")
  const { data: emergencies, loading: emergenciesLoading, refetch: refetchEmergencies } = useFetch<
    Paginated<{ id: number; title: string; content: string; created_at: string }>
  >("/notifications/emergency-announcements/?page_size=50")

  return (
    <div>
      <PageHeader
        title={t("E'lonlar")}
        description={t("Maktab bo'ylab e'lonlar va muhim xabarlar")}
        actions={
          canSend && (
            <div className="flex gap-2">
              {tab === "emergency" ? (
                canSendAll && (
                  <Button variant="danger" onClick={() => setEmergencyOpen(true)}>
                    <Siren className="h-4 w-4" /> Favqulodda xabar
                  </Button>
                )
              ) : (
                <Button onClick={() => setAddOpen(true)}>
                  <Plus className="h-4 w-4" /> Yangi e'lon
                </Button>
              )}
            </div>
          )
        }
      />

      <div className="mb-4">
        <Tabs
          tabs={[
            { key: "normal", label: t("Oddiy e'lonlar"), count: data?.count },
            { key: "emergency", label: t("Favqulodda"), count: emergencies?.count },
          ]}
          active={tab}
          onChange={(k) => setTab(k as "normal" | "emergency")}
        />
      </div>

      {tab === "normal" ? (
        loading ? (
          <div className="space-y-3">
            {Array.from({ length: 4 }).map((_, i) => (
              <CardSkeleton key={i} />
            ))}
          </div>
        ) : !data || data.results.length === 0 ? (
          <EmptyState icon={Megaphone} title={t("E'lon yo'q")} />
        ) : (
          <div className="space-y-3">
            {data.results.map((a, i) => (
              <motion.div key={a.id} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.03 }}>
                <Card>
                  <CardContent>
                    <div className="flex items-start justify-between gap-3">
                      <div className="flex items-start gap-3">
                        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-brand-50 text-brand-600 dark:bg-brand-500/10 dark:text-brand-400">
                          <Megaphone className="h-4.5 w-4.5" />
                        </div>
                        <div>
                          <p className="font-display font-semibold text-ink-800 dark:text-ink-100">{a.title}</p>
                          <p className="mt-1 text-sm text-ink-600 dark:text-ink-300">{a.content}</p>
                          <div className="mt-2 flex items-center gap-2 text-xs text-ink-400">
                            <Badge tone="neutral">{TARGET_LABELS[a.target]}</Badge>
                            {a.priority === "HIGH" && <Badge tone="danger">{t("Muhim")}</Badge>}
                            <span>{formatRelative(a.created_at)}</span>
                          </div>
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </motion.div>
            ))}
          </div>
        )
      ) : emergenciesLoading ? (
        <div className="space-y-3">
          {Array.from({ length: 3 }).map((_, i) => (
            <CardSkeleton key={i} />
          ))}
        </div>
      ) : !emergencies || emergencies.results.length === 0 ? (
        <EmptyState icon={Siren} title={t("Favqulodda xabar yo'q")} />
      ) : (
        <div className="space-y-3">
          {emergencies.results.map((e, i) => (
            <motion.div key={e.id} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.03 }}>
              <Card className="border-rose-200 dark:border-rose-500/30">
                <CardContent className="flex items-start gap-3">
                  <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-rose-100 text-rose-600 dark:bg-rose-500/15 dark:text-rose-400">
                    <AlertTriangle className="h-4.5 w-4.5" />
                  </div>
                  <div>
                    <p className="font-display font-semibold text-rose-700 dark:text-rose-300">{e.title}</p>
                    <p className="mt-1 text-sm text-ink-600 dark:text-ink-300">{e.content}</p>
                    <p className="mt-2 text-xs text-ink-400">{formatRelative(e.created_at)}</p>
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          ))}
        </div>
      )}

      <AddAnnouncementModal
        open={addOpen}
        classOnly={!canSendAll}
        onClose={() => setAddOpen(false)}
        onDone={() => {
          setAddOpen(false)
          refetch()
        }}
      />
      <AddEmergencyModal
        open={emergencyOpen}
        onClose={() => setEmergencyOpen(false)}
        onDone={() => {
          setEmergencyOpen(false)
          refetchEmergencies()
        }}
      />
    </div>
  )
}

function AddEmergencyModal({ open, onClose, onDone }: { open: boolean; onClose: () => void; onDone: () => void }) {
  const [form, setForm] = useState({ title: "", content: "" })
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setLoading(true)
    try {
      await api.post("/notifications/emergency-announcements/", form)
      toast.success(t("Favqulodda xabar yuborildi"))
      setForm({ title: "", content: "" })
      onDone()
    } catch (err) {
      toast.error(getErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  return (
    <Modal open={open} onClose={onClose} title={t("Favqulodda xabar yuborish")}>
      <form onSubmit={handleSubmit} className="space-y-4">
        <p className="rounded-xl bg-rose-50 px-3.5 py-2.5 text-xs text-rose-600 dark:bg-rose-500/10 dark:text-rose-400">
          {t("Bu xabar Web va Telegram orqali barcha foydalanuvchilarga darhol yuboriladi.")}
        </p>
        <Field label={t("Sarlavha")}>
          <Input value={form.title} onChange={(e) => setForm((f) => ({ ...f, title: e.target.value }))} required />
        </Field>
        <Field label={t("Matn")}>
          <textarea
            value={form.content}
            onChange={(e) => setForm((f) => ({ ...f, content: e.target.value }))}
            rows={3}
            required
            className="w-full rounded-xl border border-ink-200 bg-white p-3 text-sm focus:border-rose-500 focus:outline-none focus:ring-2 focus:ring-rose-400/40 dark:border-ink-700 dark:bg-ink-900 dark:text-white"
          />
        </Field>
        <Button type="submit" variant="danger" className="w-full" loading={loading}>
          {t("Yuborish")}
        </Button>
      </form>
    </Modal>
  )
}

function AddAnnouncementModal({
  open,
  classOnly,
  onClose,
  onDone,
}: {
  open: boolean
  /** A class teacher may only address the class they curate. */
  classOnly: boolean
  onClose: () => void
  onDone: () => void
}) {
  const { user } = useAccess()
  const { data: allClasses } = useFetch<Paginated<ClassRoom>>(open ? "/classes/?page_size=100" : null)
  const curated = new Set((user?.curated_classes ?? []).map((c) => c.id))
  const classes = allClasses ? { ...allClasses, results: classOnly ? allClasses.results.filter((c) => curated.has(c.id)) : allClasses.results } : allClasses
  const [form, setForm] = useState({ title: "", content: "", priority: "NORMAL", target: classOnly ? "CLASS" : "ALL", target_class: "" })
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setLoading(true)
    try {
      await api.post("/notifications/announcements/", { ...form, target_class: form.target === "CLASS" ? form.target_class : null })
      toast.success(t("E'lon yuborildi"))
      setForm({ title: "", content: "", priority: "NORMAL", target: "ALL", target_class: "" })
      onDone()
    } catch (err) {
      toast.error(getErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  return (
    <Modal open={open} onClose={onClose} title={t("Yangi e'lon")}>
      <form onSubmit={handleSubmit} className="space-y-4">
        <Field label={t("Sarlavha")}>
          <Input value={form.title} onChange={(e) => setForm((f) => ({ ...f, title: e.target.value }))} required />
        </Field>
        <Field label={t("Matn")}>
          <textarea
            value={form.content}
            onChange={(e) => setForm((f) => ({ ...f, content: e.target.value }))}
            rows={3}
            required
            className="w-full rounded-xl border border-ink-200 bg-white p-3 text-sm focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/40 dark:border-ink-700 dark:bg-ink-900 dark:text-white"
          />
        </Field>
        <div className="grid grid-cols-2 gap-4">
          <Field label={t("Kimga")}>
            <Select value={form.target} onChange={(e) => setForm((f) => ({ ...f, target: e.target.value }))}>
              {Object.entries(TARGET_LABELS)
                .filter(([key]) => !classOnly || key === "CLASS")
                .map(([key, label]) => (
                <option key={key} value={key}>
                  {label}
                </option>
                ))}
            </Select>
          </Field>
          <Field label={t("Muhimlik")}>
            <Select value={form.priority} onChange={(e) => setForm((f) => ({ ...f, priority: e.target.value }))}>
              <option value="LOW">{t("Past")}</option>
              <option value="NORMAL">{t("O'rtacha")}</option>
              <option value="HIGH">{t("Yuqori")}</option>
            </Select>
          </Field>
        </div>
        {form.target === "CLASS" && (
          <Field label={t("Sinf")}>
            <Select value={form.target_class} onChange={(e) => setForm((f) => ({ ...f, target_class: e.target.value }))} required>
              <option value="">{t("Tanlang...")}</option>
              {classes?.results.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name}
                </option>
              ))}
            </Select>
          </Field>
        )}
        <Button type="submit" className="w-full" loading={loading}>
          {t("Yuborish")}
        </Button>
      </form>
    </Modal>
  )
}
