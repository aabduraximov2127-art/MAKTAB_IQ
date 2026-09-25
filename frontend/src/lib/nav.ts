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
  ShieldCheck,
  Ticket,
  User,
  Users,
  UsersRound,
  Workflow,
} from "lucide-react"
import type { EffectiveRole, User as AppUser } from "../types"
import { permissionsOf, rolesOf } from "./access"
import { t } from "../i18n"

export interface NavItem {
  to: string
  label: string
  icon: typeof LayoutGrid
  section?: string
  /** Visible when the user holds ANY of these permissions (omit = no permission needed). */
  anyPerm?: string[]
  /** Visible when the user holds ANY of these roles (omit = any role). */
  roles?: EffectiveRole[]
  /** Hidden when every one of the user's roles is in this list (e.g. STUDENT-only accounts). */
  hiddenFor?: EffectiveRole[]
}

/*
 * Navigation is driven by the permissions the backend reports for the user, so a user with
 * several roles (Teacher + Parent, Director + Teacher ...) automatically gets the union of
 * the menus. The API still checks every request — this only decides what to show.
 *
 * SUPERADMIN is an oversight role: no attendance, homework or quizzes (it holds none of the
 * matching permissions) and no standalone class browser (it drills into a class from inside
 * Grades instead). STUDENT gets announcements/notifications only via the top bell.
 */
export const NAV_ITEMS: NavItem[] = [
  { to: "/", label: t("Bosh sahifa"), icon: LayoutGrid, section: t("Umumiy") },
  {
    to: "/schedule",
    label: t("Dars jadvali"),
    icon: CalendarDays,
    section: t("Umumiy"),
    anyPerm: ["view_own_schedule", "view_child_schedule", "view_all_schedule", "view_class_reports"],
  },
  {
    to: "/grades",
    label: t("Baholar"),
    icon: GraduationCap,
    section: t("Umumiy"),
    anyPerm: ["view_own_grades", "view_child_grades", "view_assigned_grades", "view_all_grades", "view_class_reports"],
  },
  {
    to: "/attendance",
    label: t("Davomat"),
    icon: ClipboardCheck,
    section: t("Umumiy"),
    anyPerm: [
      "view_own_attendance",
      "view_child_attendance",
      "view_assigned_attendance",
      "view_all_attendance",
      "view_class_reports",
    ],
  },
  {
    to: "/homework",
    label: t("Uy vazifalari"),
    icon: ListChecks,
    section: t("Umumiy"),
    anyPerm: ["view_own_homework", "view_child_homework", "view_assigned_homework", "view_all_homework", "view_class_reports"],
    hiddenFor: ["DIRECTOR"], // homework is the teachers' business; the director does not need the section
  },
  {
    to: "/quizzes",
    label: t("Testlar"),
    icon: BookOpen,
    section: t("Umumiy"),
    anyPerm: ["view_own_quizzes", "view_child_quizzes", "view_assigned_quizzes", "view_all_quizzes", "view_class_reports"],
  },
  { to: "/library", label: t("Kutubxona"), icon: LibraryBig, section: t("Umumiy"), anyPerm: ["view_library"] },
  { to: "/ai", label: t("AI Yordamchi"), icon: Bot, section: t("Umumiy"), anyPerm: ["use_ai_assistant"] },

  // -- role dashboards ---------------------------------------------------------------
  {
    to: "/my-class",
    label: t("Sinf boshqaruvi"),
    icon: Workflow,
    section: t("Boshqaruv"),
    roles: ["CLASS_TEACHER"],
  },
  {
    to: "/education",
    label: t("O'quv jarayoni"),
    icon: ShieldCheck,
    section: t("Boshqaruv"),
    roles: ["DIRECTOR", "DEPUTY_DIRECTOR"],
  },
  { to: "/users", label: t("Foydalanuvchilar va rollar"), icon: UsersRound, section: t("Boshqaruv"), anyPerm: ["manage_users"] },

  {
    to: "/students",
    label: t("O'quvchilar"),
    icon: Users,
    section: t("Boshqaruv"),
    anyPerm: ["view_all_students", "view_assigned_students", "view_class_students", "view_child_profile"],
  },
  { to: "/teachers", label: t("O'qituvchilar"), icon: UsersRound, section: t("Boshqaruv"), anyPerm: ["view_all_teachers"] },
  { to: "/parents", label: t("Ota-onalar"), icon: UsersRound, section: t("Boshqaruv"), anyPerm: ["view_all_parents"] },
  {
    to: "/classes",
    label: t("Sinflar"),
    icon: School,
    section: t("Boshqaruv"),
    anyPerm: ["view_all_classes", "view_assigned_classes", "view_own_class", "view_child_class"],
    hiddenFor: ["SUPERADMIN"],
  },
  {
    to: "/subjects",
    label: t("Fanlar"),
    icon: BookOpen,
    section: t("Boshqaruv"),
    anyPerm: ["view_all_subjects", "view_child_class"],
    hiddenFor: ["STUDENT"],
  },
  { to: "/analytics", label: t("Statistika"), icon: LineChart, section: t("Boshqaruv"), anyPerm: ["view_reports"] },

  { to: "/chat", label: t("Chat"), icon: MessagesSquare, section: t("Aloqa"), anyPerm: ["use_chat"] },
  {
    to: "/announcements",
    label: t("E'lonlar"),
    icon: Megaphone,
    section: t("Aloqa"),
    anyPerm: ["view_announcements"],
    hiddenFor: ["STUDENT"],
  },
  {
    to: "/notifications",
    label: t("Bildirishnomalar"),
    icon: Bell,
    section: t("Aloqa"),
    hiddenFor: ["STUDENT"],
  },
  { to: "/helpdesk", label: t("Yordam"), icon: Ticket, section: t("Aloqa") },
  { to: "/profile", label: t("Profil"), icon: User, section: t("Aloqa") },
]

export function navForUser(user: AppUser | null | undefined): NavItem[] {
  if (!user) return []
  const roles = rolesOf(user)
  const permissions = permissionsOf(user)
  return NAV_ITEMS.filter((item) => {
    if (item.roles && !item.roles.some((r) => roles.includes(r))) return false
    if (item.anyPerm && !item.anyPerm.some((p) => permissions.has(p))) return false
    if (item.hiddenFor && roles.every((r) => item.hiddenFor!.includes(r))) return false
    return true
  })
}

export const analyticsIcon = BarChart3
