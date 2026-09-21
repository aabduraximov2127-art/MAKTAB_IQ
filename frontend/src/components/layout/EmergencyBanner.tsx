import { useEffect, useState } from "react"
import { AnimatePresence, motion } from "framer-motion"
import { AlertTriangle, X } from "lucide-react"
import { api } from "../../lib/api"

interface Emergency {
  id: number
  title: string
  content: string
  created_at: string
}

export function EmergencyBanner() {
  const [emergency, setEmergency] = useState<Emergency | null>(null)
  const [dismissed, setDismissed] = useState<number | null>(null)

  useEffect(() => {
    api
      .get("/notifications/emergency-announcements/?page_size=1")
      .then((res) => {
        const latest = res.data.results?.[0] as Emergency | undefined
        if (!latest) return
        const ageHours = (Date.now() - new Date(latest.created_at).getTime()) / 36e5
        if (ageHours < 48) setEmergency(latest)
      })
      .catch(() => {})
  }, [])

  const visible = emergency && emergency.id !== dismissed

  return (
    <AnimatePresence>
      {visible && (
        <motion.div
          initial={{ height: 0, opacity: 0 }}
          animate={{ height: "auto", opacity: 1 }}
          exit={{ height: 0, opacity: 0 }}
          className="overflow-hidden"
        >
          <div className="flex items-center gap-3 bg-gradient-to-r from-rose-600 to-orange-500 px-4 py-2.5 text-white sm:px-6">
            <AlertTriangle className="h-4 w-4 shrink-0 animate-pulse" />
            <p className="min-w-0 flex-1 truncate text-sm font-medium">
              <span className="font-bold">{emergency!.title}</span> — {emergency!.content}
            </p>
            <button onClick={() => setDismissed(emergency!.id)} className="shrink-0 rounded-lg p-1 hover:bg-white/20">
              <X className="h-4 w-4" />
            </button>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}
