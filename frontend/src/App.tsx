import { useEffect } from "react"
import { Navigate, Route, Routes } from "react-router-dom"
import { Toaster } from "react-hot-toast"
import { AppLayout } from "./components/layout/AppLayout"
import { ProtectedRoute } from "./routes/ProtectedRoute"
import { RoleGuard } from "./routes/RoleGuard"
import { useAuthStore } from "./store/auth"
import { api } from "./lib/api"

import LoginPage from "./pages/auth/Login"
import DashboardPage from "./pages/Dashboard"
import StudentsPage from "./pages/Students"
import TeachersPage from "./pages/Teachers"
import ParentsPage from "./pages/Parents"
import ClassesPage from "./pages/Classes"
import SubjectsPage from "./pages/Subjects"
import SchedulePage from "./pages/Schedule"
import GradesPage from "./pages/Grades"
import AttendancePage from "./pages/Attendance"
import HomeworkPage from "./pages/Homework"
import QuizzesPage from "./pages/Quizzes"
import LibraryPage from "./pages/Library"
import ChatPage from "./pages/Chat"
import AnnouncementsPage from "./pages/Announcements"
import NotificationsPage from "./pages/Notifications"
import HelpdeskPage from "./pages/Helpdesk"
import AIAssistantPage from "./pages/AIAssistant"
import AnalyticsPage from "./pages/Analytics"
import ProfilePage from "./pages/Profile"
import ClassManagementPage from "./pages/ClassManagement"
import EducationManagementPage from "./pages/EducationManagement"
import UsersRolesPage from "./pages/UsersRoles"
import NotFoundPage from "./pages/NotFound"

const ATTENDANCE_PERMS = ["view_own_attendance", "view_child_attendance", "view_assigned_attendance", "view_all_attendance", "view_class_reports"]
const HOMEWORK_PERMS = ["view_own_homework", "view_child_homework", "view_assigned_homework", "view_all_homework", "view_class_reports"]
const QUIZ_PERMS = ["view_own_quizzes", "view_child_quizzes", "view_assigned_quizzes", "view_all_quizzes", "view_class_reports"]
const STUDENT_PERMS = ["view_all_students", "view_assigned_students", "view_class_students", "view_child_profile"]
const CLASS_PERMS = ["view_all_classes", "view_assigned_classes", "view_own_class", "view_child_class"]

export default function App() {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated())
  const setUser = useAuthStore((s) => s.setUser)

  useEffect(() => {
    if (isAuthenticated) {
      api.get("/users/me/").then((res) => setUser(res.data)).catch(() => {})
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  return (
    <>
      <Toaster position="top-right" toastOptions={{ className: "font-sans text-sm" }} />
      <Routes>
        <Route path="/login" element={isAuthenticated ? <Navigate to="/" replace /> : <LoginPage />} />

        <Route element={<ProtectedRoute />}>
          <Route element={<AppLayout />}>
            <Route path="/" element={<DashboardPage />} />
            <Route path="/schedule" element={<SchedulePage />} />
            <Route path="/grades" element={<GradesPage />} />
            <Route path="/library" element={<LibraryPage />} />
            <Route path="/chat" element={<ChatPage />} />
            <Route path="/announcements" element={<AnnouncementsPage />} />
            <Route path="/notifications" element={<NotificationsPage />} />
            <Route path="/helpdesk" element={<HelpdeskPage />} />
            <Route path="/subjects" element={<SubjectsPage />} />
            <Route path="/profile" element={<ProfilePage />} />

            <Route element={<RoleGuard perms={["use_ai_assistant"]} />}>
              <Route path="/ai" element={<AIAssistantPage />} />
            </Route>

            <Route element={<RoleGuard perms={STUDENT_PERMS} />}>
              <Route path="/students" element={<StudentsPage />} />
            </Route>

            <Route element={<RoleGuard perms={["view_all_teachers"]} />}>
              <Route path="/teachers" element={<TeachersPage />} />
            </Route>
            <Route element={<RoleGuard perms={["view_all_parents"]} />}>
              <Route path="/parents" element={<ParentsPage />} />
            </Route>
            <Route element={<RoleGuard perms={["view_reports"]} />}>
              <Route path="/analytics" element={<AnalyticsPage />} />
            </Route>

            {/* Role dashboards: a class teacher's class, the director's / deputy's school
                overview, and the administrator's user & role management. */}
            <Route element={<RoleGuard roles={["CLASS_TEACHER"]} />}>
              <Route path="/my-class" element={<ClassManagementPage />} />
            </Route>
            <Route element={<RoleGuard roles={["DIRECTOR", "DEPUTY_DIRECTOR"]} />}>
              <Route path="/education" element={<EducationManagementPage />} />
            </Route>
            <Route element={<RoleGuard perms={["manage_users"]} />}>
              <Route path="/users" element={<UsersRolesPage />} />
            </Route>

            {/* SUPERADMIN is an oversight role: it holds no attendance, homework or quiz
                permission, and no standalone class browser (it drills into a class from
                inside Grades instead). */}
            <Route element={<RoleGuard perms={ATTENDANCE_PERMS} />}>
              <Route path="/attendance" element={<AttendancePage />} />
            </Route>
            <Route element={<RoleGuard perms={HOMEWORK_PERMS} />}>
              <Route path="/homework" element={<HomeworkPage />} />
            </Route>
            <Route element={<RoleGuard perms={QUIZ_PERMS} />}>
              <Route path="/quizzes" element={<QuizzesPage />} />
            </Route>
            <Route element={<RoleGuard perms={CLASS_PERMS} hiddenFor={["SUPERADMIN"]} />}>
              <Route path="/classes" element={<ClassesPage />} />
            </Route>

            <Route path="*" element={<NotFoundPage />} />
          </Route>
        </Route>

        <Route path="*" element={<Navigate to={isAuthenticated ? "/" : "/login"} replace />} />
      </Routes>
    </>
  )
}
