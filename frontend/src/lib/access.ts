import { useAuthStore } from "../store/auth"
import type { EffectiveRole, Role, User } from "../types"

/** Roles the API can store on a user (primary role or an extra role). */
export const ASSIGNABLE_ROLES: Role[] = [
  "SUPERADMIN",
  "ADMIN",
  "DIRECTOR",
  "DEPUTY_DIRECTOR",
  "TEACHER",
  "STUDENT",
  "PARENT",
]

/** Effective roles of a user. Falls back to the primary role while `/users/me/` (which adds
 * the extra + derived roles) has not answered yet. */
export function rolesOf(user: User | null | undefined): EffectiveRole[] {
  if (!user) return []
  return user.roles && user.roles.length > 0 ? user.roles : [user.role]
}

export function permissionsOf(user: User | null | undefined): Set<string> {
  return new Set(user?.permissions ?? [])
}

/**
 * Access helpers for the signed-in user. The permission codenames come from the backend
 * (`/users/me/`), which is the single source of truth — hiding a button here is only a
 * convenience; every request is checked again by the API.
 */
export function useAccess() {
  const user = useAuthStore((s) => s.user)
  const roles = rolesOf(user)
  const permissions = permissionsOf(user)

  return {
    user,
    roles,
    permissions,
    /** Has this exact permission. */
    can: (codename: string) => permissions.has(codename),
    /** Has at least one of these permissions. */
    canAny: (...codenames: string[]) => codenames.some((c) => permissions.has(c)),
    /** Holds at least one of these roles (primary, extra or derived). */
    hasRole: (...wanted: EffectiveRole[]) => wanted.some((r) => roles.includes(r)),
    /** The one class this user curates (a curator has exactly one class in practice). */
    curatedClasses: user?.curated_classes ?? [],
  }
}

export type Access = ReturnType<typeof useAccess>
