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
import NotFoundPage from "./pages/NotFound"
import type { Role } from "./types"

const STAFF = ["ADMIN", "SUPERADMIN"] as const
const NOT_SUPERADMIN: Role[] = ["ADMIN", "TEACHER", "STUDENT", "PARENT"]

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

            <Route element={<RoleGuard roles={["STUDENT"]} />}>
              <Route path="/ai" element={<AIAssistantPage />} />
            </Route>

            <Route element={<RoleGuard roles={[...STAFF, "TEACHER", "PARENT"]} />}>
              <Route path="/students" element={<StudentsPage />} />
            </Route>

            <Route element={<RoleGuard roles={[...STAFF]} />}>
              <Route path="/teachers" element={<TeachersPage />} />
              <Route path="/parents" element={<ParentsPage />} />
              <Route path="/analytics" element={<AnalyticsPage />} />
            </Route>

            {/* SUPERADMIN is an oversight role: no attendance, homework, quizzes,
                or the standalone class browser (it drills into a class from
                inside Grades instead). */}
            <Route element={<RoleGuard roles={NOT_SUPERADMIN} />}>
              <Route path="/attendance" element={<AttendancePage />} />
              <Route path="/homework" element={<HomeworkPage />} />
              <Route path="/quizzes" element={<QuizzesPage />} />
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
