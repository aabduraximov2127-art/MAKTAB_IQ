import { type FormEvent, useEffect, useState } from "react"
import toast from "react-hot-toast"
import { useFetch } from "../../hooks/useFetch"
import { api, getErrorMessage } from "../../lib/api"
import { useAccess } from "../../lib/access"
import { cn } from "../../lib/cn"
import { Button } from "../ui/Button"
import { Field, Input } from "../ui/Input"
import { Modal } from "../ui/Modal"
import { PhoneInput, isPhoneComplete } from "../ui/PhoneInput"
import { Select } from "../ui/Select"
import type { Paginated, School, Subject, TeacherProfile } from "../../types"
import { t } from "../../i18n"

interface TeacherFormModalProps {
  open: boolean
  /** The teacher being edited; ``null`` opens the form for a new one. */
  teacher: TeacherProfile | null
  onClose: () => void
  onDone: () => void
}

const EMPTY = {
  first_name: "",
  last_name: "",
  username: "",
  password: "",
  teacher_id: "",
  phone: "",
  email: "",
  experience_years: "0",
  school: "",
}

/**
 * Add a teacher (this also creates the login) or edit one (name, contact details, experience and
 * subjects — never the login or the password). A school admin's teachers always belong to its own
 * school; only the SuperAdmin picks the school.
 */
export function TeacherFormModal({ open, teacher, onClose, onDone }: TeacherFormModalProps) {
  const { can } = useAccess()
  const chooseSchool = can("manage_schools")
  const editing = !!teacher

  const { data: subjects } = useFetch<Paginated<Subject>>(open ? "/subjects/?page_size=100" : null, [open])
  const { data: schools } = useFetch<Paginated<School>>(open && chooseSchool ? "/schools/?page_size=100" : null, [open])
  const [form, setForm] = useState(EMPTY)
  const [chosen, setChosen] = useState<number[]>([])
  const [loading, setLoading] = useState(false)
  const set = (key: keyof typeof EMPTY, value: string) => setForm((f) => ({ ...f, [key]: value }))

  useEffect(() => {
    if (!open) return
    if (teacher) {
      setForm({
        ...EMPTY,
        first_name: teacher.user.first_name,
        last_name: teacher.user.last_name,
        phone: teacher.user.phone,
        email: teacher.user.email,
        experience_years: String(teacher.experience_years),
      })
      setChosen(teacher.subjects)
    } else {
      setForm(EMPTY)
      setChosen([])
    }
  }, [open, teacher])

  const toggleSubject = (id: number) => setChosen((list) => (list.includes(id) ? list.filter((x) => x !== id) : [...list, id]))

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    if (!isPhoneComplete(form.phone)) return toast.error(t("Telefon raqami to'liq emas"))
    setLoading(true)
    try {
      const common = {
        first_name: form.first_name,
        last_name: form.last_name,
        phone: form.phone,
        email: form.email,
        experience_years: Number(form.experience_years) || 0,
        subjects: chosen,
      }
      if (teacher) {
        await api.patch(`/teachers/${teacher.id}/`, common)
        toast.success(t("O'qituvchi yangilandi"))
      } else {
        await api.post("/teachers/", {
          ...common,
          username: form.username,
          password: form.password,
          ...(form.teacher_id ? { teacher_id: form.teacher_id } : {}),
          ...(chooseSchool && form.school ? { school: Number(form.school) } : {}),
        })
        toast.success(t("O'qituvchi qo'shildi"))
      }
      onDone()
    } catch (err) {
      toast.error(getErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  return (
    <Modal open={open} onClose={onClose} title={editing ? t("O'qituvchini tahrirlash") : t("Yangi o'qituvchi")} size="lg">
      <form onSubmit={handleSubmit} className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <Field label={t("Ism")}>
          <Input value={form.first_name} onChange={(e) => set("first_name", e.target.value)} required />
        </Field>
        <Field label={t("Familiya")}>
          <Input value={form.last_name} onChange={(e) => set("last_name", e.target.value)} />
        </Field>
        {!editing && (
          <>
            <Field label={t("Login")}>
              <Input value={form.username} onChange={(e) => set("username", e.target.value)} autoComplete="off" required />
            </Field>
            <Field label={t("Parol")}>
              <Input type="password" value={form.password} onChange={(e) => set("password", e.target.value)} autoComplete="new-password" required />
            </Field>
          </>
        )}
        <Field label={t("Telefon")}>
          <PhoneInput value={form.phone} onChange={(phone) => set("phone", phone)} />
        </Field>
        <Field label={t("Email")}>
          <Input type="email" value={form.email} onChange={(e) => set("email", e.target.value)} />
        </Field>
        <Field label={t("Tajriba (yil)")}>
          <Input type="number" min={0} max={70} value={form.experience_years} onChange={(e) => set("experience_years", e.target.value)} />
        </Field>
        {!editing && (
          <Field label={t("O'qituvchi kodi")}>
            <Input value={form.teacher_id} onChange={(e) => set("teacher_id", e.target.value)} placeholder={t("Avtomatik")} />
          </Field>
        )}
        {!editing && chooseSchool && (
          <Field label={t("Maktab")} className="sm:col-span-2">
            <Select value={form.school} onChange={(e) => set("school", e.target.value)} required>
              <option value="">{t("Tanlang...")}</option>
              {schools?.results.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.name}
                </option>
              ))}
            </Select>
          </Field>
        )}

        <div className="sm:col-span-2">
          <p className="mb-2 text-sm font-medium text-ink-700 dark:text-ink-300">{t("Fanlar")}</p>
          <div className="flex flex-wrap gap-2">
            {(subjects?.results ?? []).map((s) => {
              const on = chosen.includes(s.id)
              return (
                <button
                  key={s.id}
                  type="button"
                  aria-pressed={on}
                  onClick={() => toggleSubject(s.id)}
                  className={cn(
                    "rounded-full border px-3 py-1.5 text-sm font-medium transition-colors",
                    on
                      ? "border-transparent bg-brand-600 text-white"
                      : "border-ink-200 text-ink-600 hover:bg-ink-50 dark:border-ink-700 dark:text-ink-300 dark:hover:bg-ink-800"
                  )}
                >
                  {s.name}
                </button>
              )
            })}
          </div>
        </div>

        <Button type="submit" className="sm:col-span-2" loading={loading}>
          {t("Saqlash")}
        </Button>
      </form>
    </Modal>
  )
}
