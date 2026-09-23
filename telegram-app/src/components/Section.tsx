import type { ReactNode } from "react"

export function Section({ title, children }: { title: string; children: ReactNode }) {
  return (
    <div className="section">
      <div className="section-title">{title}</div>
      <div className="section-body">{children}</div>
    </div>
  )
}

export function Row({
  title,
  sub,
  value,
  unread,
}: {
  title: string
  sub?: string
  value?: ReactNode
  unread?: boolean
}) {
  return (
    <div className="row">
      <div className="row-main">
        <div className="row-title">
          {unread && <span className="dot" />}
          {title}
        </div>
        {sub && <div className="row-sub">{sub}</div>}
      </div>
      {value !== undefined && <div className="row-value">{value}</div>}
    </div>
  )
}

export function EmptyRow({ text }: { text: string }) {
  return <div className="empty-row">{text}</div>
}
