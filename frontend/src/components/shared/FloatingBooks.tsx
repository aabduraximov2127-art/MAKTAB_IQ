import { motion } from "framer-motion"

interface FloatingItem {
  emoji: string
  top: string
  left: string
  size: number
  duration: number
  delay: number
  drift: number
}

const ITEMS: FloatingItem[] = [
  { emoji: "📚", top: "8%", left: "12%", size: 34, duration: 7, delay: 0, drift: 14 },
  { emoji: "📖", top: "22%", left: "78%", size: 28, duration: 8.5, delay: 0.6, drift: 10 },
  { emoji: "🎓", top: "62%", left: "85%", size: 36, duration: 6.5, delay: 1.2, drift: 16 },
  { emoji: "✏️", top: "48%", left: "6%", size: 24, duration: 6, delay: 0.3, drift: 12 },
  { emoji: "📝", top: "78%", left: "22%", size: 26, duration: 9, delay: 1.8, drift: 10 },
  { emoji: "🧮", top: "14%", left: "48%", size: 26, duration: 7.5, delay: 2.2, drift: 14 },
  { emoji: "📐", top: "86%", left: "64%", size: 24, duration: 8, delay: 0.9, drift: 12 },
  { emoji: "🔬", top: "35%", left: "92%", size: 22, duration: 7, delay: 2.6, drift: 10 },
]

/** Slowly drifting school-themed emoji, purely decorative (pointer-events-none). */
export function FloatingBooks({ className = "" }: { className?: string }) {
  return (
    <div className={`pointer-events-none absolute inset-0 overflow-hidden ${className}`} aria-hidden="true">
      {ITEMS.map((item, i) => (
        <motion.span
          key={i}
          className="absolute select-none opacity-[0.14]"
          style={{ top: item.top, left: item.left, fontSize: item.size }}
          animate={{
            y: [0, -item.drift, 0, item.drift * 0.6, 0],
            x: [0, item.drift * 0.5, 0, -item.drift * 0.5, 0],
            rotate: [0, 8, 0, -8, 0],
          }}
          transition={{
            duration: item.duration,
            delay: item.delay,
            repeat: Infinity,
            ease: "easeInOut",
          }}
        >
          {item.emoji}
        </motion.span>
      ))}
    </div>
  )
}
