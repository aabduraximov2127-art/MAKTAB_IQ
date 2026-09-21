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
  { to: "/", label: "Bosh sahifa", icon: LayoutGrid, roles: ALL, section: "Umumiy" },
  { to: "/schedule", label: "Dars jadvali", icon: CalendarDays, roles: ALL, section: "Umumiy" },
  { to: "/grades", label: "Baholar", icon: GraduationCap, roles: ALL, section: "Umumiy" },
  { to: "/attendance", label: "Davomat", icon: ClipboardCheck, roles: NOT_SUPERADMIN, section: "Umumiy" },
  { to: "/homework", label: "Uy vazifalari", icon: ListChecks, roles: NOT_SUPERADMIN, section: "Umumiy" },
  { to: "/quizzes", label: "Testlar", icon: BookOpen, roles: NOT_SUPERADMIN, section: "Umumiy" },
  { to: "/library", label: "Kutubxona", icon: LibraryBig, roles: ALL, section: "Umumiy" },
  { to: "/ai", label: "AI Yordamchi", icon: Bot, roles: ["STUDENT"], section: "Umumiy" },

  { to: "/students", label: "O'quvchilar", icon: Users, roles: [...STAFF, "TEACHER", "PARENT"], section: "Boshqaruv" },
  { to: "/teachers", label: "O'qituvchilar", icon: UsersRound, roles: STAFF, section: "Boshqaruv" },
  { to: "/parents", label: "Ota-onalar", icon: UsersRound, roles: STAFF, section: "Boshqaruv" },
  { to: "/classes", label: "Sinflar", icon: School, roles: NOT_SUPERADMIN, section: "Boshqaruv" },
  { to: "/subjects", label: "Fanlar", icon: BookOpen, roles: NOT_STUDENT, section: "Boshqaruv" },
  { to: "/analytics", label: "Statistika", icon: LineChart, roles: STAFF, section: "Boshqaruv" },

  { to: "/chat", label: "Chat", icon: MessagesSquare, roles: ALL, section: "Aloqa" },
  { to: "/announcements", label: "E'lonlar", icon: Megaphone, roles: NOT_STUDENT, section: "Aloqa" },
  { to: "/notifications", label: "Bildirishnomalar", icon: Bell, roles: NOT_STUDENT, section: "Aloqa" },
  { to: "/helpdesk", label: "Yordam", icon: Ticket, roles: ALL, section: "Aloqa" },
  { to: "/profile", label: "Profil", icon: User, roles: ALL, section: "Aloqa" },
]

export function navForRole(role: Role) {
  return NAV_ITEMS.filter((item) => item.roles.includes(role))
}

export const analyticsIcon = BarChart3
