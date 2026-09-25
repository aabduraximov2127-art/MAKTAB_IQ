import { format, formatDistanceToNow, parseISO } from "date-fns"
import { enUS, ru, uz } from "date-fns/locale"
import type { AbsenceReason, AttendanceStatus, EffectiveRole, NotificationType, User } from "../types"
import { getLang, t } from "../i18n"

export function fullName(user?: { first_name?: string; last_name?: string; username?: string } | null) {
  if (!user) return "—"
  const name = [user.first_name, user.last_name].filter(Boolean).join(" ").trim()
  return name || user.username || "—"
}

/** "Azizbek Abduraximov" -> "Azizbek.A" — used for compact schedule/lesson cards. */
export function shortName(name?: string | null) {
  if (!name) return "—"
  const parts = name.trim().split(/\s+/).filter(Boolean)
  if (parts.length === 0) return "—"
  if (parts.length === 1) return parts[0]!
  return `${parts[0]}.${parts[1]![0]!.toUpperCase()}`
}

export function initials(user?: { first_name?: string; last_name?: string; username?: string } | null) {
  if (!user) return "?"
  const name = fullName(user)
  const parts = name.split(" ").filter(Boolean)
  if (parts.length === 0) return "?"
  if (parts.length === 1) return parts[0]!.slice(0, 2).toUpperCase()
  return (parts[0]![0] + parts[1]![0]).toUpperCase()
}

export const ROLE_LABELS: Record<EffectiveRole, string> = {
  SUPERADMIN: "Superadmin",
  ADMIN: "Admin",
  DIRECTOR: t("Direktor"),
  DEPUTY_DIRECTOR: t("Direktor o'rinbosari"),
  CLASS_TEACHER: t("Sinf rahbari"),
  TEACHER: t("O'qituvchi"),
  STUDENT: t("O'quvchi"),
  PARENT: t("Ota-ona"),
}

export const ATTENDANCE_LABELS: Record<AttendanceStatus, string> = {
  PRESENT: t("Keldi"),
  ABSENT: t("Kelmadi"),
  LATE: t("Kechikdi"),
  EXCUSED: t("Sababli"),
}

export const ABSENCE_REASON_LABELS: Record<AbsenceReason, string> = {
  SICK: t("Kasal"),
  FAMILY: t("Oilaviy sabab"),
  COMPETITION: t("Musobaqa / olimpiada"),
  OTHER: t("Boshqa sabab"),
}

/** "Sababli · Kasal" for an excused absence, plain label otherwise. */
export function attendanceLabel(status: AttendanceStatus, reason?: AbsenceReason | "" | null) {
  if (status === "ABSENT") return t("Sababsiz")
  if (status === "EXCUSED" && reason) return `${ATTENDANCE_LABELS.EXCUSED} · ${ABSENCE_REASON_LABELS[reason]}`
  return ATTENDANCE_LABELS[status]
}

/** Soft tint with an outline — for text-sized markers; strong enough to read on both themes. */
export const ATTENDANCE_COLORS: Record<AttendanceStatus, string> = {
  PRESENT: "bg-emerald-100 text-emerald-800 ring-1 ring-inset ring-emerald-300 dark:bg-emerald-500/25 dark:text-emerald-200 dark:ring-emerald-400/40",
  ABSENT: "bg-rose-100 text-rose-800 ring-1 ring-inset ring-rose-300 dark:bg-rose-500/25 dark:text-rose-200 dark:ring-rose-400/40",
  LATE: "bg-amber-100 text-amber-900 ring-1 ring-inset ring-amber-300 dark:bg-amber-500/25 dark:text-amber-200 dark:ring-amber-400/40",
  EXCUSED: "bg-sky-100 text-sky-800 ring-1 ring-inset ring-sky-300 dark:bg-sky-500/25 dark:text-sky-200 dark:ring-sky-400/40",
}

/** Solid, saturated fills — calendar days, legend dots, counters, the chosen outcome. The first
 * class is always the background, so ``.split(" ")[0]`` gives a plain dot colour. */
export const ATTENDANCE_SOLID: Record<AttendanceStatus, string> = {
  PRESENT: "bg-emerald-600 text-white",
  ABSENT: "bg-rose-600 text-white",
  LATE: "bg-amber-400 text-amber-950",
  EXCUSED: "bg-sky-600 text-white",
}

/** "Not marked yet" — clearly grey, never confusable with a status colour. */
export const ATTENDANCE_UNMARKED = "bg-ink-200 text-ink-700 dark:bg-ink-700 dark:text-ink-100"

export const NOTIFICATION_ICON_LABEL: Record<NotificationType, string> = {
  GRADE: t("Yangi baho"),
  ATTENDANCE: t("Davomat"),
  ABSENT: t("Kelmadi"),
  HOMEWORK: t("Uy vazifasi"),
  HOMEWORK_DEADLINE: t("Muddat yaqinlashmoqda"),
  QUIZ_RESULT: t("Test natijasi"),
  ANNOUNCEMENT: t("E'lon"),
  EMERGENCY: t("Favqulodda"),
  CHAT_MESSAGE: t("Xabar"),
}

export function formatDate(value?: string | null, pattern = "dd.MM.yyyy") {
  if (!value) return "—"
  try {
    return format(parseISO(value), pattern)
  } catch {
    return value
  }
}

export function formatDateTime(value?: string | null) {
  return formatDate(value, "dd.MM.yyyy HH:mm")
}

const DATE_LOCALES = { uz, ru, en: enUS }

export function formatRelative(value?: string | null) {
  if (!value) return "—"
  try {
    return formatDistanceToNow(parseISO(value), { addSuffix: true, locale: DATE_LOCALES[getLang()] })
  } catch {
    return value
  }
}

/** Grading scale is 0-10 ("baho"): 9-10 a'lo, 7-8 yaxshi, 5-6 qoniqarli, <5 qoniqarsiz. */
export function gradeColor(value: number) {
  if (value >= 9) return "text-emerald-600 dark:text-emerald-400"
  if (value >= 7) return "text-brand-600 dark:text-brand-400"
  if (value >= 5) return "text-amber-600 dark:text-amber-400"
  return "text-rose-600 dark:text-rose-400"
}

export function gradeCellClasses(value: number | null) {
  if (value === null) return "bg-ink-50 text-ink-300 dark:bg-ink-800/50 dark:text-ink-600"
  if (value >= 9) return "bg-emerald-100 text-emerald-700 dark:bg-emerald-500/15 dark:text-emerald-400"
  if (value >= 7) return "bg-brand-100 text-brand-700 dark:bg-brand-500/15 dark:text-brand-300"
  if (value >= 5) return "bg-amber-100 text-amber-700 dark:bg-amber-500/15 dark:text-amber-400"
  return "bg-rose-100 text-rose-700 dark:bg-rose-500/15 dark:text-rose-400"
}

/** "O'qituvchi · Sinf rahbari" — every role the user effectively holds. */
export function roleLabels(user: Pick<User, "role" | "roles"> | null | undefined): string {
  if (!user) return ""
  const roles: EffectiveRole[] = user.roles && user.roles.length > 0 ? user.roles : [user.role]
  return roles.map((r) => ROLE_LABELS[r]).join(" · ")
}
