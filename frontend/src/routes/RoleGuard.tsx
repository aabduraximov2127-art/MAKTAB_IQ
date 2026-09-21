import { Navigate, Outlet } from "react-router-dom"
import { useAuthStore } from "../store/auth"
import type { Role } from "../types"

export function RoleGuard({ roles }: { roles: Role[] }) {
  const user = useAuthStore((s) => s.user)
  if (!user) return null
  if (!roles.includes(user.role)) return <Navigate to="/" replace />
  return <Outlet />
}
