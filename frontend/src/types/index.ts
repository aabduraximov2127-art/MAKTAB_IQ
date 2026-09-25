export type Role = "SUPERADMIN" | "ADMIN" | "DIRECTOR" | "DEPUTY_DIRECTOR" | "TEACHER" | "STUDENT" | "PARENT"
/** Roles a user can *effectively* hold: the stored ones plus CLASS_TEACHER, which the backend
 * derives from being the curator of a class. */
export type EffectiveRole = Role | "CLASS_TEACHER"

export interface User {
  id: number
  username: string
  first_name: string
  last_name: string
  email: string
  phone: string
  role: Role
  /** Effective roles (primary + extra + derived) — from `/users/me/`. */
  roles?: EffectiveRole[]
  /** Permission codenames the user holds — from `/users/me/`. */
  permissions?: string[]
  curated_classes?: { id: number; name: string }[]
  school: number | null
  is_active: boolean
  is_deactivated: boolean
  date_joined: string
  telegram_linked?: boolean
}

export interface School {
  id: number
  name: string
  address: string
  phone: string
  email: string
  logo: string | null
}

export interface AcademicYear {
  id: number
  name: string
  start_date: string
  end_date: string
  is_active: boolean
}

export interface Quarter {
  id: number
  academic_year: number
  number: number
  start_date: string
  end_date: string
}

export interface ClassRoom {
  id: number
  school: number
  name: string
  grade: number
  academic_year: number
  curator: number | null
  curator_name: string | null
  student_count: number
}

export interface Subject {
  id: number
  name: string
  description: string
  icon: string
}

export interface StudentProfile {
  id: number
  user: User
  school: number | null
  class_room: number | null
  class_room_name: string | null
  age: number | null
  passport_number?: string
  photo: string | null
  student_code: string
  created_at: string
}

export interface TeacherProfile {
  id: number
  user: User
  school: number | null
  teacher_id: string
  subjects: number[]
  experience_years: number
  avatar: string | null
}

export interface ParentProfile {
  id: number
  user: User
  children: StudentProfile[]
}

export interface Lesson {
  id: number
  class_room: number
  class_room_name: string
  subject: number
  subject_name: string
  teacher: number
  teacher_name: string
  room: string
  date: string
  start_time: string
  end_time: string
}

export interface Grade {
  id: number
  student: number
  student_name: string
  subject: number
  subject_name: string
  teacher: number | null
  academic_year: number
  quarter: number
  value: number
  grade_type: "DAILY" | "HOMEWORK" | "QUIZ" | "QUARTER" | "EXAM"
  comment: string
  created_at: string
}

export type AttendanceStatus = "PRESENT" | "ABSENT" | "LATE" | "EXCUSED"
/** Why an EXCUSED ("sababli") absence happened; ABSENT means "sababsiz" and carries none. */
export type AbsenceReason = "SICK" | "FAMILY" | "COMPETITION" | "OTHER"

export interface Attendance {
  id: number
  student: number
  student_name: string
  class_room: number
  subject: number | null
  lesson: number | null
  date: string
  status: AttendanceStatus
  absence_reason: AbsenceReason | ""
  marked_by: number | null
  parent_reason: string
  parent_reason_submitted_at: string | null
}

export interface Assignment {
  id: number
  lesson: number
  teacher: number
  title: string
  description: string
  attachment: string | null
  deadline: string
  created_at: string
}

export interface AssignmentSubmission {
  id: number
  assignment: number
  student: number
  student_name: string
  answer: string
  attachment: string | null
  submitted_at: string
  status: "SUBMITTED" | "LATE" | "GRADED"
  score: number | null
}

export interface Question {
  id: number
  quiz: number
  question: string
  options: string[]
  correct_answer?: number
  points: number
}

export interface Quiz {
  id: number
  title: string
  subject: number
  class_room: number
  teacher: number
  deadline: string
  time_limit_minutes: number
  questions: Question[]
  total_points: number
  created_at: string
}

export interface QuizAttempt {
  id: number
  quiz: number
  student: number
  student_name: string
  answers: Record<string, number>
  score: number
  max_score: number
  started_at: string
  submitted_at: string | null
}

export interface LibraryMaterial {
  id: number
  title: string
  material_type: "BOOK" | "PDF" | "DOCUMENT" | "LESSON_MATERIAL" | "VIDEO" | "LINK"
  subject: number | null
  author: string
  file: string | null
  link: string
  uploaded_by: number | null
  created_at: string
}

export type NotificationType =
  | "GRADE"
  | "ATTENDANCE"
  | "ABSENT"
  | "HOMEWORK"
  | "HOMEWORK_DEADLINE"
  | "QUIZ_RESULT"
  | "ANNOUNCEMENT"
  | "EMERGENCY"
  | "CHAT_MESSAGE"

export interface Notification {
  id: number
  title: string
  message: string
  type: NotificationType
  is_read: boolean
  created_at: string
}

export interface Announcement {
  id: number
  title: string
  content: string
  priority: "LOW" | "NORMAL" | "HIGH"
  target: "ALL" | "TEACHERS" | "STUDENTS" | "PARENTS" | "CLASS"
  target_class: number | null
  created_by: number | null
  created_at: string
}

export interface ChatRoom {
  id: number
  room_type: "CLASS_GENERAL" | "PRIVATE" | "TEACHER_STUDENT" | "PARENT_TEACHER" | "STAFF_GENERAL"
  name: string
  class_room: number | null
  members: { id: number; user: number; user_name: string }[]
  last_message: Message | null
}

export interface Message {
  id: number
  chat_room: number
  sender: number | null
  sender_name: string
  text: string
  attachment: string | null
  is_read: boolean
  created_at: string
}

export interface HelpDeskTicket {
  id: number
  user: number
  title: string
  description: string
  category: "TECHNICAL" | "ACADEMIC" | "ACCOUNT" | "OTHER"
  priority: "LOW" | "MEDIUM" | "HIGH"
  status: "OPEN" | "IN_PROGRESS" | "RESOLVED" | "CLOSED"
  assigned_to: number | null
  created_at: string
  updated_at: string
}

export interface StudentProgress {
  success: boolean
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

/** One row of GET /analytics/system/ — a school's headline figures. */
export interface SchoolStats {
  id: number
  name: string
  students: number
  teachers: number
  classes: number
  admins: number
  attendance_percentage: number
  average_grades: number
}

/** GET /analytics/system/ (SuperAdmin): the whole system plus one row per school. */
export interface SystemAnalytics extends AdminAnalytics {
  total_schools: number
  total_admins: number
  schools: SchoolStats[]
}

/** An account as the user directory lists it (GET /users/). */
export interface AdminAccount {
  id: number
  username: string
  first_name: string
  last_name: string
  email: string
  phone: string
  role: Role
  roles: Role[]
  school: number | null
  is_active: boolean
  date_joined: string
}

export interface Paginated<T> {
  success: boolean
  count: number
  next: string | null
  previous: string | null
  results: T[]
}

export interface TeacherAttendance {
  id: number
  teacher: number
  teacher_name: string
  date: string
  status: AttendanceStatus
  reason: string
}

/** A colleague a staff member can start a private chat with (GET /chat/staff/). */
export interface StaffContact {
  id: number
  name: string
  role: "DIRECTOR" | "TEACHER"
}
