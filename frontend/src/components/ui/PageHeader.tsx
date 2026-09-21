import type { ReactNode } from "react"
import { motion } from "framer-motion"

interface PageHeaderProps {
  title: string
  description?: string
  actions?: ReactNode
}

export function PageHeader({ title, description, actions }: PageHeaderProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: -8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="mb-10 flex flex-wrap items-center justify-between gap-4"
    >
      <div>
        <h1 className="font-display text-4xl leading-[1.1] tracking-[-0.04em] text-ink-900 dark:text-white sm:text-5xl">{title}</h1>
        {description && <p className="mt-2 text-base font-light text-ink-500 dark:text-ink-400">{description}</p>}
      </div>
      {actions && <div className="flex items-center gap-2">{actions}</div>}
    </motion.div>
  )
}
