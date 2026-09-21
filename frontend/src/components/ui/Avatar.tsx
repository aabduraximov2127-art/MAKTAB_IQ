import { initials } from "../../lib/format"
import { cn } from "../../lib/cn"

const PALETTE = [
  "bg-brand-500",
  "bg-accent-500",
  "bg-emerald-500",
  "bg-sky-500",
  "bg-rose-500",
  "bg-violet-500",
]

function colorFor(seed: string) {
  let hash = 0
  for (let i = 0; i < seed.length; i++) hash = seed.charCodeAt(i) + ((hash << 5) - hash)
  return PALETTE[Math.abs(hash) % PALETTE.length]
}

interface AvatarProps {
  name?: string | null
  src?: string | null
  size?: "sm" | "md" | "lg"
  className?: string
}

const sizeClasses = {
  sm: "h-8 w-8 text-xs",
  md: "h-10 w-10 text-sm",
  lg: "h-14 w-14 text-lg",
}

export function Avatar({ name, src, size = "md", className }: AvatarProps) {
  if (src) {
    return (
      <img
        src={src}
        alt={name ?? "avatar"}
        className={cn("rounded-full object-cover ring-2 ring-white dark:ring-ink-900", sizeClasses[size], className)}
      />
    )
  }
  const label = name ? initials({ first_name: name.split(" ")[0], last_name: name.split(" ")[1] }) : "?"
  return (
    <div
      className={cn(
        "flex items-center justify-center rounded-full font-semibold text-white ring-2 ring-white dark:ring-ink-900",
        colorFor(name ?? "?"),
        sizeClasses[size],
        className
      )}
    >
      {label}
    </div>
  )
}
