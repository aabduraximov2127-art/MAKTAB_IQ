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
import type { Paginated, TeacherProfile } from "../types"

const PAGE_SIZE = 10

export default function TeachersPage() {
  const [search, setSearch] = useState("")
  const [page, setPage] = useState(1)
  const [selected, setSelected] = useState<TeacherProfile | null>(null)

  const query = new URLSearchParams({ page: String(page), page_size: String(PAGE_SIZE) })
  if (search) query.set("search", search)

  const { data, loading } = useFetch<Paginated<TeacherProfile>>(`/teachers/?${query.toString()}`, [page, search])

  const columns: Column<TeacherProfile>[] = [
    {
      key: "name",
      header: "O'qituvchi",
      render: (row) => (
        <div className="flex items-center gap-3">
          <Avatar name={fullName(row.user)} src={row.avatar} size="sm" />
          <div className="min-w-0">
            <p className="truncate font-medium text-ink-800 dark:text-ink-100">{fullName(row.user)}</p>
            <p className="truncate text-xs text-ink-400">{row.teacher_id}</p>
          </div>
        </div>
      ),
    },
    {
      key: "experience",
      header: "Tajriba",
      render: (row) => <Badge tone="brand">{row.experience_years} yil</Badge>,
    },
    { key: "phone", header: "Telefon", render: (row) => row.user.phone || "—", hideOnMobile: true },
    { key: "email", header: "Email", render: (row) => row.user.email || "—", hideOnMobile: true },
  ]

  return (
    <div>
      <PageHeader title="O'qituvchilar" description="Maktabdagi barcha o'qituvchilar ro'yxati" />

      <div className="mb-4 max-w-xs">
        <Input
          icon={<Search className="h-4 w-4" />}
          placeholder="Ism yoki familiya bo'yicha qidirish..."
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
        emptyTitle="O'qituvchi topilmadi"
        onRowClick={setSelected}
      />

      {data && <Pagination page={page} count={data.count} pageSize={PAGE_SIZE} onChange={setPage} />}

      <Drawer open={!!selected} onClose={() => setSelected(null)} title={selected ? fullName(selected.user) : ""} subtitle={selected?.teacher_id}>
        {selected && (
          <div className="space-y-5">
            <div className="flex justify-center">
              <Avatar name={fullName(selected.user)} src={selected.avatar} size="lg" />
            </div>
            <DetailRow label="Tajriba" value={`${selected.experience_years} yil`} />
            <DetailRow label="Telefon" value={selected.user.phone || "—"} />
            <DetailRow label="Email" value={selected.user.email || "—"} />
          </div>
        )}
      </Drawer>
    </div>
  )
}

function DetailRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between border-b border-ink-100 pb-3 text-sm dark:border-ink-800">
      <span className="text-ink-500 dark:text-ink-400">{label}</span>
      <span className="font-medium text-ink-800 dark:text-ink-100">{value}</span>
    </div>
  )
}
