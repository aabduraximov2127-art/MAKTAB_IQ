import { type InputHTMLAttributes, type KeyboardEvent, useLayoutEffect, useRef, useState } from "react"
import { motion } from "framer-motion"
import { cn } from "../../lib/cn"

export const PHONE_PREFIX = "+998"
const PREFIX_FULL = `${PHONE_PREFIX} ` // what the user sees in front of the number
const MAX_DIGITS = 9 // national digits after +998

const ERASE_STEP = 0.09 // seconds between characters
const RETYPE_START = 0.55
const ANIMATION_MS = 1100

/** "90 123 45 67" grouping for the 9 national digits. */
function group(digits: string) {
  return [digits.slice(0, 2), digits.slice(2, 5), digits.slice(5, 7), digits.slice(7, 9)].filter(Boolean).join(" ")
}

/** National digits (without 998) from any stored/typed phone value. */
export function phoneToDigits(value: string | undefined | null): string {
  let d = (value ?? "").replace(/\D/g, "")
  if (d.startsWith("998")) d = d.slice(3)
  return d.slice(0, MAX_DIGITS)
}

/** Value sent to the API: "+998901234567", or "" when nothing was typed. */
export function digitsToPhone(digits: string): string {
  return digits ? PHONE_PREFIX + digits : ""
}

/** True when the field holds a full 9-digit number (or is empty). */
export function isPhoneComplete(value: string): boolean {
  const d = phoneToDigits(value)
  return d.length === 0 || d.length === MAX_DIGITS
}

interface PhoneInputProps extends Omit<InputHTMLAttributes<HTMLInputElement>, "value" | "onChange" | "type"> {
  /** Full phone ("+998901234567"), just the digits, or "". */
  value: string
  /** Called with the full phone ("+998901234567"), or "" while only the prefix is present. */
  onChange: (phone: string) => void
  error?: string
}

/**
 * Phone field with a fixed "+998" prefix. The prefix cannot be deleted: when someone tries to
 * erase it (Backspace/Delete on it, select-all + delete, cut) the prefix visibly erases itself
 * character by character and then types itself back in.
 */
export function PhoneInput({ value, onChange, error, className, ...props }: PhoneInputProps) {
  const digits = phoneToDigits(value)
  const display = PREFIX_FULL + group(digits)
  const inputRef = useRef<HTMLInputElement>(null)
  const caretDigits = useRef<number | null>(null) // digits that should sit before the caret after the next render
  const [pulse, setPulse] = useState(0)
  const [animating, setAnimating] = useState(false)
  const timer = useRef<ReturnType<typeof setTimeout> | undefined>(undefined)

  function bounce() {
    setPulse((n) => n + 1)
    setAnimating(true)
    clearTimeout(timer.current)
    timer.current = setTimeout(() => setAnimating(false), ANIMATION_MS + 100)
  }

  // Re-place the caret after reformatting ("901234567" -> "90 123 45 67").
  useLayoutEffect(() => {
    const el = inputRef.current
    const wanted = caretDigits.current
    caretDigits.current = null
    if (!el || wanted === null || document.activeElement !== el) return
    let pos = PREFIX_FULL.length
    let seen = 0
    while (pos < display.length && seen < wanted) {
      if (/\d/.test(display[pos]!)) seen++
      pos++
    }
    el.setSelectionRange(pos, pos)
  })

  function handleChange(el: HTMLInputElement) {
    const raw = el.value
    const caret = el.selectionStart ?? raw.length
    const keepsPrefix = raw.startsWith(PHONE_PREFIX)
    const rest = keepsPrefix ? raw.slice(PHONE_PREFIX.length) : raw
    let d = rest.replace(/\D/g, "")
    if (!keepsPrefix && d.startsWith("998")) d = d.slice(3) // pasted "998901234567" over a selection
    d = d.slice(0, MAX_DIGITS)

    if (!keepsPrefix && d.length <= digits.length) bounce() // the prefix got (partly) erased
    if (keepsPrefix) {
      caretDigits.current = rest.slice(0, Math.max(0, caret - PHONE_PREFIX.length)).replace(/\D/g, "").length
    } else {
      caretDigits.current = d.length
    }
    onChange(digitsToPhone(d))
  }

  function handleKeyDown(e: KeyboardEvent<HTMLInputElement>) {
    const el = e.currentTarget
    const start = el.selectionStart ?? 0
    const end = el.selectionEnd ?? 0
    if (start !== end) return // selections are handled in onChange
    const backspaceOnPrefix = e.key === "Backspace" && start <= PREFIX_FULL.length
    const deleteOnPrefix = e.key === "Delete" && start < PREFIX_FULL.length
    if (backspaceOnPrefix || deleteOnPrefix) {
      e.preventDefault()
      bounce()
    }
  }

  function keepCaretAfterPrefix(el: HTMLInputElement) {
    requestAnimationFrame(() => {
      const s = el.selectionStart ?? 0
      const e = el.selectionEnd ?? 0
      if (s === e && s < PREFIX_FULL.length) el.setSelectionRange(PREFIX_FULL.length, PREFIX_FULL.length)
    })
  }

  return (
    <div className="relative">
      <input
        ref={inputRef}
        type="tel"
        inputMode="tel"
        autoComplete="tel"
        value={display}
        onChange={(e) => handleChange(e.currentTarget)}
        onKeyDown={handleKeyDown}
        onCut={(e) => {
          if ((e.currentTarget.selectionStart ?? 0) < PREFIX_FULL.length) {
            e.preventDefault()
            bounce()
          }
        }}
        onFocus={(e) => keepCaretAfterPrefix(e.currentTarget)}
        onClick={(e) => keepCaretAfterPrefix(e.currentTarget)}
        maxLength={PREFIX_FULL.length + 12}
        className={cn(
          "h-12 w-full rounded-full border bg-white px-5 text-sm tabular-nums text-ink-900",
          "transition-colors focus:outline-none focus:ring-2 focus:ring-brand-500/40",
          "dark:bg-ink-950 dark:text-white",
          error ? "border-rose-400 focus:ring-rose-400/40" : "border-ink-200 focus:border-brand-500 dark:border-ink-700",
          className
        )}
        {...props}
      />

      {/* Masks the real prefix while it "erases" character by character and types itself back. */}
      {animating && (
        <span
          key={pulse}
          aria-hidden="true"
          className="pointer-events-none absolute left-[1.15rem] top-1/2 flex -translate-y-1/2 bg-white px-[3px] text-sm tabular-nums text-ink-900 dark:bg-ink-950 dark:text-white"
        >
          {PHONE_PREFIX.split("").map((ch, i) => {
            const eraseAt = (PHONE_PREFIX.length - 1 - i) * ERASE_STEP // last char goes first
            const typeAt = RETYPE_START + i * ERASE_STEP
            const total = ANIMATION_MS / 1000
            const t = (s: number) => Math.min(s / total, 0.999)
            return (
              <motion.span
                key={i}
                initial={{ opacity: 1 }}
                animate={{ opacity: [1, 1, 0, 0, 1, 1] }}
                transition={{
                  duration: total,
                  times: [0, t(eraseAt) + 0.0001, t(eraseAt + 0.04), t(typeAt), t(typeAt + 0.04), 1],
                  ease: "linear",
                }}
              >
                {ch}
              </motion.span>
            )
          })}
        </span>
      )}
      {error && <p className="mt-1.5 text-xs text-rose-500">{error}</p>}
    </div>
  )
}
