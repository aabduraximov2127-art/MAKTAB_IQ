import { type FormEvent, useState } from "react"
import { motion } from "framer-motion"
import { BookOpen, ExternalLink, FileText, LibraryBig, Link2, Plus, Video } from "lucide-react"
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
import { EmptyState } from "../components/ui/EmptyState"
import { CardSkeleton } from "../components/ui/Skeleton"
import type { LibraryMaterial, Paginated, Subject } from "../types"
import { t } from "../i18n"

const TYPE_META: Record<LibraryMaterial["material_type"], { label: string; icon: typeof BookOpen; color: string }> = {
  BOOK: { label: t("Kitob"), icon: BookOpen, color: "from-brand-500 to-brand-700" },
  PDF: { label: "PDF", icon: FileText, color: "from-rose-500 to-rose-600" },
  DOCUMENT: { label: t("Hujjat"), icon: FileText, color: "from-sky-500 to-sky-600" },
  LESSON_MATERIAL: { label: t("Dars materiali"), icon: LibraryBig, color: "from-accent-500 to-accent-600" },
  VIDEO: { label: t("Video"), icon: Video, color: "from-violet-500 to-violet-600" },
  LINK: { label: t("Havola"), icon: Link2, color: "from-emerald-500 to-emerald-600" },
}

export default function LibraryPage() {
  const user = useAuthStore((s) => s.user)
  // SUPERADMIN can only browse the library, never upload — that's ADMIN/TEACHER's job.
  const canManage = user?.role === "TEACHER" || user?.role === "ADMIN"
  const [typeFilter, setTypeFilter] = useState("")
  const [addOpen, setAddOpen] = useState(false)

  const query = new URLSearchParams({ page_size: "60" })
  if (typeFilter) query.set("material_type", typeFilter)

  const { data, loading, refetch } = useFetch<Paginated<LibraryMaterial>>(`/library/?${query.toString()}`, [typeFilter])

  return (
    <div>
      <PageHeader
        title={t("Kutubxona")}
        description={t("Elektron kitob, video va dars materiallari")}
        actions={
          canManage && (
            <Button onClick={() => setAddOpen(true)}>
              <Plus className="h-4 w-4" /> Material qo'shish
            </Button>
          )
        }
      />

      <div className="mb-4 max-w-xs">
        <Select value={typeFilter} onChange={(e) => setTypeFilter(e.target.value)}>
          <option value="">{t("Barcha turlar")}</option>
          {Object.entries(TYPE_META).map(([key, meta]) => (
            <option key={key} value={key}>
              {meta.label}
            </option>
          ))}
        </Select>
      </div>

      {loading ? (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {Array.from({ length: 8 }).map((_, i) => (
            <CardSkeleton key={i} />
          ))}
        </div>
      ) : !data || data.results.length === 0 ? (
        <EmptyState icon={LibraryBig} title={t("Material topilmadi")} />
      ) : (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {data.results.map((m, i) => {
            const meta = TYPE_META[m.material_type]
            const href = m.file || m.link
            return (
              <motion.div key={m.id} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.03 }}>
                <Card className="h-full transition-transform hover:-translate-y-0.5 hover:shadow-soft-lg">
                  <CardContent className="flex h-full flex-col">
                    <div className={`flex h-11 w-11 items-center justify-center rounded-xl bg-gradient-to-br text-white ${meta.color}`}>
                      <meta.icon className="h-5 w-5" />
                    </div>
                    <p className="mt-3 line-clamp-2 font-display text-sm font-semibold text-ink-800 dark:text-ink-100">{m.title}</p>
                    <p className="mt-1 text-xs text-ink-400">{m.author || meta.label}</p>
                    {href && (
                      <a
                        href={href}
                        target="_blank"
                        rel="noreferrer"
                        className="mt-auto flex items-center gap-1 pt-3 text-xs font-medium text-brand-600 dark:text-brand-400"
                      >
                        Ochish <ExternalLink className="h-3 w-3" />
                      </a>
                    )}
                  </CardContent>
                </Card>
              </motion.div>
            )
          })}
        </div>
      )}

      <AddMaterialModal open={addOpen} onClose={() => setAddOpen(false)} onDone={() => { setAddOpen(false); refetch() }} />
    </div>
  )
}

function AddMaterialModal({ open, onClose, onDone }: { open: boolean; onClose: () => void; onDone: () => void }) {
  const { data: subjects } = useFetch<Paginated<Subject>>(open ? "/subjects/?page_size=100" : null)
  const [form, setForm] = useState({ title: "", material_type: "BOOK", subject: "", author: "", link: "" })
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setLoading(true)
    try {
      await api.post("/library/", form)
      toast.success(t("Material qo'shildi"))
      setForm({ title: "", material_type: "BOOK", subject: "", author: "", link: "" })
      onDone()
    } catch (err) {
      toast.error(getErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  return (
    <Modal open={open} onClose={onClose} title={t("Yangi material qo'shish")}>
      <form onSubmit={handleSubmit} className="space-y-4">
        <Field label={t("Nomi")}>
          <Input value={form.title} onChange={(e) => setForm((f) => ({ ...f, title: e.target.value }))} required />
        </Field>
        <Field label={t("Turi")}>
          <Select value={form.material_type} onChange={(e) => setForm((f) => ({ ...f, material_type: e.target.value }))}>
            {Object.entries(TYPE_META).map(([key, meta]) => (
              <option key={key} value={key}>
                {meta.label}
              </option>
            ))}
          </Select>
        </Field>
        <Field label={t("Fan")}>
          <Select value={form.subject} onChange={(e) => setForm((f) => ({ ...f, subject: e.target.value }))}>
            <option value="">{t("Tanlanmagan")}</option>
            {subjects?.results.map((s) => (
              <option key={s.id} value={s.id}>
                {s.name}
              </option>
            ))}
          </Select>
        </Field>
        <Field label={t("Muallif")}>
          <Input value={form.author} onChange={(e) => setForm((f) => ({ ...f, author: e.target.value }))} />
        </Field>
        <Field label={t("Havola (link)")}>
          <Input value={form.link} onChange={(e) => setForm((f) => ({ ...f, link: e.target.value }))} placeholder="https://..." />
        </Field>
        <Button type="submit" className="w-full" loading={loading}>
          {t("Qo'shish")}
        </Button>
      </form>
    </Modal>
  )
}
