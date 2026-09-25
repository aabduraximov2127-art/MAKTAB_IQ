import { type KeyboardEvent, useEffect, useId, useMemo, useRef, useState } from "react"
import { Search, X } from "lucide-react"
import { cn } from "../../lib/cn"
import { normalise } from "../../lib/search"
import { t } from "../../i18n"

export interface SearchOption {
  value: string
  label: string
  /** Secondary text shown under the label and matched by the search too (e.g. a teacher's subjects). */
  hint?: string
}

interface SearchSelectProps {
  options: SearchOption[]
  /** Selected option value, "" when nothing is chosen. */
  value: string
  onChange: (value: string) => void
  placeholder?: string
  disabled?: boolean
  className?: string
}

/** 0 = starts with the query, 1 = a word starts with it, 2 = contains it, -1 = no match. */
function rank(option: SearchOption, query: string) {
  const label = normalise(option.label)
  if (label.startsWith(query)) return 0
  if (label.split(/[\s\-–—/]+/).some((word) => word.startsWith(query))) return 1
  if (label.includes(query)) return 2
  if (option.hint && normalise(option.hint).includes(query)) return 3
  return -1
}

/**
 * A select you can type into: "ma" lists the matching entries (Matematika first), arrow keys and
 * Enter pick one, the × clears it. Use it instead of a plain <select> when the list is long.
 */
export function SearchSelect({ options, value, onChange, placeholder, disabled, className }: SearchSelectProps) {
  const listId = useId()
  const rootRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)
  const [open, setOpen] = useState(false)
  const [query, setQuery] = useState("")
  const [active, setActive] = useState(0)

  const selected = options.find((o) => o.value === value)

  const matches = useMemo(() => {
    const q = normalise(query.trim())
    if (!q) return options
    return options
      .map((option) => ({ option, score: rank(option, q) }))
      .filter((m) => m.score >= 0)
      .sort((a, b) => a.score - b.score || a.option.label.localeCompare(b.option.label))
      .map((m) => m.option)
  }, [options, query])

  useEffect(() => {
    if (!open) return
    function onDown(e: MouseEvent) {
      if (rootRef.current && !rootRef.current.contains(e.target as Node)) setOpen(false)
    }
    document.addEventListener("mousedown", onDown)
    return () => document.removeEventListener("mousedown", onDown)
  }, [open])

  // keep the highlighted row in view while arrowing through a long list
  useEffect(() => {
    if (!open) return
    document.getElementById(`${listId}-${active}`)?.scrollIntoView({ block: "nearest" })
  }, [active, open, listId])

  function pick(option: SearchOption) {
    onChange(option.value)
    setOpen(false)
    setQuery("")
  }

  function onKeyDown(e: KeyboardEvent<HTMLInputElement>) {
    if (e.key === "ArrowDown") {
      e.preventDefault()
      setOpen(true)
      setActive((i) => Math.min(i + 1, Math.max(matches.length - 1, 0)))
    } else if (e.key === "ArrowUp") {
      e.preventDefault()
      setActive((i) => Math.max(i - 1, 0))
    } else if (e.key === "Enter") {
      if (open && matches[active]) {
        e.preventDefault() // do not submit the surrounding form
        pick(matches[active])
      }
    } else if (e.key === "Escape") {
      if (open) {
        e.stopPropagation() // close the list, not the dialog around it
        setOpen(false)
        setQuery("")
      }
    } else if (e.key === "Tab") {
      setOpen(false)
    }
  }

  const q = query.trim()
  const shown = open ? query : selected?.label ?? ""

  return (
    <div ref={rootRef} className={cn("relative", className)}>
      <Search className="pointer-events-none absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-ink-400" />
      <input
        ref={inputRef}
        role="combobox"
        aria-expanded={open}
        aria-controls={listId}
        aria-autocomplete="list"
        autoComplete="off"
        disabled={disabled}
        value={shown}
        placeholder={open && selected ? selected.label : placeholder}
        onFocus={() => {
          setOpen(true)
          setQuery("")
          setActive(0)
        }}
        onChange={(e) => {
          setQuery(e.target.value)
          setOpen(true)
          setActive(0)
        }}
        onKeyDown={onKeyDown}
        className={cn(
          "h-11 w-full rounded-xl border border-ink-200 bg-white pl-10 pr-9 text-sm text-ink-900 placeholder:text-ink-400",
          "transition-colors focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/40",
          "disabled:cursor-not-allowed disabled:opacity-60 dark:border-ink-700 dark:bg-ink-900 dark:text-white dark:placeholder:text-ink-500"
        )}
      />
      {value && !disabled && (
        <button
          type="button"
          aria-label={t("Tozalash")}
          onMouseDown={(e) => e.preventDefault()}
          onClick={() => {
            onChange("")
            setQuery("")
            inputRef.current?.focus()
          }}
          className="absolute right-2.5 top-1/2 flex h-6 w-6 -translate-y-1/2 items-center justify-center rounded-full text-ink-400 hover:bg-ink-100 hover:text-ink-700 dark:hover:bg-ink-800"
        >
          <X className="h-3.5 w-3.5" />
        </button>
      )}

      {open && (
        <ul
          id={listId}
          role="listbox"
          className="absolute z-40 mt-1.5 max-h-60 w-full overflow-y-auto rounded-xl border border-ink-100 bg-white p-1 shadow-soft-lg dark:border-ink-700 dark:bg-ink-900"
        >
          {matches.length === 0 ? (
            <li className="px-3 py-3 text-sm text-ink-400">{t("Hech narsa topilmadi")}</li>
          ) : (
            matches.map((option, index) => (
              <li
                key={option.value}
                id={`${listId}-${index}`}
                role="option"
                aria-selected={option.value === value}
                onMouseDown={(e) => e.preventDefault()} // keep the input focused
                onClick={() => pick(option)}
                onMouseEnter={() => setActive(index)}
                className={cn(
                  "cursor-pointer rounded-lg px-3 py-2 text-sm",
                  index === active ? "bg-brand-50 dark:bg-brand-500/15" : "",
                  option.value === value ? "font-semibold text-brand-700 dark:text-brand-300" : "text-ink-800 dark:text-ink-100"
                )}
              >
                <Highlight text={option.label} query={q} />
                {option.hint && <span className="block truncate text-xs font-normal text-ink-400">{option.hint}</span>}
              </li>
            ))
          )}
        </ul>
      )}
    </div>
  )
}

/** Bolds the part of ``text`` the query matched. */
function Highlight({ text, query }: { text: string; query: string }) {
  if (!query) return <>{text}</>
  const at = normalise(text).indexOf(normalise(query))
  // normalise() may drop apostrophes, so only highlight when both strings line up character for character
  if (at < 0 || normalise(text).length !== text.length) return <>{text}</>
  return (
    <>
      {text.slice(0, at)}
      <b className="font-bold text-brand-700 dark:text-brand-300">{text.slice(at, at + query.length)}</b>
      {text.slice(at + query.length)}
    </>
  )
}
