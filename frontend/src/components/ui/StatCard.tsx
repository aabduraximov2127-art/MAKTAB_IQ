import type { LucideIcon } from "lucide-react"
import { motion } from "framer-motion"
import { ArrowDownRight, ArrowUpRight } from "lucide-react"
import { cn } from "../../lib/cn"

interface StatCardProps {
  label: string
  value: string | number
  icon: LucideIcon
  tone?: "brand" | "accent" | "emerald" | "sky" | "rose"
  trend?: { value: string; positive: boolean }
  delay?: number
}

const toneClasses = {
  brand: "from-brand-500 to-brand-600 text-brand-600 bg-brand-50 dark:bg-brand-500/10",
  accent: "from-accent-500 to-accent-600 text-accent-600 bg-accent-50 dark:bg-accent-500/10",
  emerald: "from-emerald-500 to-emerald-600 text-emerald-600 bg-emerald-50 dark:bg-emerald-500/10",
  sky: "from-sky-500 to-sky-600 text-sky-600 bg-sky-50 dark:bg-sky-500/10",
  rose: "from-rose-500 to-rose-600 text-rose-600 bg-rose-50 dark:bg-rose-500/10",
}

export function StatCard({ label, value, icon: Icon, tone = "brand", trend, delay = 0 }: StatCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 14 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, delay, ease: [0.16, 1, 0.3, 1] }}
      className="group relative overflow-hidden rounded-2xl border border-ink-100 bg-white p-5 shadow-soft transition-shadow hover:shadow-soft-lg dark:border-ink-800 dark:bg-ink-900"
    >
      <div
        className={cn(
          "absolute -right-6 -top-6 h-24 w-24 rounded-full bg-gradient-to-br opacity-10 blur-xl transition-opacity group-hover:opacity-20",
          toneClasses[tone]
        )}
      />
      <div className="relative flex items-start justify-between">
        <div>
          <p className="text-sm font-medium text-ink-500 dark:text-ink-400">{label}</p>
          <p className="mt-2 font-display text-2xl font-bold text-ink-900 dark:text-white">{value}</p>
          {trend && (
            <span
              className={cn(
                "mt-2 inline-flex items-center gap-1 text-xs font-semibold",
                trend.positive ? "text-emerald-600 dark:text-emerald-400" : "text-rose-600 dark:text-rose-400"
              )}
            >
              {trend.positive ? <ArrowUpRight className="h-3.5 w-3.5" /> : <ArrowDownRight className="h-3.5 w-3.5" />}
              {trend.value}
            </span>
          )}
        </div>
        <div className={cn("flex h-11 w-11 shrink-0 items-center justify-center rounded-xl", toneClasses[tone])}>
          <Icon className="h-5 w-5" />
        </div>
      </div>
    </motion.div>
  )
}
