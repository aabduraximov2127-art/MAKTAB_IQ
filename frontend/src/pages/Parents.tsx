import { useState } from "react"
import { Search } from "lucide-react"
import { useFetch } from "../hooks/useFetch"
import { PageHeader } from "../components/ui/PageHeader"
import { Input } from "../components/ui/Input"
import { DataTable, type Column } from "../components/ui/Table"
import { Pagination } from "../components/ui/Pagination"
import { Drawer } from "../components/ui/Drawer"
import { Avatar } from "../components/ui/Avatar"
import { Badge } from "../components/ui/Badge"
import { fullName } from "../lib/format"
import type { ParentProfile, Paginated } from "../types"
import { t } from "../i18n"

const PAGE_SIZE = 10

export default function ParentsPage() {
  const [search, setSearch] = useState("")
  const [page, setPage] = useState(1)
  const [selected, setSelected] = useState<ParentProfile | null>(null)

  const query = new URLSearchParams({ page: String(page), page_size: String(PAGE_SIZE) })
  if (search) query.set("search", search)

  const { data, loading } = useFetch<Paginated<ParentProfile>>(`/parents/?${query.toString()}`, [page, search])

  const columns: Column<ParentProfile>[] = [
    {
      key: "name",
      header: t("Ota-ona"),
      render: (row) => (
        <div className="flex items-center gap-3">
          <Avatar name={fullName(row.user)} size="sm" />
          <p className="truncate font-medium text-ink-800 dark:text-ink-100">{fullName(row.user)}</p>
        </div>
      ),
    },
    {
      key: "children",
      header: t("Farzandlar"),
      render: (row) => (
        <div className="flex flex-wrap gap-1">
          {row.children.length === 0 ? (
            <span className="text-ink-400">—</span>
          ) : (
            row.children.map((c) => <Badge key={c.id}>{fullName(c.user)}</Badge>)
          )}
        </div>
      ),
    },
    { key: "phone", header: t("Telefon"), render: (row) => row.user.phone || "—", hideOnMobile: true },
  ]

  return (
    <div>
      <PageHeader title={t("Ota-onalar")} description={t("Tizimga ulangan ota-onalar ro'yxati")} />

      <div className="mb-4 max-w-xs">
        <Input
          icon={<Search className="h-4 w-4" />}
          placeholder={t("Qidirish...")}
          value={search}
          onChange={(e) => {
            setSearch(e.target.value)
            setPage(1)
          }}
        />
      </div>

      <DataTable
        columns={columns}
        rows={data?.results ?? []}
        keyField={(r) => r.id}
        loading={loading}
        emptyTitle={t("Ota-ona topilmadi")}
        onRowClick={setSelected}
      />

      {data && <Pagination page={page} count={data.count} pageSize={PAGE_SIZE} onChange={setPage} />}

      <Drawer open={!!selected} onClose={() => setSelected(null)} title={selected ? fullName(selected.user) : ""}>
        {selected && (
          <div className="space-y-4">
            <p className="text-sm font-medium text-ink-500 dark:text-ink-400">{t("Farzandlari")}</p>
            {selected.children.length === 0 ? (
              <p className="text-sm text-ink-400">{t("Farzand biriktirilmagan")}</p>
            ) : (
              selected.children.map((c) => (
                <div key={c.id} className="flex items-center gap-3 rounded-xl border border-ink-100 p-3 dark:border-ink-800">
                  <Avatar name={fullName(c.user)} src={c.photo} size="sm" />
                  <div>
                    <p className="text-sm font-medium text-ink-800 dark:text-ink-100">{fullName(c.user)}</p>
                    <p className="text-xs text-ink-400">{c.class_room_name ?? t("Sinf biriktirilmagan")}</p>
                  </div>
                </div>
              ))
            )}
          </div>
        )}
      </Drawer>
    </div>
  )
}
