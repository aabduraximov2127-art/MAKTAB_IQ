import { useState } from "react"
import { motion } from "framer-motion"
import { Bell, CheckCheck } from "lucide-react"
import toast from "react-hot-toast"
import { useFetch } from "../hooks/useFetch"
import { api, getErrorMessage } from "../lib/api"
import { PageHeader } from "../components/ui/PageHeader"
import { Button } from "../components/ui/Button"
import { Card, CardContent } from "../components/ui/Card"
import { EmptyState } from "../components/ui/EmptyState"
import { CardSkeleton } from "../components/ui/Skeleton"
import { Pagination } from "../components/ui/Pagination"
import { labelFor } from "../hooks/useNotificationSocket"
import { formatRelative } from "../lib/format"
import { cn } from "../lib/cn"
import type { Notification, Paginated } from "../types"

const PAGE_SIZE = 15

export default function NotificationsPage() {
  const [page, setPage] = useState(1)
  const { data, loading, refetch } = useFetch<Paginated<Notification>>(
    `/notifications/?page=${page}&page_size=${PAGE_SIZE}`,
    [page]
  )

  async function markRead(id: number) {
    try {
      await api.post(`/notifications/${id}/mark_read/`)
      refetch()
    } catch (err) {
      toast.error(getErrorMessage(err))
    }
  }

  async function markAllRead() {
    try {
      await api.post("/notifications/mark_all_read/")
      toast.success("Barchasi o'qilgan deb belgilandi")
      refetch()
    } catch (err) {
      toast.error(getErrorMessage(err))
    }
  }

  return (
    <div>
      <PageHeader
        title="Bildirishnomalar"
        description="Barcha bildirishnomalaringiz"
        actions={
          <Button variant="outline" onClick={markAllRead}>
            <CheckCheck className="h-4 w-4" /> Hammasini o'qish
          </Button>
        }
      />

      {loading ? (
        <div className="space-y-3">
          {Array.from({ length: 5 }).map((_, i) => (
            <CardSkeleton key={i} />
          ))}
        </div>
      ) : !data || data.results.length === 0 ? (
        <EmptyState icon={Bell} title="Bildirishnoma yo'q" />
      ) : (
        <div className="space-y-2.5">
          {data.results.map((n, i) => (
            <motion.div key={n.id} initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.02 }}>
              <Card
                onClick={() => !n.is_read && markRead(n.id)}
                className={cn("cursor-pointer transition-colors", !n.is_read && "border-brand-200 bg-brand-50/40 dark:border-brand-500/30 dark:bg-brand-500/5")}
              >
                <CardContent className="flex items-start justify-between gap-3">
                  <div>
                    <p className="text-xs font-semibold uppercase tracking-wide text-brand-600 dark:text-brand-400">{labelFor(n.type)}</p>
                    <p className="mt-0.5 font-medium text-ink-800 dark:text-ink-100">{n.title}</p>
                    <p className="mt-1 text-sm text-ink-500 dark:text-ink-400">{n.message}</p>
                    <p className="mt-1.5 text-xs text-ink-400">{formatRelative(n.created_at)}</p>
                  </div>
                  {!n.is_read && <span className="mt-1 h-2 w-2 shrink-0 rounded-full bg-brand-500" />}
                </CardContent>
              </Card>
            </motion.div>
          ))}
        </div>
      )}

      {data && <Pagination page={page} count={data.count} pageSize={PAGE_SIZE} onChange={setPage} />}
    </div>
  )
}
