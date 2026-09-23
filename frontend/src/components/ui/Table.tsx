import type { ReactNode } from "react"
import { TableSkeleton } from "./Skeleton"
import { EmptyState } from "./EmptyState"
import { t } from "../../i18n"

export interface Column<T> {
  key: string
  header: string
  render: (row: T) => ReactNode
  className?: string
  hideOnMobile?: boolean
}

interface DataTableProps<T> {
  columns: Column<T>[]
  rows: T[]
  keyField: (row: T) => string | number
  loading?: boolean
  emptyTitle?: string
  emptyDescription?: string
  onRowClick?: (row: T) => void
}

export function DataTable<T>({
  columns,
  rows,
  keyField,
  loading,
  emptyTitle = t("Hech narsa topilmadi"),
  emptyDescription,
  onRowClick,
}: DataTableProps<T>) {
  if (loading) return <TableSkeleton rows={6} />
  if (rows.length === 0) return <EmptyState title={emptyTitle} description={emptyDescription} />

  return (
    <div className="overflow-x-auto rounded-2xl border border-ink-100 dark:border-ink-800">
      <table className="w-full min-w-[560px] border-collapse text-sm">
        <thead>
          <tr className="border-b border-ink-100 bg-ink-50/60 dark:border-ink-800 dark:bg-ink-900/60">
            {columns.map((col) => (
              <th
                key={col.key}
                className={`px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-ink-500 dark:text-ink-400 ${
                  col.hideOnMobile ? "hidden sm:table-cell" : ""
                } ${col.className ?? ""}`}
              >
                {col.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            <tr
              key={keyField(row)}
              onClick={() => onRowClick?.(row)}
              className={`border-b border-ink-50 bg-white transition-colors last:border-0 dark:border-ink-800/60 dark:bg-ink-900 ${
                onRowClick ? "cursor-pointer hover:bg-brand-50/60 dark:hover:bg-ink-800/60" : ""
              }`}
              style={{ animationDelay: `${i * 20}ms` }}
            >
              {columns.map((col) => (
                <td
                  key={col.key}
                  className={`px-4 py-3.5 text-ink-700 dark:text-ink-200 ${
                    col.hideOnMobile ? "hidden sm:table-cell" : ""
                  } ${col.className ?? ""}`}
                >
                  {col.render(row)}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
