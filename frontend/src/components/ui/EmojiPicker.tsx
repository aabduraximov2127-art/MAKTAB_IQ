import { useEffect, useRef, useState } from "react"
import { AnimatePresence, motion } from "framer-motion"
import { Smile } from "lucide-react"
import { cn } from "../../lib/cn"
import { t } from "../../i18n"

const CATEGORIES: { id: string; icon: string; label: string; emojis: string }[] = [
  {
    id: "smileys",
    icon: "😀",
    label: "Yuzlar",
    emojis:
      "😀 😃 😄 😁 😆 😅 😂 🤣 🙂 🙃 😉 😊 😇 🥰 😍 🤩 😘 😗 😚 😋 😛 😜 🤪 😝 🤗 🤭 🤔 🤨 😐 😑 😶 🙄 😏 😒 😞 😔 😟 😕 🙁 😣 😖 😫 😩 🥺 😢 😭 😤 😠 😡 🤬 🤯 😳 🥵 🥶 😱 😨 😰 😥 😓 🤤 😴 🥱 😷 🤒 🤕 🤢 🤮 🤧 😎 🤓 🥳 🤠",
  },
  {
    id: "gestures",
    icon: "👍",
    label: "Qo'l va harakatlar",
    emojis: "👍 👎 👌 ✌️ 🤞 🤟 🤘 🤙 👈 👉 👆 👇 ☝️ ✋ 🤚 🖐️ 🖖 👋 🤝 🙏 👏 🙌 👐 🤲 💪 ✍️ 🤳 👀 🧠 🙋 🤷 🤦 💃 🕺 🏃",
  },
  {
    id: "hearts",
    icon: "❤️",
    label: "Yuraklar va belgilar",
    emojis: "❤️ 🧡 💛 💚 💙 💜 🖤 🤍 🤎 💔 ❣️ 💕 💞 💓 💗 💖 💘 💝 ✨ 🌟 ⭐ 💫 🔥 💯 ✅ ❌ ⚡ 🎉 🎊 🏆 🥇 🥈 🥉 ❓ ❗ 💬 💤",
  },
  {
    id: "school",
    icon: "📚",
    label: "Maktab",
    emojis: "📚 📖 📝 ✏️ 🖊️ 📐 📏 🧮 🔬 🔭 🧪 🧬 💻 🖥️ ⌨️ 📱 🎓 🏫 🎒 📅 ⏰ 🔔 💡 🎨 🎵 🎮 ⚽ 🏀 🏐 🎯 📊 📈 🗂️ 📌 📎",
  },
  {
    id: "nature",
    icon: "🐱",
    label: "Hayvonlar va tabiat",
    emojis: "🐶 🐱 🐭 🐹 🐰 🦊 🐻 🐼 🐨 🐯 🦁 🐮 🐷 🐸 🐵 🐔 🐧 🐦 🦉 🦋 🐝 🐢 🐍 🐙 🐬 🐳 🌸 🌹 🌻 🌲 🌍 ☀️ 🌈 ☁️ ⛄ 🌙",
  },
  {
    id: "food",
    icon: "🍎",
    label: "Ovqat",
    emojis: "🍎 🍌 🍇 🍓 🍉 🍊 🍋 🍒 🥕 🌽 🍕 🍔 🍟 🌭 🍿 🍩 🍪 🎂 🍰 🍫 🍬 🍭 ☕ 🥤 🍵 🥛 🍞 🧀 🍳 🥗",
  },
]

const RECENT_KEY = "maktabiq-recent-emojis"
const RECENT_MAX = 16

function loadRecent(): string[] {
  try {
    const parsed = JSON.parse(localStorage.getItem(RECENT_KEY) ?? "[]")
    return Array.isArray(parsed) ? parsed.filter((e) => typeof e === "string").slice(0, RECENT_MAX) : []
  } catch {
    return []
  }
}

function saveRecent(list: string[]) {
  try {
    localStorage.setItem(RECENT_KEY, JSON.stringify(list))
  } catch {
    /* storage unavailable */
  }
}

interface EmojiPickerProps {
  onPick: (emoji: string) => void
  className?: string
}

/** Emoji button + popover. Stays open while picking several emojis; closes on outside click / Escape. */
export function EmojiPicker({ onPick, className }: EmojiPickerProps) {
  const [open, setOpen] = useState(false)
  const [active, setActive] = useState(CATEGORIES[0]!.id)
  const [recent, setRecent] = useState<string[]>(loadRecent)
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!open) return
    const onDown = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false)
    }
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && setOpen(false)
    document.addEventListener("mousedown", onDown)
    document.addEventListener("keydown", onKey)
    return () => {
      document.removeEventListener("mousedown", onDown)
      document.removeEventListener("keydown", onKey)
    }
  }, [open])

  function pick(emoji: string) {
    onPick(emoji)
    const next = [emoji, ...recent.filter((e) => e !== emoji)].slice(0, RECENT_MAX)
    setRecent(next)
    saveRecent(next)
  }

  const category = CATEGORIES.find((c) => c.id === active) ?? CATEGORIES[0]!

  return (
    <div ref={ref} className={cn("relative", className)}>
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        title={t("Emoji")}
        aria-label={t("Emoji")}
        aria-expanded={open}
        className={cn(
          "flex h-11 w-11 shrink-0 items-center justify-center rounded-full text-ink-500 transition-colors hover:bg-ink-100 hover:text-brand-500 dark:text-ink-400 dark:hover:bg-ink-800",
          open && "bg-ink-100 text-brand-500 dark:bg-ink-800"
        )}
      >
        <Smile className="h-5 w-5" />
      </button>

      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ opacity: 0, y: 8, scale: 0.97 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 8, scale: 0.97 }}
            transition={{ duration: 0.15 }}
            className="absolute bottom-full left-0 z-30 mb-2 w-[19.5rem] overflow-hidden rounded-3xl border border-ink-100 bg-white dark:border-ink-800 dark:bg-ink-900"
          >
            <div className="flex items-center gap-1 border-b border-ink-100 px-2 py-1.5 dark:border-ink-800">
              {CATEGORIES.map((c) => (
                <button
                  key={c.id}
                  type="button"
                  onClick={() => setActive(c.id)}
                  title={t(c.label)}
                  aria-label={t(c.label)}
                  className={cn(
                    "flex h-8 w-8 items-center justify-center rounded-full text-base transition-colors hover:bg-ink-100 dark:hover:bg-ink-800",
                    active === c.id && "bg-brand-500/15"
                  )}
                >
                  {c.icon}
                </button>
              ))}
            </div>

            <div className="max-h-56 overflow-y-auto p-2">
              {recent.length > 0 && (
                <>
                  <p className="eyebrow px-1 pb-1 text-[10px] text-ink-400">{t("Ko'p ishlatilgan")}</p>
                  <EmojiGrid emojis={recent} onPick={pick} />
                  <div className="my-2 h-px bg-ink-100 dark:bg-ink-800" />
                </>
              )}
              <p className="eyebrow px-1 pb-1 text-[10px] text-ink-400">{t(category.label)}</p>
              <EmojiGrid emojis={category.emojis.split(" ")} onPick={pick} />
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

function EmojiGrid({ emojis, onPick }: { emojis: string[]; onPick: (emoji: string) => void }) {
  return (
    <div className="grid grid-cols-8 gap-0.5">
      {emojis.map((emoji) => (
        <button
          key={emoji}
          type="button"
          onClick={() => onPick(emoji)}
          className="flex h-8 w-8 items-center justify-center rounded-lg text-xl transition-transform hover:scale-125 hover:bg-ink-100 dark:hover:bg-ink-800"
        >
          {emoji}
        </button>
      ))}
    </div>
  )
}
