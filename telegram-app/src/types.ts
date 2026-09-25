export type Role = "SUPERADMIN" | "ADMIN" | "DIRECTOR" | "DEPUTY_DIRECTOR" | "TEACHER" | "STUDENT" | "PARENT"
/** Effective roles also include CLASS_TEACHER, derived from being a class curator. */
export type EffectiveRole = Role | "CLASS_TEACHER"

export interface User {
  id: number
  username: string
  first_name: string
  last_name: string
  email: string
  phone: string
  role: Role
  roles?: EffectiveRole[]
  permissions?: string[]
  telegram_linked?: boolean
}

export interface Paginated<T> {
  count: number
  next: string | null
  previous: string | null
  results: T[]
}

export interface Lesson {
  id: number
  class_room_name: string
  subject_name: string
  teacher_name: string
  room: string
  date: string
  start_time: string
  end_time: string
}

export interface Grade {
  id: number
  subject_name: string
  value: number
  grade_type: string
  created_at: string
}

export interface StudentProgress {
  student: number
  average_grade: number
  attendance_percentage: number
  homework_completion: number
  quiz_average: number
}

export interface AdminAnalytics {
  total_students: number
  total_teachers: number
  total_classes: number
  attendance_percentage: number
  average_grades: number
  homework_completion: number
  quiz_average: number
  active_users: number
  absent_students: number
  teacher_attendance_percentage: number
}

export interface ClassRoom {
  id: number
  name: string
  student_count: number
}

export interface Announcement {
  id: number
  title: string
  content: string
  priority: "LOW" | "NORMAL" | "HIGH"
  created_at: string
}

export interface Notification {
  id: number
  title: string
  message: string
  type: string
  is_read: boolean
  created_at: string
}

export interface Child {
  id: number
  user: { first_name: string; last_name: string }
  class_room_name: string | null
}
