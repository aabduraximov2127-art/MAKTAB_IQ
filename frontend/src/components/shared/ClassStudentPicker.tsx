import { useState } from "react"
import { useFetch } from "../../hooks/useFetch"
import { Select } from "../ui/Select"
import { fullName } from "../../lib/format"
import type { ClassRoom, Paginated, StudentProfile } from "../../types"
import { cn } from "../../lib/cn"
import { t } from "../../i18n"

export interface PickerSelection {
  classRoom: ClassRoom | null
  student: StudentProfile | null
}

interface ClassStudentPickerProps {
  onChange: (selection: PickerSelection) => void
  /** Ask for a pupil after the class. When false only the class select is shown. */
  withStudent?: boolean
  className?: string
}

/**
 * "Sinfni tanlang" -> "O'quvchini tanlang" — the two linked selects the director uses to browse
 * the school. The pupil list is only loaded once a class is chosen and resets when the class
 * changes. Reports the chosen class / pupil objects (not just ids) to the parent.
 */
export function ClassStudentPicker({ onChange, withStudent = true, className }: ClassStudentPickerProps) {
  const [classId, setClassId] = useState("")
  const [studentId, setStudentId] = useState("")

  const { data: classes } = useFetch<Paginated<ClassRoom>>("/classes/?page_size=100&ordering=name")
  const { data: students, loading: studentsLoading } = useFetch<Paginated<StudentProfile>>(
    withStudent && classId ? `/students/?class_room=${classId}&page_size=100` : null,
    [classId]
  )

  function pickClass(id: string) {
    setClassId(id)
    setStudentId("")
    onChange({ classRoom: classes?.results.find((c) => String(c.id) === id) ?? null, student: null })
  }

  function pickStudent(id: string) {
    setStudentId(id)
    onChange({
      classRoom: classes?.results.find((c) => String(c.id) === classId) ?? null,
      student: students?.results.find((s) => String(s.id) === id) ?? null,
    })
  }

  return (
    <div className={cn("flex flex-wrap gap-3", className)}>
      <Select value={classId} onChange={(e) => pickClass(e.target.value)} className="min-w-[12rem]" aria-label={t("Sinfni tanlang...")}>
        <option value="">{t("Sinfni tanlang...")}</option>
        {classes?.results.map((c) => (
          <option key={c.id} value={c.id}>
            {c.name}
          </option>
        ))}
      </Select>

      {withStudent && (
        <Select
          value={studentId}
          onChange={(e) => pickStudent(e.target.value)}
          disabled={!classId || studentsLoading}
          className="min-w-[14rem]"
          aria-label={t("O'quvchini tanlang...")}
        >
          <option value="">{studentsLoading ? t("Yuklanmoqda...") : t("O'quvchini tanlang...")}</option>
          {students?.results.map((s) => (
            <option key={s.id} value={s.id}>
              {fullName(s.user)}
            </option>
          ))}
        </Select>
      )}
    </div>
  )
}
