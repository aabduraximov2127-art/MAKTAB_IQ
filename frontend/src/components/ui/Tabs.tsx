import { motion } from "framer-motion"
import { cn } from "../../lib/cn"

interface TabsProps {
  tabs: { key: string; label: string; count?: number }[]
  active: string
  onChange: (key: string) => void
}

export function Tabs({ tabs, active, onChange }: TabsProps) {
  return (
    <div className="flex items-center gap-1 rounded-xl bg-ink-100 p-1 dark:bg-ink-800/70">
      {tabs.map((tab) => (
        <button
          key={tab.key}
          onClick={() => onChange(tab.key)}
          className={cn(
            "relative flex items-center gap-1.5 rounded-lg px-3.5 py-1.5 text-sm font-medium transition-colors",
            active === tab.key ? "text-ink-900 dark:text-white" : "text-ink-500 hover:text-ink-700 dark:text-ink-400"
          )}
        >
          {active === tab.key && (
            <motion.span
              layoutId="tab-pill"
              className="absolute inset-0 rounded-lg bg-white shadow-soft dark:bg-ink-700"
              transition={{ type: "spring", duration: 0.4, bounce: 0.2 }}
            />
          )}
          <span className="relative">{tab.label}</span>
          {tab.count !== undefined && (
            <span className="relative rounded-full bg-ink-200 px-1.5 text-xs dark:bg-ink-600">{tab.count}</span>
          )}
        </button>
      ))}
    </div>
  )
}
