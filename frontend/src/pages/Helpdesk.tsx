import { type FormEvent, useState } from "react"
import { Headset, Plus } from "lucide-react"
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
import { Drawer } from "../components/ui/Drawer"
import { Badge } from "../components/ui/Badge"
import { DataTable, type Column } from "../components/ui/Table"
import { ContactInfo } from "../components/shared/ContactInfo"
import { formatDate } from "../lib/format"
import type { HelpDeskTicket, Paginated } from "../types"

const STATUS_TONE: Record<HelpDeskTicket["status"], "info" | "warning" | "success" | "neutral"> = {
  OPEN: "info",
  IN_PROGRESS: "warning",
  RESOLVED: "success",
  CLOSED: "neutral",
}

const STATUS_LABELS: Record<HelpDeskTicket["status"], string> = {
  OPEN: "Ochiq",
  IN_PROGRESS: "Jarayonda",
  RESOLVED: "Yechilgan",
  CLOSED: "Yopilgan",
}

const PRIORITY_LABELS: Record<HelpDeskTicket["priority"], string> = { LOW: "Past", MEDIUM: "O'rtacha", HIGH: "Yuqori" }

export default function HelpdeskPage() {
  const user = useAuthStore((s) => s.user)
  const isAdmin = user?.role === "ADMIN" || user?.role === "SUPERADMIN"
  const [addOpen, setAddOpen] = useState(false)
  const [selected, setSelected] = useState<HelpDeskTicket | null>(null)

  const { data, loading, refetch } = useFetch<Paginated<HelpDeskTicket>>("/helpdesk/?ordering=-created_at&page_size=50")

  const columns: Column<HelpDeskTicket>[] = [
    { key: "title", header: "Sarlavha", render: (r) => <p className="font-medium text-ink-800 dark:text-ink-100">{r.title}</p> },
    { key: "category", header: "Kategoriya", render: (r) => r.category, hideOnMobile: true },
    { key: "priority", header: "Muhimlik", render: (r) => PRIORITY_LABELS[r.priority], hideOnMobile: true },
    { key: "status", header: "Status", render: (r) => <Badge tone={STATUS_TONE[r.status]}>{STATUS_LABELS[r.status]}</Badge> },
    { key: "date", header: "Sana", render: (r) => formatDate(r.created_at), hideOnMobile: true },
  ]

  return (
    <div>
      <PageHeader
        title="Yordam"
        description={isAdmin ? "Foydalanuvchilar murojaatlari" : "Muammo yoki savolingiz bo'yicha murojaat qiling"}
        actions={
          <Button onClick={() => setAddOpen(true)}>
            <Plus className="h-4 w-4" /> Yangi murojaat
          </Button>
        }
      />

      <Card className="mb-5">
        <CardHeader>
          <div className="flex items-center gap-2">
            <Headset className="h-4 w-4 text-brand-500" />
            <CardTitle>Tezkor yordam kerakmi?</CardTitle>
          </div>
        </CardHeader>
        <CardContent>
          <ContactInfo variant="light" />
        </CardContent>
      </Card>

      <DataTable
        columns={columns}
        rows={data?.results ?? []}
        keyField={(r) => r.id}
        loading={loading}
        emptyTitle="Murojaat topilmadi"
        onRowClick={setSelected}
      />

      <TicketDrawer ticket={selected} isAdmin={!!isAdmin} onClose={() => setSelected(null)} onUpdated={refetch} />
      <AddTicketModal open={addOpen} onClose={() => setAddOpen(false)} onDone={() => { setAddOpen(false); refetch() }} />
    </div>
  )
}

function TicketDrawer({
  ticket,
  isAdmin,
  onClose,
  onUpdated,
}: {
  ticket: HelpDeskTicket | null
  isAdmin: boolean
  onClose: () => void
  onUpdated: () => void
}) {
  const [status, setStatus] = useState<HelpDeskTicket["status"] | "">("")

  async function updateStatus(newStatus: string) {
    if (!ticket) return
    try {
      await api.patch(`/helpdesk/${ticket.id}/`, { status: newStatus })
      toast.success("Status yangilandi")
      onUpdated()
    } catch (err) {
      toast.error(getErrorMessage(err))
    }
  }

  return (
    <Drawer open={!!ticket} onClose={onClose} title={ticket?.title} subtitle={ticket ? formatDate(ticket.created_at) : ""}>
      {ticket && (
        <div className="space-y-4">
          <p className="text-sm text-ink-600 dark:text-ink-300">{ticket.description}</p>
          <div className="flex flex-wrap gap-2">
            <Badge tone="neutral">{ticket.category}</Badge>
            <Badge tone="neutral">{PRIORITY_LABELS[ticket.priority]}</Badge>
            <Badge tone={STATUS_TONE[ticket.status]}>{STATUS_LABELS[ticket.status]}</Badge>
          </div>
          {isAdmin && (
            <Field label="Statusni o'zgartirish">
              <Select value={status || ticket.status} onChange={(e) => { setStatus(e.target.value as HelpDeskTicket["status"]); updateStatus(e.target.value) }}>
                {Object.entries(STATUS_LABELS).map(([key, label]) => (
                  <option key={key} value={key}>
                    {label}
                  </option>
                ))}
              </Select>
            </Field>
          )}
        </div>
      )}
    </Drawer>
  )
}

function AddTicketModal({ open, onClose, onDone }: { open: boolean; onClose: () => void; onDone: () => void }) {
  const [form, setForm] = useState({ title: "", description: "", category: "OTHER", priority: "MEDIUM" })
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setLoading(true)
    try {
      await api.post("/helpdesk/", form)
      toast.success("Murojaat yuborildi")
      setForm({ title: "", description: "", category: "OTHER", priority: "MEDIUM" })
      onDone()
    } catch (err) {
      toast.error(getErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  return (
    <Modal open={open} onClose={onClose} title="Yangi murojaat">
      <form onSubmit={handleSubmit} className="space-y-4">
        <Field label="Sarlavha">
          <Input value={form.title} onChange={(e) => setForm((f) => ({ ...f, title: e.target.value }))} required />
        </Field>
        <Field label="Tavsif">
          <textarea
            value={form.description}
            onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))}
            rows={4}
            required
            className="w-full rounded-xl border border-ink-200 bg-white p-3 text-sm focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/40 dark:border-ink-700 dark:bg-ink-900 dark:text-white"
          />
        </Field>
        <div className="grid grid-cols-2 gap-4">
          <Field label="Kategoriya">
            <Select value={form.category} onChange={(e) => setForm((f) => ({ ...f, category: e.target.value }))}>
              <option value="TECHNICAL">Texnik</option>
              <option value="ACADEMIC">O'quv</option>
              <option value="ACCOUNT">Hisob</option>
              <option value="OTHER">Boshqa</option>
            </Select>
          </Field>
          <Field label="Muhimlik">
            <Select value={form.priority} onChange={(e) => setForm((f) => ({ ...f, priority: e.target.value }))}>
              <option value="LOW">Past</option>
              <option value="MEDIUM">O'rtacha</option>
              <option value="HIGH">Yuqori</option>
            </Select>
          </Field>
        </div>
        <Button type="submit" className="w-full" loading={loading}>
          Yuborish
        </Button>
      </form>
    </Modal>
  )
}
