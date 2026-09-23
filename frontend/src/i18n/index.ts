import translations from "./translations.json"

export type Lang = "uz" | "ru" | "en"

export const LANGS: { code: Lang; label: string; short: string }[] = [
  { code: "uz", label: "O'zbekcha", short: "UZ" },
  { code: "ru", label: "Русский", short: "RU" },
  { code: "en", label: "English", short: "EN" },
]

const STORAGE_KEY = "maktabiq-lang"

const LOCALE_TAGS: Record<Lang, string> = { uz: "uz-UZ", ru: "ru-RU", en: "en-GB" }

function readLang(): Lang {
  try {
    const v = localStorage.getItem(STORAGE_KEY)
    if (v === "uz" || v === "ru" || v === "en") return v
  } catch {
    /* storage unavailable */
  }
  return "uz"
}

let current: Lang = readLang()
if (typeof document !== "undefined") document.documentElement.lang = current

const dict = translations as Record<string, { ru: string; en: string }>

export function getLang(): Lang {
  return current
}

/** BCP-47 tag for Intl / toLocaleDateString in the active language. */
export function localeTag(): string {
  return LOCALE_TAGS[current]
}

/**
 * Translate an Uzbek source string. Unknown keys fall back to the Uzbek text, so untranslated
 * strings never break the UI. `{name}` placeholders are filled from `params`.
 * The language is fixed for the lifetime of the page (switching reloads it), so calling `t`
 * at module level is safe.
 */
export function t(key: string, params?: Record<string, string | number>): string {
  let text = current === "uz" ? key : (dict[key]?.[current] ?? key)
  if (params) {
    for (const [k, v] of Object.entries(params)) text = text.split(`{${k}}`).join(String(v))
  }
  return text
}

/** Persist the language and reload so every string (including module-level ones) is re-evaluated. */
export function setLang(lang: Lang) {
  if (lang === current) return
  try {
    localStorage.setItem(STORAGE_KEY, lang)
  } catch {
    /* ignore */
  }
  window.location.reload()
}
