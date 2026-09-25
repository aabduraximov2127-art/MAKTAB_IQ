import { LogOut } from "lucide-react"
import { useAccess } from "../../lib/access"
import { LogoutIcon } from "../ui/icons"

/** The sign-out glyph. The director's console uses the filled Material "Logout" icon; everyone
 * else keeps the outline one. */
export function SignOutIcon({ className }: { className?: string }) {
  const { hasRole } = useAccess()
  return hasRole("DIRECTOR") ? <LogoutIcon className={className} /> : <LogOut className={className} />
}
