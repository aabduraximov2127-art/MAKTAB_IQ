import { cn } from "../../lib/cn"

/** Angular triangular mark (violet fading into teal) + wordmark. */
export function Logo({ className, showWord = true }: { className?: string; showWord?: boolean }) {
  return (
    <span className={cn("inline-flex items-center gap-2.5", className)}>
      <svg width="28" height="28" viewBox="0 0 28 28" fill="none" aria-hidden="true">
        <defs>
          <linearGradient id="logo-fade" x1="4" y1="4" x2="24" y2="26" gradientUnits="userSpaceOnUse">
            <stop stopColor="#8052ff" />
            <stop offset="1" stopColor="#15846e" />
          </linearGradient>
        </defs>
        <path d="M14 2 26 24H2L14 2Z" stroke="url(#logo-fade)" strokeWidth="2.2" strokeLinejoin="round" />
        <path d="M14 11 19.5 21h-11L14 11Z" fill="url(#logo-fade)" />
      </svg>
      {showWord && <span className="font-display text-xl text-white">MaktabIQ</span>}
    </span>
  )
}
