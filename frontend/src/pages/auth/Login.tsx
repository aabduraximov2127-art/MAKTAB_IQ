import { type FormEvent, useState } from "react"
import { useNavigate } from "react-router-dom"
import { motion } from "framer-motion"
import { Eye, EyeOff, Lock, User } from "lucide-react"
import toast from "react-hot-toast"
import { api, getErrorMessage } from "../../lib/api"
import { useAuthStore } from "../../store/auth"
import { Button } from "../../components/ui/Button"
import { Input } from "../../components/ui/Input"
import { ContactInfo } from "../../components/shared/ContactInfo"
import { Logo } from "../../components/shared/Logo"
import { ParticleConstellation } from "../../components/shared/ParticleConstellation"

export default function LoginPage() {
  const navigate = useNavigate()
  const setTokens = useAuthStore((s) => s.setTokens)
  const setUser = useAuthStore((s) => s.setUser)

  const [username, setUsername] = useState("")
  const [password, setPassword] = useState("")
  const [showPassword, setShowPassword] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setLoading(true)
    setError(null)
    try {
      const { data } = await api.post("/auth/login/", { username, password })
      setTokens(data.access, data.refresh)
      const me = await api.get("/users/me/", { headers: { Authorization: `Bearer ${data.access}` } })
      setUser(me.data)
      toast.success(`Xush kelibsiz, ${me.data.first_name || me.data.username}!`)
      navigate("/", { replace: true })
    } catch (err) {
      setError(getErrorMessage(err, "Login yoki parol xato"))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="relative min-h-screen overflow-x-hidden bg-ink-950 text-white">
      {/* Particle brain, floating on the void */}
      <div className="pointer-events-none absolute inset-y-0 right-0 w-full opacity-40 lg:w-1/2 lg:opacity-100">
        <ParticleConstellation />
      </div>

      <div className="relative mx-auto flex min-h-screen w-full max-w-[1280px] flex-col px-6 py-8 sm:px-10">
        <header className="flex items-center justify-between">
          <Logo />
          <span className="eyebrow hidden text-ink-400 sm:block">Maktab boshqaruv platformasi</span>
        </header>

        <main className="flex flex-1 items-center py-16">
          <div className="w-full max-w-[520px]">
            <motion.p
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5 }}
              className="eyebrow mb-6 text-accent-400"
            >
              Tizimga kirish
            </motion.p>
            <motion.h1
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.08 }}
              className="font-display text-[56px] leading-[1.05] tracking-[-0.04em] sm:text-[78px]"
            >
              Bilim, bir joyda.
            </motion.h1>
            <motion.p
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.16 }}
              className="copy-light mt-6 max-w-[440px] text-lg text-white"
            >
              Davomat, baholar, vazifalar va muloqot — o'quvchi, o'qituvchi va ota-onalar uchun yagona tizim.
            </motion.p>

            <motion.form
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.24 }}
              onSubmit={handleSubmit}
              className="mt-10 max-w-[380px] space-y-3"
            >
              <Input
                icon={<User className="h-4 w-4" />}
                placeholder="Foydalanuvchi nomi"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                autoFocus
                required
              />
              <div className="relative">
                <Input
                  icon={<Lock className="h-4 w-4" />}
                  type={showPassword ? "text" : "password"}
                  placeholder="Parol"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  className="pr-11"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword((v) => !v)}
                  className="absolute right-4 top-1/2 -translate-y-1/2 text-ink-400 hover:text-white"
                >
                  {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>

              {error && <p className="px-1 text-sm text-rose-400">{error}</p>}

              <Button type="submit" size="lg" className="mt-2" loading={loading}>
                Kirish
              </Button>
            </motion.form>
          </div>
        </main>

        <footer className="flex flex-wrap items-end justify-between gap-6 border-t border-ink-800 pt-6">
          <div>
            <p className="eyebrow mb-3 text-ink-400">Biz bilan bog'laning</p>
            <ContactInfo variant="dark" />
          </div>
          <p className="text-xs text-ink-500">© {new Date().getFullYear()} MaktabIQ</p>
        </footer>
      </div>
    </div>
  )
}
