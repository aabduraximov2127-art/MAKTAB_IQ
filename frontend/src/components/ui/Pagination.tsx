import { ChevronLeft, ChevronRight } from "lucide-react"
import { Button } from "./Button"

interface PaginationProps {
  page: number
  count: number
  pageSize: number
  onChange: (page: number) => void
}

export function Pagination({ page, count, pageSize, onChange }: PaginationProps) {
  const totalPages = Math.max(1, Math.ceil(count / pageSize))
  if (totalPages <= 1) return null

  return (
    <div className="mt-4 flex items-center justify-between">
      <p className="text-sm text-ink-500 dark:text-ink-400">
        Jami <span className="font-medium text-ink-700 dark:text-ink-200">{count}</span> ta natija
      </p>
      <div className="flex items-center gap-2">
        <Button variant="outline" size="icon" disabled={page <= 1} onClick={() => onChange(page - 1)}>
          <ChevronLeft className="h-4 w-4" />
        </Button>
        <span className="text-sm text-ink-600 dark:text-ink-300">
          {page} / {totalPages}
        </span>
        <Button variant="outline" size="icon" disabled={page >= totalPages} onClick={() => onChange(page + 1)}>
          <ChevronRight className="h-4 w-4" />
        </Button>
      </div>
    </div>
  )
}
