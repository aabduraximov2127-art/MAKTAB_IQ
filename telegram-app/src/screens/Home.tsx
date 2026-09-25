import { api, clearTokens } from "../api"
import { getTelegram } from "../telegram"
import { useApi } from "../useApi"
import { Section, Row, EmptyRow } from "../components/Section"
import { formatDate, formatTime, fullName, roleLabels, todayISO } from "../format"
import type {
  AdminAnalytics,
  Announcement,
  Child,
  ClassRoom,
  Grade,
  Lesson,
  Notification,
  Paginated,
  StudentProgress,
  User,
} from "../types"

const FULL_SITE_URL = import.meta.env.VITE_FULL_SITE_URL as string | undefined

export function Home({ user, onSignedOut }: { user: User; onSignedOut: () => void }) {
  return (
    <div>
      <Header user={user} />
      <RoleSections user={user} />
      <NotificationsSection />
      <Footer onSignedOut={onSignedOut} />
    </div>
  )
}

function Header({ user }: { user: User }) {
  return (
    <div className="app-header">
      <div className="greeting">Salom, {user.first_name || user.username} 👋</div>
      <div className="subtitle">{formatDate(new Date().toISOString())}</div>
      <span className="role-badge">{roleLabels(user)}</span>
    </div>
  )
}

/** A user can hold several roles (e.g. Teacher + Parent) — show one block per role family. */
function RoleSections({ user }: { user: User }) {
  const roles = new Set<string>(user.roles && user.roles.length > 0 ? user.roles : [user.role])
  const isAdminLike = ["SUPERADMIN", "ADMIN", "DIRECTOR", "DEPUTY_DIRECTOR"].some((r) => roles.has(r))

  return (
    <>
      {roles.has("STUDENT") && <StudentSections />}
      {roles.has("TEACHER") && <TeacherSections />}
      {roles.has("PARENT") && <ParentSections />}
      {isAdminLike && <AdminSections />}
    </>
  )
}

/* --------------------------------- STUDENT --------------------------------- */

function StudentSections() {
  const { data: progress } = useApi<StudentProgress>("/analytics/progress/")
  const { data: lessons, loading: lessonsLoading } = useApi<Paginated<Lesson>>(
    `/lessons/?date=${todayISO()}&ordering=start_time`
  )
  const { data: grades, loading: gradesLoading } = useApi<Paginated<Grade>>("/grades/?ordering=-created_at&page_size=5")

  return (
    <>
      {progress && (
        <div className="stat-grid">
          <StatTile label="O'rtacha baho" value={progress.average_grade} />
          <StatTile label="Davomat" value={`${progress.attendance_percentage}%`} />
          <StatTile label="Uy vazifa" value={`${progress.homework_completion}%`} />
          <StatTile label="Test o'rtachasi" value={`${progress.quiz_average}%`} />
        </div>
      )}

      <Section title="Bugungi darslar">
        {lessonsLoading ? (
          <EmptyRow text="Yuklanmoqda..." />
        ) : !lessons || lessons.results.length === 0 ? (
          <EmptyRow text="Bugun darsingiz yo'q" />
        ) : (
          lessons.results.map((l) => (
            <Row key={l.id} title={l.subject_name} sub={`${formatTime(l.start_time)}–${formatTime(l.end_time)}`} value={l.room} />
          ))
        )}
      </Section>

      <Section title="So'nggi baholar">
        {gradesLoading ? (
          <EmptyRow text="Yuklanmoqda..." />
        ) : !grades || grades.results.length === 0 ? (
          <EmptyRow text="Hali baho yo'q" />
        ) : (
          grades.results.map((g) => <Row key={g.id} title={g.subject_name} sub={formatDate(g.created_at)} value={g.value} />)
        )}
      </Section>
    </>
  )
}

/* --------------------------------- TEACHER --------------------------------- */

function TeacherSections() {
  const { data: lessons, loading } = useApi<Paginated<Lesson>>(`/lessons/?date=${todayISO()}&ordering=start_time`)
  const { data: classes } = useApi<Paginated<ClassRoom>>("/classes/?page_size=8")
  const totalStudents = classes?.results.reduce((sum, c) => sum + (c.student_count ?? 0), 0)

  return (
    <>
      <div className="stat-grid">
        <StatTile label="Bugungi darslar" value={lessons?.count ?? "—"} />
        <StatTile label="Mening sinflarim" value={classes?.count ?? "—"} />
        <StatTile label="Jami o'quvchilar" value={totalStudents ?? "—"} />
      </div>

      <Section title="Bugungi dars jadvali">
        {loading ? (
          <EmptyRow text="Yuklanmoqda..." />
        ) : !lessons || lessons.results.length === 0 ? (
          <EmptyRow text="Bugun darsingiz yo'q" />
        ) : (
          lessons.results.map((l) => (
            <Row
              key={l.id}
              title={l.subject_name}
              sub={`${l.class_room_name} • ${formatTime(l.start_time)}–${formatTime(l.end_time)}`}
              value={l.room}
            />
          ))
        )}
      </Section>
    </>
  )
}

/* --------------------------------- PARENT --------------------------------- */

function ParentSections() {
  const { data: children, loading } = useApi<Paginated<Child>>("/students/")

  return (
    <Section title="Farzandlaringiz">
      {loading ? (
        <EmptyRow text="Yuklanmoqda..." />
      ) : !children || children.results.length === 0 ? (
        <EmptyRow text="Farzand topilmadi" />
      ) : (
        children.results.map((child) => <ChildRow key={child.id} child={child} />)
      )}
    </Section>
  )
}

function ChildRow({ child }: { child: Child }) {
  const { data: progress } = useApi<StudentProgress>(`/analytics/progress/?student=${child.id}`)
  return (
    <Row
      title={fullName(child.user)}
      sub={child.class_room_name ?? "Sinf biriktirilmagan"}
      value={progress ? `${progress.average_grade} / 10` : "…"}
    />
  )
}

/* ------------------------------- ADMIN/SUPERADMIN ------------------------------- */

function AdminSections() {
  const { data } = useApi<AdminAnalytics>("/analytics/admin/")
  const { data: announcements, loading } = useApi<Paginated<Announcement>>("/notifications/announcements/?page_size=4")

  return (
    <>
      {data && (
        <div className="stat-grid">
          <StatTile label="Jami o'quvchilar" value={data.total_students} />
          <StatTile label="Jami o'qituvchilar" value={data.total_teachers} />
          <StatTile label="Faol foydalanuvchilar" value={data.active_users} />
          <StatTile label="O'rtacha baho" value={data.average_grades} />
        </div>
      )}

      <Section title="So'nggi e'lonlar">
        {loading ? (
          <EmptyRow text="Yuklanmoqda..." />
        ) : !announcements || announcements.results.length === 0 ? (
          <EmptyRow text="E'lonlar yo'q" />
        ) : (
          announcements.results.map((a) => <Row key={a.id} title={a.title} sub={formatDate(a.created_at)} />)
        )}
      </Section>
    </>
  )
}

/* --------------------------------- shared --------------------------------- */

function StatTile({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="stat-tile">
      <div className="stat-label">{label}</div>
      <div className="stat-value">{value}</div>
    </div>
  )
}

function NotificationsSection() {
  const { data, loading } = useApi<Paginated<Notification>>("/notifications/?is_read=false&page_size=5")
  if (!loading && (!data || data.results.length === 0)) return null

  return (
    <Section title={`Bildirishnomalar${data ? ` (${data.count})` : ""}`}>
      {loading ? (
        <EmptyRow text="Yuklanmoqda..." />
      ) : (
        data!.results.map((n) => <Row key={n.id} title={n.title} sub={n.message} unread />)
      )}
    </Section>
  )
}

function Footer({ onSignedOut }: { onSignedOut: () => void }) {
  async function unlink() {
    try {
      await api.post("/users/me/telegram-unlink/")
    } catch {
      /* even if the request fails, still sign the Mini App session out locally */
    }
    clearTokens()
    onSignedOut()
  }

  return (
    <div className="footer-links">
      {FULL_SITE_URL && (
        <button className="text-button" onClick={() => getTelegram()?.openLink(FULL_SITE_URL)}>
          To'liq saytni ochish →
        </button>
      )}
      <button className="text-button" onClick={() => void unlink()} style={{ color: "var(--tg-theme-destructive-text-color, #e0245e)" }}>
        Telegramdan uzish
      </button>
    </div>
  )
}
