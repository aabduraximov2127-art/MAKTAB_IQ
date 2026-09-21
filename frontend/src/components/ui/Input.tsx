import { type InputHTMLAttributes, type LabelHTMLAttributes, type ReactNode, forwardRef } from "react"
import { cn } from "../../lib/cn"

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  icon?: ReactNode
  error?: string
}

export const Input = forwardRef<HTMLInputElement, InputProps>(({ className, icon, error, ...props }, ref) => {
  return (
    <div className="relative">
      {icon && (
        <span className="pointer-events-none absolute left-3.5 top-1/2 -translate-y-1/2 text-ink-400">{icon}</span>
      )}
      <input
        ref={ref}
        className={cn(
          "h-12 w-full rounded-full border bg-white px-5 text-sm text-ink-900 placeholder:text-ink-400",
          "transition-colors focus:outline-none focus:ring-2 focus:ring-brand-500/40",
          "dark:bg-ink-950 dark:text-white dark:placeholder:text-ink-500",
          error ? "border-rose-400 focus:ring-rose-400/40" : "border-ink-200 focus:border-brand-500 dark:border-ink-700",
          icon && "pl-11",
          className
        )}
        {...props}
      />
      {error && <p className="mt-1.5 text-xs text-rose-500">{error}</p>}
    </div>
  )
})
Input.displayName = "Input"

interface FieldProps extends Omit<LabelHTMLAttributes<HTMLLabelElement>, "className"> {
  label: string
  htmlFor?: string
  children: ReactNode
  className?: string
}

export function Field({ label, htmlFor, children, className, ...props }: FieldProps) {
  return (
    <div className={cn("space-y-1.5", className)}>
      <label htmlFor={htmlFor} className="text-sm font-medium text-ink-700 dark:text-ink-300" {...props}>
        {label}
      </label>
      {children}
    </div>
  )
}
