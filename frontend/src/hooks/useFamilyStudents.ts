import { useMemo } from "react"
import { useAccess } from "../lib/access"
import type { ParentProfile, StudentProfile } from "../types"
import { useFetch } from "./useFetch"

/**
 * The pupils whose grades / attendance the signed-in user opens as "theirs": their own profile
 * (a student) and their children (a parent) — never classmates or other pupils the user can merely
 * *list*. (`GET /students/` also returns a student's classmates, which exist for the class chat
 * only; building tabs from it showed other pupils' names next to the student's own results.)
 */
export function useFamilyStudents() {
  const { canAny } = useAccess()
  const isStudent = canAny("view_own_grades", "view_own_attendance")
  const isParent = canAny("view_child_grades", "view_child_attendance")

  const own = useFetch<StudentProfile>(isStudent ? "/students/me/" : null)
  const parent = useFetch<ParentProfile>(isParent ? "/parents/me/" : null)

  const students = useMemo(() => {
    const list: StudentProfile[] = []
    if (own.data) list.push(own.data)
    for (const child of parent.data?.children ?? []) {
      if (!list.some((s) => s.id === child.id)) list.push(child)
    }
    return list
  }, [own.data, parent.data])

  return { students, loading: own.loading || parent.loading }
}
