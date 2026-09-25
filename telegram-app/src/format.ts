import type { EffectiveRole, User } from "./types"

export function todayISO(): string {
  return new Date().toISOString().slice(0, 10)
}

export function formatDate(iso: string): string {
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return iso
  return d.toLocaleDateString("uz-UZ", { day: "2-digit", month: "2-digit", year: "numeric" })
}

/** "09:00:00" -> "09:00" */
export function formatTime(hms: string): string {
  return hms.slice(0, 5)
}

export function fullName(user?: { first_name?: string; last_name?: string } | null): string {
  if (!user) return "—"
  return [user.first_name, user.last_name].filter(Boolean).join(" ") || "—"
}

export const ROLE_LABELS: Record<EffectiveRole, string> = {
  SUPERADMIN: "Superadmin",
  ADMIN: "Admin",
  DIRECTOR: "Direktor",
  DEPUTY_DIRECTOR: "Direktor o'rinbosari",
  CLASS_TEACHER: "Sinf rahbari",
  TEACHER: "O'qituvchi",
  STUDENT: "O'quvchi",
  PARENT: "Ota-ona",
}

/** "O'qituvchi · Sinf rahbari" — every role the user effectively holds. */
export function roleLabels(user: Pick<User, "role" | "roles">): string {
  const roles = user.roles && user.roles.length > 0 ? user.roles : [user.role]
  return roles.map((r) => ROLE_LABELS[r]).join(" · ")
}
