import { Link } from "react-router-dom"
import { Compass } from "lucide-react"
import { Button } from "../components/ui/Button"

export default function NotFoundPage() {
  return (
    <div className="flex flex-col items-center justify-center gap-4 py-24 text-center">
      <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-brand-50 text-brand-500 dark:bg-brand-500/10">
        <Compass className="h-8 w-8" />
      </div>
      <h1 className="font-display text-3xl font-bold text-ink-900 dark:text-white">404</h1>
      <p className="text-ink-500 dark:text-ink-400">Bu sahifa topilmadi.</p>
      <Link to="/">
        <Button>Bosh sahifaga qaytish</Button>
      </Link>
    </div>
  )
}
