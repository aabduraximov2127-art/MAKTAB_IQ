import { type FormEvent, useEffect, useState } from "react"
import { motion } from "framer-motion"
import { BookOpen, Plus, Trash2 } from "lucide-react"
import toast from "react-hot-toast"
import { useFetch } from "../hooks/useFetch"
import { api, getErrorMessage } from "../lib/api"
import { useAccess } from "../lib/access"
import { PageHeader } from "../components/ui/PageHeader"
import { Button } from "../components/ui/Button"
import { ConfirmButton } from "../components/ui/ConfirmButton"
import { Card, CardContent } from "../components/ui/Card"
import { Field, Input } from "../components/ui/Input"
import { Modal } from "../components/ui/Modal"
import { EmptyState } from "../components/ui/EmptyState"
import { CardSkeleton } from "../components/ui/Skeleton"
import type { Paginated, Subject } from "../types"
import { t } from "../i18n"

const GRADIENTS = [
  "from-brand-500 to-brand-700",
  "from-accent-500 to-accent-600",
  "from-emerald-500 to-emerald-600",
  "from-sky-500 to-sky-600",
  "from-rose-500 to-rose-600",
  "from-violet-500 to-violet-600",
]

export default function SubjectsPage() {
  const { can } = useAccess()
  const isAdmin = can("manage_subjects")
  const [addOpen, setAddOpen] = useState(false)
  const [editing, setEditing] = useState<Subject | null>(null)
  const { data, loading, refetch } = useFetch<Paginated<Subject>>("/subjects/?page_size=100")

  return (
    <div>
      <PageHeader
        title={t("Fanlar")}
        description={t("Maktabda o'qitiladigan fanlar ro'yxati")}
        actions={
          isAdmin && (
            <Button onClick={() => setAddOpen(true)}>
              <Plus className="h-4 w-4" /> Yangi fan
            </Button>
          )
        }
      />

      {loading ? (
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
          {Array.from({ length: 8 }).map((_, i) => (
            <CardSkeleton key={i} />
          ))}
        </div>
      ) : !data || data.results.length === 0 ? (
        <EmptyState icon={BookOpen} title={t("Fan topilmadi")} />
      ) : (
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
          {data.results.map((s, i) => (
            <motion.div key={s.id} initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} transition={{ delay: i * 0.03 }}>
              <Card
                className={`h-full transition-transform hover:-translate-y-0.5 hover:shadow-soft-lg ${isAdmin ? "cursor-pointer" : ""}`}
                onClick={isAdmin ? () => setEditing(s) : undefined}
              >
                <CardContent className="flex flex-col items-center gap-3 text-center">
                  <div
                    className={`flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-br text-2xl text-white ${GRADIENTS[i % GRADIENTS.length]}`}
                  >
                    {s.icon || <BookOpen className="h-5 w-5" />}
                  </div>
                  <p className="font-display font-semibold text-ink-800 dark:text-ink-100">{s.name}</p>
                  {s.description && <p className="line-clamp-2 text-xs text-ink-400">{s.description}</p>}
                </CardContent>
              </Card>
            </motion.div>
          ))}
        </div>
      )}

      <AddSubjectModal open={addOpen} onClose={() => setAddOpen(false)} onDone={() => { setAddOpen(false); refetch() }} />
      <EditSubjectModal subject={editing} onClose={() => setEditing(null)} onDone={() => { setEditing(null); refetch() }} />
    </div>
  )
}

/** Rename / re-describe a subject or delete it. The subject list is shared by every school, so the API
 * refuses to change one that other schools' lessons, grades or teachers use (its message is shown). */
function EditSubjectModal({ subject, onClose, onDone }: { subject: Subject | null; onClose: () => void; onDone: () => void }) {
  const [form, setForm] = useState({ name: "", description: "", icon: "" })
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (subject) setForm({ name: subject.name, description: subject.description, icon: subject.icon })
  }, [subject])

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    if (!subject) return
    setLoading(true)
    try {
      await api.patch(`/subjects/${subject.id}/`, form)
      toast.success(t("Fan yangilandi"))
      onDone()
    } catch (err) {
      toast.error(getErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  async function remove() {
    if (!subject) return
    setLoading(true)
    try {
      await api.delete(`/subjects/${subject.id}/`)
      toast.success(t("Fan o'chirildi"))
      onDone()
    } catch (err) {
      toast.error(getErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  return (
    <Modal open={!!subject} onClose={onClose} title={subject?.name ?? ""}>
      <form onSubmit={handleSubmit} className="space-y-4">
        <Field label={t("Nomi")}>
          <Input value={form.name} onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))} required />
        </Field>
        <Field label={t("Icon (emoji)")}>
          <Input value={form.icon} onChange={(e) => setForm((f) => ({ ...f, icon: e.target.value }))} />
        </Field>
        <Field label={t("Tavsif")}>
          <Input value={form.description} onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))} />
        </Field>
        <Button type="submit" className="w-full" loading={loading}>
          {t("Saqlash")}
        </Button>
        <ConfirmButton
          className="w-full"
          label={t("Fanni o'chirish")}
          confirmLabel={t("Ishonchingiz komilmi?")}
          icon={<Trash2 className="h-4 w-4" />}
          disabled={loading}
          onConfirm={remove}
        />
      </form>
    </Modal>
  )
}

function AddSubjectModal({ open, onClose, onDone }: { open: boolean; onClose: () => void; onDone: () => void }) {
  const [form, setForm] = useState({ name: "", description: "", icon: "" })
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setLoading(true)
    try {
      await api.post("/subjects/", form)
      toast.success(t("Fan qo'shildi"))
      setForm({ name: "", description: "", icon: "" })
      onDone()
    } catch (err) {
      toast.error(getErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  return (
    <Modal open={open} onClose={onClose} title={t("Yangi fan qo'shish")}>
      <form onSubmit={handleSubmit} className="space-y-4">
        <Field label={t("Nomi")}>
          <Input value={form.name} onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))} required />
        </Field>
        <Field label={t("Icon (emoji)")}>
          <Input value={form.icon} onChange={(e) => setForm((f) => ({ ...f, icon: e.target.value }))} placeholder="📐" />
        </Field>
        <Field label={t("Tavsif")}>
          <Input value={form.description} onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))} />
        </Field>
        <Button type="submit" className="w-full" loading={loading}>
          {t("Qo'shish")}
        </Button>
      </form>
    </Modal>
  )
}
