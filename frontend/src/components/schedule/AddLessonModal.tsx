import { type FormEvent, useEffect, useMemo, useState } from "react"
import toast from "react-hot-toast"
import { useFetch } from "../../hooks/useFetch"
import { api, getErrorMessage } from "../../lib/api"
import { fullName } from "../../lib/format"
import { Button } from "../ui/Button"
import { Field, Input } from "../ui/Input"
import { Modal } from "../ui/Modal"
import { Select } from "../ui/Select"
import { SearchSelect, type SearchOption } from "../ui/SearchSelect"
import type { ClassRoom, Paginated, Subject, TeacherProfile } from "../../types"
import { t } from "../../i18n"

interface AddLessonModalProps {
  open: boolean
  /** Class and day currently open on the timetable — the form starts with them. */
  defaultClassId: string
  defaultDate: string
  onClose: () => void
  onDone: () => void
}

/**
 * "Yangi dars": class (select), day, subject and teacher (both searchable — type "ma" and the
 * matching subjects appear), room and time. The API refuses a teacher, room or class that is
 * already busy at that time; its message is shown as it comes.
 */
export function AddLessonModal({ open, defaultClassId, defaultDate, onClose, onDone }: AddLessonModalProps) {
  const { data: classes } = useFetch<Paginated<ClassRoom>>(open ? "/classes/?page_size=100&ordering=name" : null, [open])
  const { data: subjects } = useFetch<Paginated<Subject>>(open ? "/subjects/?page_size=100" : null, [open])
  const { data: teachers } = useFetch<Paginated<TeacherProfile>>(open ? "/teachers/?page_size=100" : null, [open])

  const [form, setForm] = useState({
    class_room: defaultClassId,
    subject: "",
    teacher: "",
    room: "",
    date: defaultDate,
    start_time: "09:00",
    end_time: "09:45",
  })
  const [loading, setLoading] = useState(false)
  const set = (key: keyof typeof form, value: string) => setForm((f) => ({ ...f, [key]: value }))

  // every time the dialog opens it starts from the class and day the deputy is looking at
  useEffect(() => {
    if (open) setForm((f) => ({ ...f, class_room: defaultClassId, date: defaultDate, subject: "", teacher: "", room: "" }))
  }, [open, defaultClassId, defaultDate])

  const subjectOptions: SearchOption[] = useMemo(
    () => (subjects?.results ?? []).map((s) => ({ value: String(s.id), label: s.name })),
    [subjects]
  )

  // teachers of the chosen subject come first, and everybody shows what they teach
  const teacherOptions: SearchOption[] = useMemo(() => {
    const subjectName = new Map((subjects?.results ?? []).map((s) => [s.id, s.name]))
    const chosen = Number(form.subject) || null
    return (teachers?.results ?? [])
      .map((tp) => ({
        option: {
          value: String(tp.id),
          label: fullName(tp.user),
          hint: tp.subjects.map((id) => subjectName.get(id)).filter(Boolean).join(", ") || undefined,
        } as SearchOption,
        teachesChosen: chosen !== null && tp.subjects.includes(chosen),
      }))
      .sort((a, b) => Number(b.teachesChosen) - Number(a.teachesChosen) || a.option.label.localeCompare(b.option.label))
      .map((x) => x.option)
  }, [teachers, subjects, form.subject])

  function chooseSubject(value: string) {
    setForm((f) => {
      const next = { ...f, subject: value }
      // if exactly one teacher teaches it, there is nothing to decide
      const teaching = (teachers?.results ?? []).filter((tp) => value && tp.subjects.includes(Number(value)))
      if (teaching.length === 1 && !f.teacher) next.teacher = String(teaching[0]!.id)
      return next
    })
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    if (!form.class_room) return toast.error(t("Sinfni tanlang"))
    if (!form.subject) return toast.error(t("Fanni tanlang"))
    if (!form.teacher) return toast.error(t("O'qituvchini tanlang..."))
    setLoading(true)
    try {
      await api.post("/lessons/", form)
      toast.success(t("Dars qo'shildi"))
      onDone()
    } catch (err) {
      toast.error(getErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  return (
    <Modal open={open} onClose={onClose} title={t("Yangi dars")} size="lg">
      <form onSubmit={handleSubmit} className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <Field label={t("Sinf")}>
          <Select value={form.class_room} onChange={(e) => set("class_room", e.target.value)} required>
            <option value="">{t("Tanlang...")}</option>
            {classes?.results.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name}
              </option>
            ))}
          </Select>
        </Field>
        <Field label={t("Kun")}>
          <Input type="date" value={form.date} onChange={(e) => set("date", e.target.value)} required />
        </Field>
        <Field label={t("Fan")}>
          <SearchSelect options={subjectOptions} value={form.subject} onChange={chooseSubject} placeholder={t("Fan nomini yozing...")} />
        </Field>
        <Field label={t("O'qituvchi")}>
          <SearchSelect
            options={teacherOptions}
            value={form.teacher}
            onChange={(value) => set("teacher", value)}
            placeholder={t("Ism yozing...")}
          />
        </Field>
        <Field label={t("Xona")}>
          <Input value={form.room} onChange={(e) => set("room", e.target.value)} required />
        </Field>
        <div className="grid grid-cols-2 gap-3">
          <Field label={t("Boshlanishi")}>
            <Input type="time" value={form.start_time} onChange={(e) => set("start_time", e.target.value)} required />
          </Field>
          <Field label={t("Tugashi")}>
            <Input type="time" value={form.end_time} onChange={(e) => set("end_time", e.target.value)} required />
          </Field>
        </div>
        <Button type="submit" className="sm:col-span-2" loading={loading}>
          {t("Saqlash")}
        </Button>
      </form>
    </Modal>
  )
}
