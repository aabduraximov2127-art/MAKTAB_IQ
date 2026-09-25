"""Role & permission system: one shared 'school world' and a test class per role.

Every scenario checks the BACKEND (status codes and payloads), never the UI:
401 for anonymous requests, 403 for a missing permission or somebody else's object.
"""

from django.test import SimpleTestCase
from rest_framework import status
from rest_framework.test import APITestCase

from apps.assignments.models import Assignment
from apps.attendance.models import Attendance, AttendanceStatus
from apps.classes.models import AcademicYear, ClassRoom, Quarter
from apps.grades.models import Grade
from apps.lessons.models import Lesson
from apps.notifications.models import Announcement
from apps.quizzes.models import Quiz
from apps.schools.models import School
from apps.subjects.models import Subject
from common import rbac

from .models import ParentProfile, ParentStudent, StudentProfile, TeacherProfile, User

PASSWORD = "Str0ngPass!23"
R = User.Role


# ---------------------------------------------------------------------------
# The registry itself (no database)
# ---------------------------------------------------------------------------
class RegistryTests(SimpleTestCase):
    SPEC_NAMES = """
        view_own_profile view_own_grades view_own_attendance view_own_homework view_own_schedule view_own_class
        view_child_profile view_child_grades view_child_attendance view_child_homework view_child_schedule
        view_assigned_students create_grade update_grade delete_grade create_homework update_homework
        delete_homework mark_attendance update_attendance
        manage_class_students manage_class_attendance manage_class_homework view_class_reports
        view_all_students view_all_teachers view_all_classes view_all_subjects view_all_grades
        view_all_attendance view_reports
        manage_users manage_roles manage_permissions manage_students manage_teachers manage_classes
        manage_subjects manage_schedule manage_school_settings
    """.split()

    def test_every_permission_named_in_the_spec_exists(self):
        missing = [name for name in self.SPEC_NAMES if name not in rbac.PERMISSIONS]
        self.assertEqual(missing, [])

    def test_eight_roles_class_teacher_is_derived(self):
        self.assertEqual(
            set(rbac.ALL_ROLES),
            {"SUPERADMIN", "ADMIN", "DIRECTOR", "DEPUTY_DIRECTOR", "TEACHER", "CLASS_TEACHER", "STUDENT", "PARENT"},
        )
        self.assertNotIn(rbac.CLASS_TEACHER, rbac.STORED_ROLES)

    def test_student_holds_no_write_or_management_permission(self):
        perms = rbac.ROLE_PERMISSIONS[rbac.STUDENT]
        forbidden = {
            "create_grade", "update_grade", "delete_grade", "mark_attendance", "update_attendance",
            "create_homework", "update_homework", "delete_homework", "manage_users", "manage_roles",
            "manage_permissions", "manage_students", "manage_teachers", "manage_classes", "manage_subjects",
            "transfer_students", "update_own_profile", "view_all_students", "view_all_grades",
        }
        self.assertEqual(perms & forbidden, set())

    def test_parent_is_read_only_on_children(self):
        perms = rbac.ROLE_PERMISSIONS[rbac.PARENT]
        self.assertEqual(perms & {"create_grade", "update_attendance", "transfer_students", "manage_classes"}, set())
        self.assertTrue({"view_child_grades", "view_child_attendance", "view_child_schedule"} <= perms)

    def test_teacher_cannot_transfer_students_by_default_but_class_teacher_can(self):
        self.assertNotIn("transfer_students", rbac.ROLE_PERMISSIONS[rbac.TEACHER])
        self.assertIn("transfer_students", rbac.ROLE_PERMISSIONS[rbac.CLASS_TEACHER])

    def test_director_and_admin_are_separate(self):
        director, admin = rbac.ROLE_PERMISSIONS[rbac.DIRECTOR], rbac.ROLE_PERMISSIONS[rbac.ADMIN]
        self.assertNotEqual(director, admin)
        self.assertEqual(
            director & {"manage_users", "manage_roles", "manage_permissions", "manage_school_settings",
                        "manage_classes", "manage_subjects", "manage_students", "manage_teachers"},
            set(),
        )
        self.assertTrue({"manage_users", "manage_roles", "manage_permissions"} <= admin)

    def test_deputy_supervises_and_manages_schedule_only(self):
        perms = rbac.ROLE_PERMISSIONS[rbac.DEPUTY_DIRECTOR]
        self.assertIn("manage_schedule", perms)
        self.assertTrue({"view_all_students", "view_all_grades", "view_all_attendance", "view_reports"} <= perms)
        self.assertEqual(perms & {"create_grade", "mark_attendance", "manage_users", "manage_classes"}, set())

    def test_superadmin_stays_an_oversight_role(self):
        perms = rbac.ROLE_PERMISSIONS[rbac.SUPERADMIN]
        self.assertEqual(
            perms & {"mark_attendance", "view_all_attendance", "create_homework", "view_all_homework",
                     "manage_quizzes", "view_all_quizzes", "create_grade", "manage_library"},
            set(),
        )
        self.assertIn("view_all_grades", perms)


# ---------------------------------------------------------------------------
# Shared fixture: two schools, classes, teachers, students, parents and their data
# ---------------------------------------------------------------------------
class SchoolWorld(APITestCase):
    def make_user(self, username, role, school=None, **extra):
        return User.objects.create_user(username=username, password=PASSWORD, role=role, school=school, **extra)

    def make_teacher(self, username, school, teacher_id, subjects=()):
        user = self.make_user(username, R.TEACHER, school)
        profile = TeacherProfile.objects.create(user=user, school=school, teacher_id=teacher_id)
        profile.subjects.set(subjects)
        return user, profile

    def make_student(self, username, school, class_room, code):
        user = self.make_user(username, R.STUDENT, school, first_name=username.title())
        return user, StudentProfile.objects.create(user=user, school=school, class_room=class_room, student_code=code)

    def as_user(self, user):
        """Authenticate with a *fresh* instance (the RBAC cache lives on the instance)."""
        self.client.force_authenticate(User.objects.get(pk=user.pk))

    def ids(self, response):
        return [row["id"] for row in response.data["results"]]

    def setUp(self):
        self.school_a = School.objects.create(name="School A")
        self.school_b = School.objects.create(name="School B")
        year = AcademicYear.objects.create(name="2026-2027", start_date="2026-09-01", end_date="2027-05-31", is_active=True)
        self.year = year
        self.quarter = Quarter.objects.create(academic_year=year, number=1, start_date="2026-09-01", end_date="2026-10-30")
        self.math = Subject.objects.create(name="Matematika")
        self.physics = Subject.objects.create(name="Fizika")

        # staff
        self.superadmin = self.make_user("super", R.SUPERADMIN, self.school_a)
        self.admin_a = self.make_user("admin_a", R.ADMIN, self.school_a)
        self.admin_b = self.make_user("admin_b", R.ADMIN, self.school_b)
        self.director = self.make_user("director", R.DIRECTOR, self.school_a)
        self.deputy = self.make_user("deputy", R.DEPUTY_DIRECTOR, self.school_a)

        # teachers: t1 curates 9-A and teaches maths there, t2 curates 9-B and teaches physics
        # there, t3 has no assignment at all
        self.t1_user, self.t1 = self.make_teacher("t1", self.school_a, "T-1", [self.math])
        self.t2_user, self.t2 = self.make_teacher("t2", self.school_a, "T-2", [self.physics])
        self.t3_user, self.t3 = self.make_teacher("t3", self.school_a, "T-3")

        self.class_a = ClassRoom.objects.create(school=self.school_a, name="9-A", grade=9, academic_year=year, curator=self.t1)
        self.class_b = ClassRoom.objects.create(school=self.school_a, name="9-B", grade=9, academic_year=year, curator=self.t2)
        self.class_x = ClassRoom.objects.create(school=self.school_b, name="9-X", grade=9, academic_year=year)

        self.s1_user, self.s1 = self.make_student("s1", self.school_a, self.class_a, "S-1")
        self.s2_user, self.s2 = self.make_student("s2", self.school_a, self.class_a, "S-2")
        self.s3_user, self.s3 = self.make_student("s3", self.school_a, self.class_b, "S-3")
        self.s4_user, self.s4 = self.make_student("s4", self.school_b, self.class_x, "S-4")

        self.p1_user = self.make_user("p1", R.PARENT, self.school_a)
        self.p1 = ParentProfile.objects.create(user=self.p1_user)
        ParentStudent.objects.create(parent=self.p1, student=self.s1)
        self.p2_user = self.make_user("p2", R.PARENT, self.school_a)
        self.p2 = ParentProfile.objects.create(user=self.p2_user)
        ParentStudent.objects.create(parent=self.p2, student=self.s3)

        common = {"room": "101", "date": "2026-09-15", "start_time": "09:00", "end_time": "09:45"}
        self.lesson_a = Lesson.objects.create(class_room=self.class_a, subject=self.math, teacher=self.t1, **common)
        self.lesson_b = Lesson.objects.create(class_room=self.class_b, subject=self.physics, teacher=self.t2, **common)

        self.grade_1 = Grade.objects.create(student=self.s1, subject=self.math, teacher=self.t1, academic_year=year, quarter=self.quarter, value=8)
        self.grade_3 = Grade.objects.create(student=self.s3, subject=self.physics, teacher=self.t2, academic_year=year, quarter=self.quarter, value=6)

        self.att_1 = Attendance.objects.create(student=self.s1, class_room=self.class_a, date="2026-09-15", status=AttendanceStatus.PRESENT, marked_by=self.t1)
        self.att_3 = Attendance.objects.create(student=self.s3, class_room=self.class_b, date="2026-09-15", status=AttendanceStatus.PRESENT, marked_by=self.t2)

        deadline = "2026-12-01T10:00:00Z"
        self.hw_a = Assignment.objects.create(lesson=self.lesson_a, teacher=self.t1, title="HW A", deadline=deadline)
        self.hw_b = Assignment.objects.create(lesson=self.lesson_b, teacher=self.t2, title="HW B", deadline=deadline)
        self.quiz_a = Quiz.objects.create(title="Quiz A", subject=self.math, class_room=self.class_a, teacher=self.t1, deadline=deadline, time_limit_minutes=10)
        self.quiz_b = Quiz.objects.create(title="Quiz B", subject=self.physics, class_room=self.class_b, teacher=self.t2, deadline=deadline, time_limit_minutes=10)

    def grade_payload(self, student, subject, value=9):
        return {"student": student.id, "subject": subject.id, "academic_year": self.year.id, "quarter": self.quarter.id, "value": value}


# ---------------------------------------------------------------------------
# API security basics
# ---------------------------------------------------------------------------
class AuthenticationTests(SchoolWorld):
    PROTECTED = [
        "/api/v1/users/me/", "/api/v1/users/", "/api/v1/students/", "/api/v1/teachers/", "/api/v1/parents/",
        "/api/v1/grades/", "/api/v1/attendance/", "/api/v1/assignments/", "/api/v1/quizzes/", "/api/v1/lessons/",
        "/api/v1/classes/", "/api/v1/subjects/", "/api/v1/chat/messages/", "/api/v1/notifications/announcements/",
        "/api/v1/analytics/admin/", "/api/v1/analytics/progress/", "/api/v1/roles/", "/api/v1/permissions/",
    ]

    def test_anonymous_requests_get_401(self):
        for url in self.PROTECTED:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, status.HTTP_401_UNAUTHORIZED)

    def test_anonymous_cannot_change_roles(self):
        response = self.client.post(f"/api/v1/users/{self.t1_user.id}/roles/", {"role": "DIRECTOR"})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_missing_permission_is_403_not_401(self):
        self.as_user(self.s1_user)
        for url in ["/api/v1/users/", "/api/v1/roles/", "/api/v1/permissions/", "/api/v1/analytics/admin/"]:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, status.HTTP_403_FORBIDDEN)

    def test_role_field_still_cannot_be_patched(self):
        self.as_user(self.admin_a)
        response = self.client.patch(f"/api/v1/users/{self.s1_user.id}/", {"role": "SUPERADMIN"})
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)


# ---------------------------------------------------------------------------
# 1. STUDENT
# ---------------------------------------------------------------------------
class StudentRoleTests(SchoolWorld):
    def setUp(self):
        super().setUp()
        self.as_user(self.s1_user)

    def test_sees_only_own_data(self):
        self.assertEqual(self.ids(self.client.get("/api/v1/grades/")), [self.grade_1.id])
        self.assertEqual(self.ids(self.client.get("/api/v1/attendance/")), [self.att_1.id])
        self.assertEqual(self.ids(self.client.get("/api/v1/assignments/")), [self.hw_a.id])
        self.assertEqual(self.ids(self.client.get("/api/v1/lessons/")), [self.lesson_a.id])
        self.assertEqual(self.ids(self.client.get("/api/v1/classes/")), [self.class_a.id])
        self.assertEqual(self.ids(self.client.get("/api/v1/quizzes/")), [self.quiz_a.id])

    def test_sees_own_class_teachers_only(self):
        self.assertEqual(self.ids(self.client.get("/api/v1/teachers/")), [self.t1.id])

    def test_sees_own_profile_and_school_announcements(self):
        self.assertEqual(self.client.get(f"/api/v1/students/{self.s1.id}/").status_code, 200)
        Announcement.objects.create(title="All", content="x", target=Announcement.Target.ALL, created_by=self.admin_a)
        Announcement.objects.create(title="Teachers", content="x", target=Announcement.Target.TEACHERS, created_by=self.admin_a)
        titles = [a["title"] for a in self.client.get("/api/v1/notifications/announcements/").data["results"]]
        self.assertIn("All", titles)
        self.assertNotIn("Teachers", titles)

    def test_other_students_data_is_403(self):
        for url in [
            f"/api/v1/grades/?student={self.s2.id}",
            f"/api/v1/attendance/?student={self.s2.id}",
            f"/api/v1/attendance/calendar/?student={self.s2.id}&month=9&year=2026",
            f"/api/v1/grades/annual/?student={self.s2.id}&academic_year={self.year.id}",
            f"/api/v1/students/{self.s2.id}/",
            f"/api/v1/analytics/progress/?student={self.s2.id}",
            f"/api/v1/grades/{self.grade_3.id}/",
            f"/api/v1/attendance/{self.att_3.id}/",
        ]:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, status.HTTP_403_FORBIDDEN)

    def test_cannot_touch_grades_or_attendance(self):
        self.assertEqual(self.client.post("/api/v1/grades/", self.grade_payload(self.s1, self.math)).status_code, 403)
        self.assertEqual(self.client.patch(f"/api/v1/grades/{self.grade_1.id}/", {"value": 10}).status_code, 403)
        self.assertEqual(self.client.delete(f"/api/v1/grades/{self.grade_1.id}/").status_code, 403)
        self.assertEqual(self.client.patch(f"/api/v1/attendance/{self.att_1.id}/", {"status": "ABSENT"}).status_code, 403)
        self.assertEqual(self.client.delete(f"/api/v1/attendance/{self.att_1.id}/").status_code, 403)
        payload = {"student": self.s1.id, "class_room": self.class_a.id, "subject": self.math.id, "date": "2026-09-16", "status": "PRESENT"}
        self.assertEqual(self.client.post("/api/v1/attendance/", payload).status_code, 403)
        self.grade_1.refresh_from_db()
        self.assertEqual(self.grade_1.value, 8)

    def test_cannot_manage_people_classes_subjects_homework(self):
        self.assertEqual(self.client.post("/api/v1/teachers/", {"teacher_id": "T-9"}).status_code, 403)
        self.assertEqual(self.client.delete(f"/api/v1/teachers/{self.t1.id}/").status_code, 403)
        self.assertEqual(self.client.post("/api/v1/subjects/", {"name": "Kimyo"}).status_code, 403)
        self.assertEqual(
            self.client.post("/api/v1/classes/", {"school": self.school_a.id, "name": "10-A", "grade": 10, "academic_year": self.year.id}).status_code,
            403,
        )
        payload = {"lesson": self.lesson_a.id, "title": "Own homework", "deadline": "2026-12-01T10:00:00Z"}
        self.assertEqual(self.client.post("/api/v1/assignments/", payload).status_code, 403)
        self.assertEqual(self.client.patch(f"/api/v1/assignments/{self.hw_a.id}/", {"title": "Hacked"}).status_code, 403)
        self.assertEqual(self.client.patch(f"/api/v1/assignments/{self.hw_b.id}/", {"title": "Hacked"}).status_code, 403)

    def test_cannot_change_class_role_or_admin_settings(self):
        self.assertEqual(self.client.post(f"/api/v1/students/{self.s1.id}/transfer/", {"new_class": self.class_b.id}).status_code, 403)
        self.assertEqual(self.client.patch(f"/api/v1/students/{self.s1.id}/", {"class_room": self.class_b.id}).status_code, 403)
        self.assertEqual(self.client.patch(f"/api/v1/students/{self.s2.id}/", {"first_name": "X"}).status_code, 403)
        self.assertEqual(self.client.post(f"/api/v1/users/{self.s1_user.id}/roles/", {"role": "ADMIN"}).status_code, 403)
        self.assertEqual(self.client.post(f"/api/v1/users/{self.s1_user.id}/permissions/", {"permission": "create_grade"}).status_code, 403)
        self.assertEqual(self.client.post(f"/api/v1/users/{self.s2_user.id}/reset-password/", {"new_password": "Xx123456!!"}).status_code, 404)
        self.assertEqual(
            self.client.post(f"/api/v1/auth/users/{self.s1_user.id}/reset-password/", {"new_password": "Xx123456!!"}).status_code, 403
        )
        self.s1_user.refresh_from_db()
        self.assertEqual(self.s1_user.role, R.STUDENT)
        self.assertEqual(self.client.get("/api/v1/students/").status_code, 200)

    def test_own_profile_edit_only_with_explicit_grant(self):
        self.assertEqual(self.client.patch(f"/api/v1/students/{self.s1.id}/", {"first_name": "Aziz"}).status_code, 403)
        self.as_user(self.admin_a)
        granted = self.client.post(f"/api/v1/users/{self.s1_user.id}/permissions/", {"permission": "update_own_profile"})
        self.assertEqual(granted.status_code, 200)
        self.as_user(self.s1_user)
        self.assertEqual(self.client.patch(f"/api/v1/students/{self.s1.id}/", {"first_name": "Aziz"}).status_code, 200)
        # even then the class stays untouchable
        self.client.patch(f"/api/v1/students/{self.s1.id}/", {"class_room": self.class_b.id})
        self.s1.refresh_from_db()
        self.assertEqual(self.s1.class_room_id, self.class_a.id)

    def test_submits_only_own_class_homework_and_quizzes(self):
        self.assertEqual(self.client.post(f"/api/v1/assignments/{self.hw_a.id}/submit/", {"answer": "ok"}).status_code, 201)
        self.assertEqual(self.client.post(f"/api/v1/assignments/{self.hw_b.id}/submit/", {"answer": "x"}).status_code, 403)
        self.assertEqual(self.client.post(f"/api/v1/quizzes/{self.quiz_b.id}/submit/", {"answers": {}}, format="json").status_code, 403)

    def test_cannot_see_admin_endpoints(self):
        for url in ["/api/v1/users/", "/api/v1/roles/", "/api/v1/permissions/", "/api/v1/analytics/admin/", "/api/v1/analytics/class/?class_room=1"]:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 403)


# ---------------------------------------------------------------------------
# 2. PARENT
# ---------------------------------------------------------------------------
class ParentRoleTests(SchoolWorld):
    def setUp(self):
        super().setUp()
        self.as_user(self.p1_user)

    def test_sees_only_own_children_data(self):
        self.assertEqual(self.ids(self.client.get("/api/v1/grades/")), [self.grade_1.id])
        self.assertEqual(self.ids(self.client.get("/api/v1/attendance/")), [self.att_1.id])
        self.assertEqual(self.ids(self.client.get("/api/v1/assignments/")), [self.hw_a.id])
        self.assertEqual(self.ids(self.client.get("/api/v1/lessons/")), [self.lesson_a.id])
        self.assertEqual(self.ids(self.client.get("/api/v1/students/")), [self.s1.id])
        self.assertEqual(self.ids(self.client.get("/api/v1/teachers/")), [self.t1.id])
        self.assertEqual(self.ids(self.client.get("/api/v1/classes/")), [self.class_a.id])
        self.assertEqual(self.client.get(f"/api/v1/students/{self.s1.id}/").status_code, 200)

    def test_other_parents_child_is_403(self):
        for url in [
            f"/api/v1/students/{self.s3.id}/",
            f"/api/v1/grades/?student={self.s3.id}",
            f"/api/v1/attendance/?student={self.s3.id}",
            f"/api/v1/analytics/progress/?student={self.s3.id}",
            f"/api/v1/parents/{self.p2.id}/",
            f"/api/v1/grades/{self.grade_3.id}/",
        ]:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, status.HTTP_403_FORBIDDEN)

    def test_can_view_own_child_progress(self):
        self.assertEqual(self.client.get(f"/api/v1/analytics/progress/?student={self.s1.id}").status_code, 200)

    def test_read_only_on_school_data(self):
        self.assertEqual(self.client.post("/api/v1/grades/", self.grade_payload(self.s1, self.math)).status_code, 403)
        self.assertEqual(self.client.patch(f"/api/v1/attendance/{self.att_1.id}/", {"status": "ABSENT"}).status_code, 403)
        self.assertEqual(self.client.post(f"/api/v1/students/{self.s1.id}/transfer/", {"new_class": self.class_b.id}).status_code, 403)
        self.assertEqual(self.client.patch(f"/api/v1/teachers/{self.t1.id}/", {"experience_years": 40}).status_code, 403)
        self.assertEqual(self.client.patch(f"/api/v1/classes/{self.class_a.id}/", {"name": "X"}).status_code, 403)
        self.assertEqual(self.client.delete(f"/api/v1/students/{self.s1.id}/").status_code, 403)

    def test_absence_reason_only_for_own_child(self):
        self.assertEqual(self.client.patch(f"/api/v1/attendance/{self.att_1.id}/submit_reason/", {"parent_reason": "kasal"}).status_code, 200)
        self.assertEqual(self.client.patch(f"/api/v1/attendance/{self.att_3.id}/submit_reason/", {"parent_reason": "kasal"}).status_code, 403)


# ---------------------------------------------------------------------------
# 3. TEACHER
# ---------------------------------------------------------------------------
class TeacherRoleTests(SchoolWorld):
    def test_sees_only_assigned_students_and_classes(self):
        self.as_user(self.t1_user)
        self.assertEqual(sorted(self.ids(self.client.get("/api/v1/students/"))), sorted([self.s1.id, self.s2.id]))
        self.assertEqual(self.ids(self.client.get("/api/v1/classes/")), [self.class_a.id])
        self.assertEqual(self.ids(self.client.get("/api/v1/lessons/")), [self.lesson_a.id])
        self.assertEqual(self.ids(self.client.get("/api/v1/grades/")), [self.grade_1.id])

    def test_unassigned_teacher_sees_and_can_do_nothing(self):
        self.as_user(self.t3_user)
        self.assertEqual(self.ids(self.client.get("/api/v1/students/")), [])
        self.assertEqual(self.client.post("/api/v1/grades/", self.grade_payload(self.s1, self.math)).status_code, 403)
        payload = {"student": self.s1.id, "class_room": self.class_a.id, "subject": self.math.id, "date": "2026-09-16", "status": "PRESENT"}
        self.assertEqual(self.client.post("/api/v1/attendance/", payload).status_code, 403)

    def test_grades_only_inside_own_class_and_subject(self):
        self.as_user(self.t1_user)
        self.assertEqual(self.client.post("/api/v1/grades/", self.grade_payload(self.s1, self.math)).status_code, 201)
        self.assertEqual(self.client.post("/api/v1/grades/", self.grade_payload(self.s3, self.math)).status_code, 403)  # other class
        self.assertEqual(self.client.post("/api/v1/grades/", self.grade_payload(self.s1, self.physics)).status_code, 403)  # other subject
        self.assertEqual(self.client.post("/api/v1/grades/", self.grade_payload(self.s4, self.math)).status_code, 403)  # other school

    def test_cannot_change_another_teachers_grade(self):
        self.as_user(self.t1_user)
        self.assertEqual(self.client.patch(f"/api/v1/grades/{self.grade_3.id}/", {"value": 10}).status_code, 403)
        self.assertEqual(self.client.delete(f"/api/v1/grades/{self.grade_3.id}/").status_code, 403)
        self.assertEqual(self.client.patch(f"/api/v1/grades/{self.grade_1.id}/", {"value": 9}).status_code, 200)
        # ...and cannot re-point an own grade at an outside student
        self.assertEqual(self.client.patch(f"/api/v1/grades/{self.grade_1.id}/", {"student": self.s3.id}).status_code, 403)

    def test_homework_only_on_own_lessons(self):
        self.as_user(self.t1_user)
        deadline = "2026-12-01T10:00:00Z"
        self.assertEqual(self.client.post("/api/v1/assignments/", {"lesson": self.lesson_a.id, "title": "New", "deadline": deadline}).status_code, 201)
        self.assertEqual(self.client.post("/api/v1/assignments/", {"lesson": self.lesson_b.id, "title": "New", "deadline": deadline}).status_code, 403)
        self.assertEqual(self.client.patch(f"/api/v1/assignments/{self.hw_b.id}/", {"title": "X"}).status_code, 403)
        self.assertEqual(self.client.delete(f"/api/v1/assignments/{self.hw_b.id}/").status_code, 403)
        self.assertEqual(self.client.patch(f"/api/v1/assignments/{self.hw_a.id}/", {"lesson": self.lesson_b.id}).status_code, 403)

    def test_attendance_only_for_own_class(self):
        self.as_user(self.t1_user)
        own = {"student": self.s2.id, "class_room": self.class_a.id, "subject": self.math.id, "date": "2026-09-16", "status": "PRESENT"}
        self.assertEqual(self.client.post("/api/v1/attendance/", own).status_code, 201)
        other_class = {"student": self.s3.id, "class_room": self.class_b.id, "subject": self.math.id, "date": "2026-09-16", "status": "ABSENT"}
        self.assertEqual(self.client.post("/api/v1/attendance/", other_class).status_code, 403)
        # a student of another class smuggled into the own class is refused too
        smuggled = {"student": self.s3.id, "class_room": self.class_a.id, "subject": self.math.id, "date": "2026-09-17", "status": "ABSENT"}
        self.assertEqual(self.client.post("/api/v1/attendance/", smuggled).status_code, 403)
        self.assertEqual(self.client.patch(f"/api/v1/attendance/{self.att_3.id}/", {"status": "ABSENT"}).status_code, 403)
        self.assertEqual(self.client.patch(f"/api/v1/attendance/{self.att_1.id}/", {"student": self.s3.id, "date": "2026-09-30"}).status_code, 403)

    def test_cannot_register_students_or_manage_people(self):
        self.as_user(self.t1_user)
        payload = {"username": "new", "password": PASSWORD, "first_name": "N", "last_name": "S", "student_code": "S-77"}
        self.assertEqual(self.client.post("/api/v1/auth/register/student/", payload).status_code, 403)
        self.assertEqual(self.client.patch(f"/api/v1/teachers/{self.t2.id}/", {"experience_years": 30}).status_code, 403)
        self.assertEqual(self.client.patch(f"/api/v1/classes/{self.class_b.id}/", {"name": "Hacked"}).status_code, 403)
        self.assertEqual(self.client.get("/api/v1/users/").status_code, 403)

    def test_cannot_transfer_students_unless_granted(self):
        payload = {"new_class": self.class_b.id, "reason": "test"}
        self.as_user(self.t3_user)
        self.assertEqual(self.client.post(f"/api/v1/students/{self.s1.id}/transfer/", payload).status_code, 403)

        # a teacher who teaches in the class but is not its curator
        Lesson.objects.create(class_room=self.class_a, subject=self.physics, teacher=self.t2, room="102", date="2026-09-16", start_time="10:00", end_time="10:45")
        self.as_user(self.t2_user)
        self.assertEqual(self.client.post(f"/api/v1/students/{self.s1.id}/transfer/", payload).status_code, 403)

        # ...until an admin grants the permission to *that* teacher
        self.as_user(self.admin_a)
        self.assertEqual(self.client.post(f"/api/v1/users/{self.t2_user.id}/permissions/", {"permission": "transfer_students"}).status_code, 200)
        self.as_user(self.t2_user)
        self.assertEqual(self.client.post(f"/api/v1/students/{self.s1.id}/transfer/", {"new_class": self.class_b.id}).status_code, 201)
        # the grant does not reach pupils the teacher is not assigned to
        self.assertEqual(self.client.post(f"/api/v1/students/{self.s4.id}/transfer/", {"new_class": self.class_b.id}).status_code, 403)
        # and other teachers remain unable
        self.as_user(self.t3_user)
        self.assertEqual(self.client.post(f"/api/v1/students/{self.s2.id}/transfer/", payload).status_code, 403)

    def test_teacher_attendance_is_read_only_for_teacher(self):
        self.as_user(self.t1_user)
        self.assertEqual(self.client.get("/api/v1/attendance/teacher-attendance/").status_code, 200)
        self.assertEqual(
            self.client.post("/api/v1/attendance/teacher-attendance/", {"teacher": self.t1.id, "date": "2026-09-16", "status": "PRESENT"}).status_code,
            403,
        )


# ---------------------------------------------------------------------------
# 4. CLASS TEACHER (derived from ClassRoom.curator, always per class)
# ---------------------------------------------------------------------------
class ClassTeacherRoleTests(SchoolWorld):
    def setUp(self):
        super().setUp()
        self.as_user(self.t1_user)  # curator of 9-A only

    def test_role_is_derived_from_curatorship(self):
        me = self.client.get("/api/v1/users/me/").data
        self.assertIn("CLASS_TEACHER", me["roles"])
        self.assertIn("TEACHER", me["roles"])
        self.assertEqual([c["name"] for c in me["curated_classes"]], ["9-A"])
        self.assertIn("manage_class_attendance", me["permissions"])

        self.as_user(self.t3_user)  # not a curator
        me = self.client.get("/api/v1/users/me/").data
        self.assertNotIn("CLASS_TEACHER", me["roles"])
        self.assertNotIn("manage_class_students", me["permissions"])

        # when the curatorship moves, the role moves with it
        ClassRoom.objects.filter(pk=self.class_a.pk).update(curator=self.t3)
        self.as_user(self.t1_user)
        self.assertNotIn("CLASS_TEACHER", self.client.get("/api/v1/users/me/").data["roles"])
        self.as_user(self.t3_user)
        self.assertIn("CLASS_TEACHER", self.client.get("/api/v1/users/me/").data["roles"])

    def test_edits_students_of_own_class_only(self):
        self.assertEqual(self.client.patch(f"/api/v1/students/{self.s1.id}/", {"first_name": "Bobur"}).status_code, 200)
        self.assertEqual(self.client.patch(f"/api/v1/students/{self.s3.id}/", {"first_name": "Bobur"}).status_code, 403)

    def test_manages_attendance_of_own_class_only(self):
        self.assertEqual(self.client.patch(f"/api/v1/attendance/{self.att_1.id}/", {"status": "LATE"}).status_code, 200)
        self.assertEqual(self.client.patch(f"/api/v1/attendance/{self.att_3.id}/", {"status": "LATE"}).status_code, 403)

    def test_transfers_own_class_students_within_the_school(self):
        self.assertEqual(self.client.post(f"/api/v1/students/{self.s1.id}/transfer/", {"new_class": self.class_b.id}).status_code, 201)
        # not a pupil of the curated class, and never into another school
        self.assertEqual(self.client.post(f"/api/v1/students/{self.s3.id}/transfer/", {"new_class": self.class_a.id}).status_code, 403)
        self.assertEqual(self.client.post(f"/api/v1/students/{self.s2.id}/transfer/", {"new_class": self.class_x.id}).status_code, 403)

    def test_sends_announcements_to_own_class_only(self):
        ok = {"title": "9-A parents", "content": "hi", "priority": "NORMAL", "target": "CLASS", "target_class": self.class_a.id}
        created = self.client.post("/api/v1/notifications/announcements/", ok)
        self.assertEqual(created.status_code, 201)
        other = dict(ok, target_class=self.class_b.id)
        self.assertEqual(self.client.post("/api/v1/notifications/announcements/", other).status_code, 403)
        whole_school = dict(ok, target="ALL", target_class=None)
        self.assertEqual(self.client.post("/api/v1/notifications/announcements/", whole_school, format="json").status_code, 403)
        # edits only what they sent themselves
        admin_post = Announcement.objects.create(title="Admin", content="x", target=Announcement.Target.ALL, created_by=self.admin_a)
        self.assertEqual(self.client.patch(f"/api/v1/notifications/announcements/{admin_post.id}/", {"title": "Mine now"}).status_code, 403)
        self.assertEqual(self.client.patch(f"/api/v1/notifications/announcements/{created.data['id']}/", {"title": "Edited"}).status_code, 200)

    def test_class_report_for_own_class_only(self):
        report = self.client.get(f"/api/v1/analytics/class/?class_room={self.class_a.id}")
        self.assertEqual(report.status_code, 200)
        self.assertEqual(report.data["student_count"], 2)
        self.assertEqual(self.client.get(f"/api/v1/analytics/class/?class_room={self.class_b.id}").status_code, 403)
        self.assertEqual(self.client.get("/api/v1/analytics/admin/").status_code, 403)

    def test_no_powers_over_other_classes(self):
        self.assertEqual(self.client.get(f"/api/v1/students/{self.s3.id}/").status_code, 403)
        self.assertNotIn(self.grade_3.id, self.ids(self.client.get("/api/v1/grades/")))
        self.assertNotIn(self.att_3.id, self.ids(self.client.get("/api/v1/attendance/")))
        self.assertEqual(self.client.patch(f"/api/v1/assignments/{self.hw_b.id}/", {"title": "X"}).status_code, 403)


# ---------------------------------------------------------------------------
# 5. DEPUTY DIRECTOR
# ---------------------------------------------------------------------------
class DeputyDirectorRoleTests(SchoolWorld):
    def setUp(self):
        super().setUp()
        self.as_user(self.deputy)

    def test_sees_the_whole_school_but_not_other_schools(self):
        students = self.ids(self.client.get("/api/v1/students/"))
        self.assertEqual(sorted(students), sorted([self.s1.id, self.s2.id, self.s3.id]))
        self.assertNotIn(self.s4.id, students)
        self.assertEqual(sorted(self.ids(self.client.get("/api/v1/teachers/"))), sorted([self.t1.id, self.t2.id, self.t3.id]))
        self.assertEqual(sorted(self.ids(self.client.get("/api/v1/classes/"))), sorted([self.class_a.id, self.class_b.id]))
        self.assertEqual(sorted(self.ids(self.client.get("/api/v1/grades/"))), sorted([self.grade_1.id, self.grade_3.id]))
        self.assertEqual(sorted(self.ids(self.client.get("/api/v1/attendance/"))), sorted([self.att_1.id, self.att_3.id]))
        self.assertEqual(sorted(self.ids(self.client.get("/api/v1/assignments/"))), sorted([self.hw_a.id, self.hw_b.id]))
        self.assertEqual(sorted(self.ids(self.client.get("/api/v1/lessons/"))), sorted([self.lesson_a.id, self.lesson_b.id]))
        self.assertEqual(self.client.get("/api/v1/analytics/admin/").status_code, 200)
        self.assertEqual(self.client.get(f"/api/v1/students/{self.s4.id}/").status_code, 403)

    def test_manages_the_timetable_inside_own_school(self):
        lesson = {"class_room": self.class_a.id, "subject": self.math.id, "teacher": self.t1.id, "room": "201", "date": "2026-09-20", "start_time": "11:00", "end_time": "11:45"}
        created = self.client.post("/api/v1/lessons/", lesson)
        self.assertEqual(created.status_code, 201)
        self.assertEqual(self.client.patch(f"/api/v1/lessons/{created.data['id']}/", {"room": "202"}).status_code, 200)
        foreign = dict(lesson, class_room=self.class_x.id, room="301", start_time="13:00", end_time="13:45")
        self.assertEqual(self.client.post("/api/v1/lessons/", foreign).status_code, 403)

    def test_supervises_but_does_not_write_or_administrate(self):
        self.assertEqual(self.client.post("/api/v1/grades/", self.grade_payload(self.s1, self.math)).status_code, 403)
        self.assertEqual(self.client.patch(f"/api/v1/grades/{self.grade_1.id}/", {"value": 1}).status_code, 403)
        self.assertEqual(self.client.patch(f"/api/v1/attendance/{self.att_1.id}/", {"status": "ABSENT"}).status_code, 403)
        self.assertEqual(self.client.post("/api/v1/subjects/", {"name": "Kimyo"}).status_code, 403)
        self.assertEqual(self.client.patch(f"/api/v1/classes/{self.class_a.id}/", {"name": "X"}).status_code, 403)
        self.assertEqual(self.client.get("/api/v1/users/").status_code, 403)
        self.assertEqual(self.client.post(f"/api/v1/users/{self.t1_user.id}/roles/", {"role": "DIRECTOR"}).status_code, 403)
        self.assertEqual(self.client.post(f"/api/v1/users/{self.t1_user.id}/permissions/", {"permission": "create_grade"}).status_code, 403)
        self.assertEqual(self.client.post(f"/api/v1/students/{self.s1.id}/transfer/", {"new_class": self.class_b.id}).status_code, 403)


# ---------------------------------------------------------------------------
# 6. DIRECTOR (educational oversight, NOT a technical admin)
# ---------------------------------------------------------------------------
class DirectorRoleTests(SchoolWorld):
    def setUp(self):
        super().setUp()
        self.as_user(self.director)

    def test_sees_the_whole_school(self):
        self.assertEqual(len(self.ids(self.client.get("/api/v1/students/"))), 3)
        self.assertEqual(len(self.ids(self.client.get("/api/v1/teachers/"))), 3)
        self.assertEqual(len(self.ids(self.client.get("/api/v1/grades/"))), 2)
        self.assertEqual(self.client.get("/api/v1/analytics/admin/").status_code, 200)
        self.assertEqual(self.client.get(f"/api/v1/analytics/class/?class_room={self.class_b.id}").status_code, 200)
        self.assertEqual(self.client.get(f"/api/v1/students/{self.s4.id}/").status_code, 403)

    def test_is_not_a_technical_admin(self):
        for method, url, body in [
            ("get", "/api/v1/users/", None),
            ("get", "/api/v1/roles/", None),
            ("get", "/api/v1/permissions/", None),
            ("post", f"/api/v1/users/{self.t1_user.id}/roles/", {"role": "ADMIN"}),
            ("post", "/api/v1/subjects/", {"name": "Kimyo"}),
            ("patch", f"/api/v1/classes/{self.class_a.id}/", {"name": "X"}),
            ("patch", f"/api/v1/schools/{self.school_a.id}/", {"name": "Renamed"}),
            ("post", "/api/v1/auth/register/student/", {"username": "n", "password": PASSWORD, "student_code": "S-9"}),
            ("post", "/api/v1/grades/", self.grade_payload(self.s1, self.math)),
        ]:
            with self.subTest(url=url):
                self.assertEqual(getattr(self.client, method)(url, body).status_code, 403)

    def test_can_transfer_students_inside_own_school(self):
        self.assertEqual(self.client.post(f"/api/v1/students/{self.s1.id}/transfer/", {"new_class": self.class_b.id}).status_code, 201)
        self.assertEqual(self.client.post(f"/api/v1/students/{self.s2.id}/transfer/", {"new_class": self.class_x.id}).status_code, 403)


# ---------------------------------------------------------------------------
# 7. ADMIN
# ---------------------------------------------------------------------------
class AdminRoleTests(SchoolWorld):
    def setUp(self):
        super().setUp()
        self.as_user(self.admin_a)

    def test_user_administration_inside_own_school(self):
        listed = [u["username"] for u in self.client.get("/api/v1/users/?page_size=100").data["results"]]
        self.assertIn("s1", listed)
        self.assertNotIn("s4", listed)      # other school
        self.assertNotIn("super", listed)   # never a SUPERADMIN
        self.assertEqual(self.client.post(f"/api/v1/auth/users/{self.s1_user.id}/deactivate/").status_code, 200)
        self.assertEqual(self.client.post(f"/api/v1/auth/users/{self.s4_user.id}/deactivate/").status_code, 403)
        self.assertEqual(self.client.post(f"/api/v1/auth/users/{self.superadmin.id}/deactivate/").status_code, 403)

    def test_creates_students_teachers_classes_subjects(self):
        student = {"username": "newkid", "password": PASSWORD, "first_name": "N", "last_name": "K", "student_code": "S-50", "class_room": self.class_a.id}
        self.assertEqual(self.client.post("/api/v1/auth/register/student/", student).status_code, 201)
        self.assertEqual(self.client.post("/api/v1/subjects/", {"name": "Kimyo"}).status_code, 201)
        klass = {"school": self.school_a.id, "name": "10-A", "grade": 10, "academic_year": self.year.id, "curator": self.t3.id}
        self.assertEqual(self.client.post("/api/v1/classes/", klass).status_code, 201)
        self.assertEqual(self.client.post("/api/v1/classes/", dict(klass, school=self.school_b.id, name="10-B")).status_code, 403)
        self.assertEqual(self.client.patch(f"/api/v1/teachers/{self.t3.id}/", {"subjects": [self.math.id]}).status_code, 200)
        self.assertEqual(self.client.patch(f"/api/v1/teachers/{self.t3.id}/", {"school": self.school_b.id}).status_code, 403)

    def test_assigns_students_to_classes(self):
        self.assertEqual(self.client.post(f"/api/v1/students/{self.s1.id}/transfer/", {"new_class": self.class_b.id}).status_code, 201)
        self.assertEqual(self.client.post(f"/api/v1/students/{self.s4.id}/transfer/", {"new_class": self.class_b.id}).status_code, 403)

    def test_school_settings_only_for_own_school(self):
        self.assertEqual(self.client.patch(f"/api/v1/schools/{self.school_a.id}/", {"name": "Renamed"}).status_code, 200)
        self.assertEqual(self.client.patch(f"/api/v1/schools/{self.school_b.id}/", {"name": "Hacked"}).status_code, 403)

    def test_grants_and_revokes_roles(self):
        url = f"/api/v1/users/{self.t3_user.id}/roles/"
        granted = self.client.post(url, {"role": "DIRECTOR"})
        self.assertEqual(granted.status_code, 200)
        self.assertEqual(granted.data["extra_roles"], ["DIRECTOR"])
        self.assertIn("view_all_grades", granted.data["permissions"])
        self.assertIn("TEACHER", granted.data["roles"])  # multi-role: primary + extra
        removed = self.client.delete(f"{url}DIRECTOR/")
        self.assertEqual(removed.status_code, 200)
        self.assertEqual(removed.data["extra_roles"], [])
        self.assertNotIn("view_all_grades", removed.data["permissions"])

    def test_role_guard_rails(self):
        url = f"/api/v1/users/{self.t3_user.id}/roles/"
        self.assertEqual(self.client.post(url, {"role": "SUPERADMIN"}).status_code, 403)            # only SUPERADMIN hands that out
        self.assertEqual(self.client.post(url, {"role": "CLASS_TEACHER"}).status_code, 400)          # derived, not assignable
        self.assertEqual(self.client.post(url, {"role": "NOPE"}).status_code, 400)
        self.assertEqual(self.client.delete(f"{url}CLASS_TEACHER/").status_code, 400)
        self.assertEqual(self.client.delete(f"{url}TEACHER/").status_code, 400)                     # primary role
        own = f"/api/v1/users/{self.admin_a.id}/roles/"
        self.assertEqual(self.client.post(own, {"role": "DIRECTOR"}).status_code, 403)              # no self-edit
        foreign = f"/api/v1/users/{self.s4_user.id}/roles/"
        self.assertEqual(self.client.post(foreign, {"role": "TEACHER"}).status_code, 403)           # other school
        target_super = f"/api/v1/users/{self.superadmin.id}/roles/"
        self.assertEqual(self.client.post(target_super, {"role": "TEACHER"}).status_code, 403)      # never a SUPERADMIN

    def test_permission_guard_rails(self):
        url = f"/api/v1/users/{self.t3_user.id}/permissions/"
        self.assertEqual(self.client.post(url, {"permission": "transfer_students"}).status_code, 200)
        self.assertEqual(self.client.post(url, {"permission": "manage_roles"}).status_code, 403)    # system level
        self.assertEqual(self.client.post(url, {"permission": "made_up"}).status_code, 400)
        revoked = self.client.delete(f"{url}transfer_students/")
        self.assertEqual(revoked.status_code, 200)
        self.assertNotIn("transfer_students", revoked.data["permissions"])

    def test_catalogues(self):
        roles = self.client.get("/api/v1/roles/").data
        self.assertEqual({r["code"] for r in roles}, set(rbac.ALL_ROLES))
        self.assertTrue(next(r for r in roles if r["code"] == "CLASS_TEACHER")["derived"])
        perms = self.client.get("/api/v1/permissions/").data
        self.assertGreaterEqual(len(perms), 80)
        self.assertIn("manage_school_settings", [p["codename"] for p in perms])

    def test_access_endpoint(self):
        own = self.client.get(f"/api/v1/users/{self.admin_a.id}/access/")
        self.assertEqual(own.status_code, 200)
        other = self.client.get(f"/api/v1/users/{self.t1_user.id}/access/")
        self.assertEqual(other.data["roles"], ["TEACHER", "CLASS_TEACHER"])
        self.assertEqual(self.client.get(f"/api/v1/users/{self.s4_user.id}/access/").status_code, 403)
        self.as_user(self.s1_user)
        self.assertEqual(self.client.get(f"/api/v1/users/{self.s1_user.id}/access/").status_code, 200)   # own
        self.assertEqual(self.client.get(f"/api/v1/users/{self.s2_user.id}/access/").status_code, 403)   # somebody else's

    def test_superadmin_can_hand_out_system_permissions_and_superadmin(self):
        self.as_user(self.superadmin)
        url = f"/api/v1/users/{self.t3_user.id}/permissions/"
        self.assertEqual(self.client.post(url, {"permission": "manage_roles"}).status_code, 200)
        self.assertEqual(self.client.post(f"/api/v1/users/{self.t3_user.id}/roles/", {"role": "SUPERADMIN"}).status_code, 200)
        self.assertEqual(self.client.get(f"/api/v1/users/{self.s4_user.id}/access/").status_code, 200)  # any school


# ---------------------------------------------------------------------------
# 11. MULTIPLE ROLES
# ---------------------------------------------------------------------------
class MultiRoleTests(SchoolWorld):
    def add_role(self, user, role):
        rbac.get_role_group(role).user_set.add(user)

    def test_teacher_plus_parent_gets_the_union(self):
        # t3 is an unassigned teacher who is also the parent of s1
        self.add_role(self.t3_user, R.PARENT)
        parent = ParentProfile.objects.create(user=self.t3_user)
        ParentStudent.objects.create(parent=parent, student=self.s1)
        self.as_user(self.t3_user)

        me = self.client.get("/api/v1/users/me/").data
        self.assertEqual(me["roles"], ["TEACHER", "PARENT"])
        self.assertIn("view_child_grades", me["permissions"])
        self.assertIn("create_grade", me["permissions"])

        self.assertEqual(self.ids(self.client.get("/api/v1/grades/")), [self.grade_1.id])      # via the child
        self.assertEqual(self.client.get(f"/api/v1/students/{self.s1.id}/").status_code, 200)   # own child
        self.assertEqual(self.client.get(f"/api/v1/students/{self.s3.id}/").status_code, 403)   # somebody else's pupil
        # the teacher powers are still confined to the teacher's own assignment
        self.assertEqual(self.client.post("/api/v1/grades/", self.grade_payload(self.s1, self.math)).status_code, 403)

    def test_director_plus_teacher(self):
        self.add_role(self.director, R.TEACHER)
        profile = TeacherProfile.objects.create(user=self.director, school=self.school_a, teacher_id="T-D")
        profile.subjects.add(self.physics)
        self.lesson_c = Lesson.objects.create(class_room=self.class_b, subject=self.physics, teacher=profile, room="9", date="2026-09-18", start_time="08:00", end_time="08:45")
        self.as_user(self.director)

        me = self.client.get("/api/v1/users/me/").data
        self.assertEqual(me["roles"], ["DIRECTOR", "TEACHER"])
        self.assertEqual(len(self.ids(self.client.get("/api/v1/grades/"))), 2)                   # director: everything
        self.assertEqual(self.client.post("/api/v1/grades/", self.grade_payload(self.s3, self.physics)).status_code, 201)   # teacher: own class + subject
        self.assertEqual(self.client.post("/api/v1/grades/", self.grade_payload(self.s1, self.math)).status_code, 403)      # not assigned
        self.assertEqual(self.client.get("/api/v1/users/").status_code, 403)                      # still not an admin

    def test_admin_plus_teacher(self):
        self.add_role(self.admin_a, R.TEACHER)
        self.as_user(self.admin_a)
        me = self.client.get("/api/v1/users/me/").data
        self.assertEqual(me["roles"], ["ADMIN", "TEACHER"])
        self.assertIn("manage_users", me["permissions"])
        self.assertIn("view_assigned_students", me["permissions"])

    def test_extra_permission_is_added_on_top_of_role_permissions(self):
        self.as_user(self.admin_a)
        self.client.post(f"/api/v1/users/{self.s1_user.id}/permissions/", {"permission": "manage_library"})
        self.as_user(self.s1_user)
        self.assertEqual(self.client.post("/api/v1/library/", {"title": "Kitob", "material_type": "BOOK"}).status_code, 201)
        self.as_user(self.s2_user)
        self.assertEqual(self.client.post("/api/v1/library/", {"title": "Kitob", "material_type": "BOOK"}).status_code, 403)

    def test_removing_a_role_removes_its_permissions(self):
        self.add_role(self.t3_user, R.DIRECTOR)
        self.as_user(self.t3_user)
        self.assertEqual(len(self.ids(self.client.get("/api/v1/students/"))), 3)
        self.as_user(self.admin_a)
        self.client.delete(f"/api/v1/users/{self.t3_user.id}/roles/DIRECTOR/")
        self.as_user(self.t3_user)
        self.assertEqual(self.ids(self.client.get("/api/v1/students/")), [])


# ---------------------------------------------------------------------------
# SUPERADMIN keeps its documented limits
# ---------------------------------------------------------------------------
class SuperadminLimitsTests(SchoolWorld):
    def test_oversight_only(self):
        self.as_user(self.superadmin)
        self.assertEqual(len(self.ids(self.client.get("/api/v1/students/"))), 4)   # every school
        self.assertEqual(len(self.ids(self.client.get("/api/v1/grades/"))), 2)
        for url in ["/api/v1/attendance/", "/api/v1/assignments/", "/api/v1/quizzes/"]:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 403)
        self.assertEqual(self.client.post("/api/v1/grades/", self.grade_payload(self.s1, self.math)).status_code, 403)
