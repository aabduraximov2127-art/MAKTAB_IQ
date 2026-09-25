import { Navigate, Outlet } from "react-router-dom"
import { useAccess } from "../lib/access"
import type { EffectiveRole } from "../types"

interface RoleGuardProps {
  /** Allowed when the user holds ANY of these roles (primary, extra or derived). */
  roles?: EffectiveRole[]
  /** Allowed when the user holds ANY of these permissions. */
  perms?: string[]
  /** Refused when every one of the user's roles is listed (e.g. STUDENT-only accounts). */
  hiddenFor?: EffectiveRole[]
}

/**
 * Route guard. Sends the user back to the dashboard when they lack the role / permission.
 * This is a UX nicety — the API enforces the same rules on every request.
 */
export function RoleGuard({ roles, perms, hiddenFor }: RoleGuardProps) {
  const { user, roles: mine, canAny } = useAccess()
  if (!user) return null
  if (roles && !roles.some((r) => mine.includes(r))) return <Navigate to="/" replace />
  if (perms && !canAny(...perms)) return <Navigate to="/" replace />
  if (hiddenFor && mine.every((r) => hiddenFor.includes(r))) return <Navigate to="/" replace />
  return <Outlet />
}
