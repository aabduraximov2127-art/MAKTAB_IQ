import { Headset, Phone, Send } from "lucide-react"

const ADMIN_TELEGRAM = "abduraximov_uz7"
const BOT_TELEGRAM = "maktabIQ_bot"
const CALL_CENTER_NUMBERS = ["+998950391009", "+998901251103"]

interface ContactInfoProps {
  variant?: "dark" | "light"
  className?: string
}

/** Admin/bot Telegram + call-center numbers — used on the Login page and Helpdesk. */
export function ContactInfo({ variant = "dark", className = "" }: ContactInfoProps) {
  const isDark = variant === "dark"
  const rowClass = isDark
    ? "flex items-center gap-2.5 text-ink-300"
    : "flex items-center gap-2.5 text-ink-600 dark:text-ink-300"
  const iconWrapClass = isDark
    ? "flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-white/10 text-brand-300"
    : "flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-brand-50 text-brand-600 dark:bg-brand-500/10 dark:text-brand-400"
  const labelClass = isDark ? "text-xs text-ink-400" : "text-xs text-ink-400 dark:text-ink-500"
  const valueClass = isDark ? "text-sm font-medium text-white" : "text-sm font-medium text-ink-800 dark:text-ink-100"

  return (
    <div className={`space-y-3 ${className}`}>
      <a href={`https://t.me/${ADMIN_TELEGRAM}`} target="_blank" rel="noreferrer" className={rowClass}>
        <span className={iconWrapClass}>
          <Send className="h-4 w-4" />
        </span>
        <span>
          <span className={`block ${labelClass}`}>Admin (Telegram)</span>
          <span className={valueClass}>@{ADMIN_TELEGRAM}</span>
        </span>
      </a>

      <a href={`https://t.me/${BOT_TELEGRAM}`} target="_blank" rel="noreferrer" className={rowClass}>
        <span className={iconWrapClass}>
          <Send className="h-4 w-4" />
        </span>
        <span>
          <span className={`block ${labelClass}`}>Telegram bot</span>
          <span className={valueClass}>@{BOT_TELEGRAM}</span>
        </span>
      </a>

      <div className={rowClass}>
        <span className={iconWrapClass}>
          <Headset className="h-4 w-4" />
        </span>
        <span>
          <span className={`block ${labelClass}`}>Call-markaz</span>
          <span className="flex flex-wrap gap-x-3">
            {CALL_CENTER_NUMBERS.map((num) => (
              <a key={num} href={`tel:${num}`} className={`${valueClass} hover:underline`}>
                <Phone className="mr-1 inline h-3 w-3 -translate-y-px" />
                {num}
              </a>
            ))}
          </span>
        </span>
      </div>
    </div>
  )
}
