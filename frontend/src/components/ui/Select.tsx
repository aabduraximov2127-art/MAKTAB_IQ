import { type SelectHTMLAttributes, forwardRef } from "react"
import { ChevronDown } from "lucide-react"
import { cn } from "../../lib/cn"

export const Select = forwardRef<HTMLSelectElement, SelectHTMLAttributes<HTMLSelectElement>>(
  ({ className, children, ...props }, ref) => {
    return (
      <div className="relative">
        <select
          ref={ref}
          className={cn(
            "h-11 w-full appearance-none rounded-xl border border-ink-200 bg-white px-3.5 pr-9 text-sm text-ink-900",
            "transition-colors focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/40",
            "dark:border-ink-700 dark:bg-ink-900 dark:text-white",
            className
          )}
          {...props}
        >
          {children}
        </select>
        <ChevronDown className="pointer-events-none absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-ink-400" />
      </div>
    )
  }
)
Select.displayName = "Select"
