import { format, formatDistanceToNow, parseISO } from "date-fns"
import { enUS, ru, uz } from "date-fns/locale"
import type { AttendanceStatus, NotificationType, Role } from "../types"
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

export const ROLE_LABELS: Record<Role, string> = {
  SUPERADMIN: "Superadmin",
  ADMIN: "Admin",
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

export const ATTENDANCE_COLORS: Record<AttendanceStatus, string> = {
  PRESENT: "bg-emerald-100 text-emerald-700 dark:bg-emerald-500/15 dark:text-emerald-400",
  ABSENT: "bg-rose-100 text-rose-700 dark:bg-rose-500/15 dark:text-rose-400",
  LATE: "bg-amber-100 text-amber-700 dark:bg-amber-500/15 dark:text-amber-400",
  EXCUSED: "bg-sky-100 text-sky-700 dark:bg-sky-500/15 dark:text-sky-400",
}

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
