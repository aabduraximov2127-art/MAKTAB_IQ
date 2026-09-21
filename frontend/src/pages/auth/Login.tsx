import { type FormEvent, useState } from "react"
import { useNavigate } from "react-router-dom"
import { motion } from "framer-motion"
import {
  BarChart3,
  Bot,
  Eye,
  EyeOff,
  GraduationCap,
  Heart,
  Lock,
  MessagesSquare,
  ShieldCheck,
  User,
} from "lucide-react"
import toast from "react-hot-toast"
import { api, getErrorMessage } from "../../lib/api"
import { useAuthStore } from "../../store/auth"
import { Button } from "../../components/ui/Button"
import { Input } from "../../components/ui/Input"
import { ContactInfo } from "../../components/shared/ContactInfo"
import { FloatingBooks } from "../../components/shared/FloatingBooks"

const FEATURES = [
  { icon: BarChart3, title: "Real vaqtda statistika", desc: "Davomat, baho va progressni bir joydan kuzating" },
  { icon: MessagesSquare, title: "Jonli muloqot", desc: "O'qituvchi, o'quvchi va ota-onalar bir tizimda" },
  { icon: Bot, title: "AI Study Assistant", desc: "O'quvchilarga shaxsiy yordamchi yordam beradi" },
]

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
    <div className="flex h-screen overflow-hidden bg-ink-50 dark:bg-ink-950">
      {/* Left — branding (scrolls independently so the form on the right always stays put) */}
      <div className="relative hidden h-full w-1/2 overflow-y-auto overflow-x-hidden bg-ink-950 lg:block">
        <div className="bg-mesh absolute inset-0" />
        <div className="absolute inset-0 bg-gradient-to-b from-transparent via-ink-950/40 to-ink-950" />
        <FloatingBooks />

        <div className="relative flex min-h-full flex-col gap-10 p-12">
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="flex items-center gap-2.5"
          >
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-brand-500 to-brand-700 shadow-soft">
              <GraduationCap className="h-6 w-6 text-white" />
            </div>
            <span className="font-display text-xl font-bold text-white">MaktabIQ</span>
          </motion.div>

          <div className="space-y-8">
            <motion.h1
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.1 }}
              className="font-display text-4xl font-bold leading-tight text-white"
            >
              Maktabingizni <br /> yagona raqamli <br />
              <span className="bg-gradient-to-r from-brand-300 to-accent-300 bg-clip-text text-transparent">
                platformaga
              </span>{" "}
              aylantiring
            </motion.h1>

            <div className="space-y-4">
              {FEATURES.map((f, i) => (
                <motion.div
                  key={f.title}
                  initial={{ opacity: 0, x: -16 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ duration: 0.4, delay: 0.2 + i * 0.1 }}
                  className="flex items-start gap-3 rounded-2xl border border-white/10 bg-white/5 p-4 backdrop-blur-sm"
                >
                  <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-white/10 text-brand-300">
                    <f.icon className="h-4.5 w-4.5" />
                  </div>
                  <div>
                    <p className="text-sm font-semibold text-white">{f.title}</p>
                    <p className="text-xs text-ink-300">{f.desc}</p>
                  </div>
                </motion.div>
              ))}
            </div>
          </div>

          {/* Biz haqimizda */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: "-40px" }}
            transition={{ duration: 0.5 }}
            className="relative overflow-hidden rounded-2xl border border-white/10 bg-white/5 p-6 backdrop-blur-sm"
          >
            <motion.div
              animate={{ rotate: [0, 8, -8, 0], scale: [1, 1.08, 1] }}
              transition={{ duration: 4, repeat: Infinity, ease: "easeInOut" }}
              className="mb-3 flex h-11 w-11 items-center justify-center rounded-xl bg-gradient-to-br from-accent-400 to-accent-600 text-white shadow-soft"
            >
              <Heart className="h-5 w-5" />
            </motion.div>
            <h2 className="font-display text-lg font-bold text-white">Biz haqimizda</h2>
            <p className="mt-2 text-sm leading-relaxed text-ink-300">
              MaktabIQ — zamonaviy maktablar uchun yaratilgan yagona raqamli ta'lim boshqaruv tizimi.
              Maqsadimiz — o'quvchi, o'qituvchi va ota-onalarni bitta qulay platformada birlashtirib,
              o'quv jarayonini shaffof, tezkor va zamonaviy qilish.
            </p>

            <div className="mt-5 border-t border-white/10 pt-5">
              <p className="mb-3 text-xs font-semibold uppercase tracking-wider text-ink-400">Biz bilan bog'laning</p>
              <ContactInfo variant="dark" />
            </div>
          </motion.div>

          <p className="text-xs text-ink-500">© {new Date().getFullYear()} MaktabIQ. Barcha huquqlar himoyalangan.</p>
        </div>
      </div>

      {/* Right — form */}
      <div className="flex h-full w-full flex-col items-center justify-center overflow-y-auto px-6 py-12 lg:w-1/2">
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4 }}
          className="w-full max-w-sm"
        >
          <div className="mb-8 flex items-center gap-2.5 lg:hidden">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-brand-500 to-brand-700">
              <GraduationCap className="h-5 w-5 text-white" />
            </div>
            <span className="font-display text-lg font-bold text-ink-900 dark:text-white">MaktabIQ</span>
          </div>

          <h2 className="font-display text-2xl font-bold text-ink-900 dark:text-white">Xush kelibsiz</h2>
          <p className="mt-1.5 text-sm text-ink-500 dark:text-ink-400">
            Tizimga kirish uchun login va parolingizni kiriting
          </p>

          <form onSubmit={handleSubmit} className="mt-8 space-y-4">
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
                className="absolute right-3.5 top-1/2 -translate-y-1/2 text-ink-400 hover:text-ink-600 dark:hover:text-ink-300"
              >
                {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
              </button>
            </div>

            {error && (
              <motion.p
                initial={{ opacity: 0, y: -4 }}
                animate={{ opacity: 1, y: 0 }}
                className="rounded-lg bg-rose-50 px-3 py-2 text-sm text-rose-600 dark:bg-rose-500/10 dark:text-rose-400"
              >
                {error}
              </motion.p>
            )}

            <Button type="submit" size="lg" className="w-full" loading={loading}>
              Kirish
            </Button>
          </form>

          <div className="mt-8 flex items-center gap-2 rounded-xl bg-ink-100/60 px-3.5 py-3 text-xs text-ink-500 dark:bg-ink-800/50 dark:text-ink-400">
            <ShieldCheck className="h-4 w-4 shrink-0 text-emerald-500" />
            Ma'lumotlaringiz JWT autentifikatsiya bilan himoyalangan
          </div>
        </motion.div>
      </div>
    </div>
  )
}
