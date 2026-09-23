import {
  BarChart3,
  BookOpen,
  Bot,
  CalendarDays,
  ClipboardCheck,
  GraduationCap,
  LayoutGrid,
  LibraryBig,
  LineChart,
  ListChecks,
  MessagesSquare,
  Megaphone,
  Bell,
  School,
  Ticket,
  User,
  Users,
  UsersRound,
} from "lucide-react"
import type { Role } from "../types"
import { t } from "../i18n"

export interface NavItem {
  to: string
  label: string
  icon: typeof LayoutGrid
  roles: Role[]
  section?: string
}

const ALL: Role[] = ["SUPERADMIN", "ADMIN", "TEACHER", "STUDENT", "PARENT"]
const STAFF: Role[] = ["SUPERADMIN", "ADMIN"]
// SUPERADMIN is deliberately excluded from attendance, homework, quizzes and the
// standalone classes browser — it's an oversight role, not an operational one.
const NOT_SUPERADMIN: Role[] = ["ADMIN", "TEACHER", "STUDENT", "PARENT"]
// STUDENT gets announcements/notifications only via the top bell (NotificationBell) —
// no separate sidebar pages for them. Subjects is a staff/teacher concern for STUDENT.
const NOT_STUDENT: Role[] = ["SUPERADMIN", "ADMIN", "TEACHER", "PARENT"]

export const NAV_ITEMS: NavItem[] = [
  { to: "/", label: t("Bosh sahifa"), icon: LayoutGrid, roles: ALL, section: t("Umumiy") },
  { to: "/schedule", label: t("Dars jadvali"), icon: CalendarDays, roles: ALL, section: t("Umumiy") },
  { to: "/grades", label: t("Baholar"), icon: GraduationCap, roles: ALL, section: t("Umumiy") },
  { to: "/attendance", label: t("Davomat"), icon: ClipboardCheck, roles: NOT_SUPERADMIN, section: t("Umumiy") },
  { to: "/homework", label: t("Uy vazifalari"), icon: ListChecks, roles: NOT_SUPERADMIN, section: t("Umumiy") },
  { to: "/quizzes", label: t("Testlar"), icon: BookOpen, roles: NOT_SUPERADMIN, section: t("Umumiy") },
  { to: "/library", label: t("Kutubxona"), icon: LibraryBig, roles: ALL, section: t("Umumiy") },
  { to: "/ai", label: t("AI Yordamchi"), icon: Bot, roles: ["STUDENT"], section: t("Umumiy") },

  { to: "/students", label: t("O'quvchilar"), icon: Users, roles: [...STAFF, "TEACHER", "PARENT"], section: t("Boshqaruv") },
  { to: "/teachers", label: t("O'qituvchilar"), icon: UsersRound, roles: STAFF, section: t("Boshqaruv") },
  { to: "/parents", label: t("Ota-onalar"), icon: UsersRound, roles: STAFF, section: t("Boshqaruv") },
  { to: "/classes", label: t("Sinflar"), icon: School, roles: NOT_SUPERADMIN, section: t("Boshqaruv") },
  { to: "/subjects", label: t("Fanlar"), icon: BookOpen, roles: NOT_STUDENT, section: t("Boshqaruv") },
  { to: "/analytics", label: t("Statistika"), icon: LineChart, roles: STAFF, section: t("Boshqaruv") },

  { to: "/chat", label: t("Chat"), icon: MessagesSquare, roles: ALL, section: t("Aloqa") },
  { to: "/announcements", label: t("E'lonlar"), icon: Megaphone, roles: NOT_STUDENT, section: t("Aloqa") },
  { to: "/notifications", label: t("Bildirishnomalar"), icon: Bell, roles: NOT_STUDENT, section: t("Aloqa") },
  { to: "/helpdesk", label: t("Yordam"), icon: Ticket, roles: ALL, section: t("Aloqa") },
  { to: "/profile", label: t("Profil"), icon: User, roles: ALL, section: t("Aloqa") },
]

export function navForRole(role: Role) {
  return NAV_ITEMS.filter((item) => item.roles.includes(role))
}

export const analyticsIcon = BarChart3
