import { Navigate, Outlet, useLocation } from "react-router-dom"
import { useAuthStore } from "../store/auth"

export function ProtectedRoute() {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated())
  const user = useAuthStore((s) => s.user)
  const location = useLocation()

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />
  }
  // A session saved before the permission system existed has no `permissions` yet; App
  // refreshes `/users/me/` on load, so hold the page for that one round-trip instead of
  // flashing a menu with nothing in it.
  if (user && !user.permissions) {
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="h-7 w-7 animate-spin rounded-full border-[3px] border-ink-300 border-t-transparent" />
      </div>
    )
  }
  return <Outlet />
}
