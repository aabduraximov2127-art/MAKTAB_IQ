"""DEPUTY_DIRECTOR: every capability the role must (and must not) have, checked on the backend.

The deputy oversees the learning process of ONE school: it reads students, teachers, classes,
subjects, grades, attendance (pupils and teachers), homework, the timetable and the reports,
and it manages the timetable. It writes nothing else and administrates nothing — that is the
admin's job. The requested capabilities are enforced by existing permission codenames (see
``SPEC_TO_CODENAME``); no new permission was necessary.

Only the deputy is exercised here; other roles are covered by ``test_rbac``.
"""

from django.test import SimpleTestCase

from apps.assignments.models import AssignmentSubmission
from apps.attendance.models import TeacherAttendance
from apps.grades.models import Grade
from apps.lessons.models import Lesson
from common import rbac

from .test_rbac import PASSWORD, R, SchoolWorld

# requested capability -> the codename that enforces it in this project
SPEC_TO_CODENAME = {
    # students
    "view_students": "view_all_students",
    "view_student_profile": "view_all_students",
    "view_student_grades": "view_all_grades",
    "view_student_attendance": "view_all_attendance",
    "view_student_homework": "view_all_homework",
    "view_student_class": "view_all_classes",
    # teachers
    "view_teachers": "view_all_teachers",
    "view_teacher_profile": "view_all_teachers",
    "view_teacher_subjects": "view_all_subjects",
    "view_teacher_classes": "view_all_classes",
    "view_teacher_schedule": "view_all_schedule",
    "view_teacher_attendance": "view_all_attendance",
    # classes
    "view_classes": "view_all_classes",
    "view_class_students": "view_class_students",
    "view_class_teachers": "view_class_teachers",
    "view_class_subjects": "view_all_subjects",
    "view_class_schedule": "view_all_schedule",
    "view_class_attendance": "view_all_attendance",
    # grades / attendance / homework
    "view_grades": "view_all_grades",
    "view_grade_reports": "view_reports",
    "view_student_grade_history": "view_all_grades",
    "view_attendance": "view_all_attendance",
    "view_attendance_reports": "view_reports",
    "view_homework": "view_all_homework",
    "view_class_homework": "view_all_homework",
    "view_homework_reports": "view_reports",
    # schedule (update_schedule is part of manage_schedule)
    "view_schedule": "view_all_schedule",
    "view_subject_schedule": "view_all_schedule",
    "manage_schedule": "manage_schedule",
    "update_schedule": "manage_schedule",
    # reports
    "view_student_reports": "view_reports",
    "view_teacher_reports": "view_reports",
    "view_class_reports": "view_class_reports",
    "view_academic_reports": "view_reports",
}

# what the deputy must never hold (admin / technical / write permissions)
NOT_FOR_DEPUTY = {
    "manage_users", "manage_roles", "manage_permissions", "manage_school_settings",
    "manage_students", "manage_teachers", "manage_classes", "manage_subjects",
    "create_grade", "update_grade", "delete_grade",
    "mark_attendance", "update_attendance", "mark_teacher_attendance", "manage_class_attendance",
    "create_homework", "update_homework", "delete_homework", "grade_submissions",
    "manage_quizzes", "manage_academic_records", "manage_library", "manage_helpdesk",
    "send_announcements", "moderate_chat", "transfer_students", "view_sensitive_student_data",
}


class DeputyPermissionSetTests(SimpleTestCase):
    def test_every_requested_capability_is_covered_by_an_existing_codename(self):
        deputy = rbac.ROLE_PERMISSIONS[rbac.DEPUTY_DIRECTOR]
        for wanted, codename in SPEC_TO_CODENAME.items():
            with self.subTest(wanted=wanted):
                self.assertIn(codename, rbac.PERMISSIONS)  # nothing invented
                self.assertIn(codename, deputy)

    def test_deputy_holds_no_administrative_or_write_permission(self):
        self.assertEqual(rbac.ROLE_PERMISSIONS[rbac.DEPUTY_DIRECTOR] & NOT_FOR_DEPUTY, set())

    def test_the_deputy_set_is_exactly_this(self):
        self.assertEqual(
            rbac.ROLE_PERMISSIONS[rbac.DEPUTY_DIRECTOR],
            {
                # everybody
                "view_own_profile", "view_announcements", "use_chat", "view_library",
                # the whole school, read-only
                "view_all_students", "view_all_teachers", "view_all_classes", "view_all_subjects",
                "view_all_grades", "view_all_attendance", "view_all_homework", "view_all_quizzes",
                "view_all_schedule", "view_all_announcements", "view_reports",
                "view_class_students", "view_class_teachers", "view_class_reports",
                # the one thing it may change
                "manage_schedule",
            },
        )


class DeputyWorld(SchoolWorld):
    """SchoolWorld + a teacher, lessons, grades, attendance and homework in school B, so that
    every 'own school only' assertion has something to leak."""

    def setUp(self):
        super().setUp()
        self.tb_user, self.tb = self.make_teacher("t_b", self.school_b, "T-B", [self.math])
        self.lesson_x = Lesson.objects.create(
            class_room=self.class_x, subject=self.math, teacher=self.tb,
            room="1", date="2026-09-15", start_time="09:00", end_time="09:45",
        )
        self.grade_4 = Grade.objects.create(
            student=self.s4, subject=self.math, teacher=self.tb,
            academic_year=self.year, quarter=self.quarter, value=5,
        )
        self.ta_a = TeacherAttendance.objects.create(teacher=self.t1, date="2026-09-15", status="PRESENT")
        self.ta_b = TeacherAttendance.objects.create(teacher=self.tb, date="2026-09-15", status="ABSENT")
        self.sub_a = AssignmentSubmission.objects.create(assignment=self.hw_a, student=self.s1, answer="a")
        self.deputy_b = self.make_user("deputy_b", R.DEPUTY_DIRECTOR, self.school_b)
        self.as_user(self.deputy)

    def get(self, url):
        return self.client.get(f"/api/v1/{url}")


class DeputyReadsTheSchool(DeputyWorld):
    def test_students(self):
        self.assertEqual(sorted(self.ids(self.get("students/"))), sorted([self.s1.id, self.s2.id, self.s3.id]))
        profile = self.get(f"students/{self.s1.id}/")
        self.assertEqual(profile.status_code, 200)
        self.assertEqual(profile.data["class_room_name"], "9-A")  # the pupil's class
        self.assertNotIn("passport_number", profile.data)  # sensitive data stays with the admin
        self.assertEqual(self.get("students/health-records/").status_code, 403)
        self.assertEqual(self.ids(self.get("students/documents/")), [])

    def test_student_grades_attendance_and_homework(self):
        self.assertEqual(sorted(self.ids(self.get("grades/"))), sorted([self.grade_1.id, self.grade_3.id]))
        self.assertEqual(self.ids(self.get(f"grades/?student={self.s1.id}")), [self.grade_1.id])
        self.assertEqual(self.get(f"grades/annual/?student={self.s1.id}&academic_year={self.year.id}").status_code, 200)
        self.assertEqual(sorted(self.ids(self.get("attendance/"))), sorted([self.att_1.id, self.att_3.id]))
        self.assertEqual(self.get(f"attendance/calendar/?student={self.s1.id}&month=9&year=2026").status_code, 200)
        self.assertEqual(sorted(self.ids(self.get("assignments/"))), sorted([self.hw_a.id, self.hw_b.id]))
        self.assertEqual(self.ids(self.get("submissions/")), [self.sub_a.id])

    def test_teachers(self):
        self.assertEqual(sorted(self.ids(self.get("teachers/"))), sorted([self.t1.id, self.t2.id, self.t3.id]))
        profile = self.get(f"teachers/{self.t1.id}/")
        self.assertEqual(profile.status_code, 200)
        self.assertEqual(profile.data["subjects"], [self.math.id])  # subject <-> teacher link
        self.assertEqual(self.ids(self.get(f"lessons/?teacher={self.t1.id}")), [self.lesson_a.id])  # teacher schedule
        self.assertEqual(self.ids(self.get("attendance/teacher-attendance/")), [self.ta_a.id])  # teachers' work attendance
        self.assertEqual(self.ids(self.get(f"attendance/teacher-attendance/?teacher={self.t1.id}")), [self.ta_a.id])

    def test_classes(self):
        self.assertEqual(sorted(self.ids(self.get("classes/"))), sorted([self.class_a.id, self.class_b.id]))
        detail = self.get(f"classes/{self.class_a.id}/")
        self.assertEqual((detail.status_code, detail.data["curator_name"] is not None), (200, True))
        self.assertEqual(sorted(self.ids(self.get(f"students/?class_room={self.class_a.id}"))), sorted([self.s1.id, self.s2.id]))
        lessons = self.get(f"lessons/?class_room={self.class_a.id}")
        self.assertEqual([lesson["teacher_name"] for lesson in lessons.data["results"]], [self.t1_user.get_full_name()])
        self.assertEqual(self.ids(self.get(f"attendance/?class_room={self.class_a.id}")), [self.att_1.id])
        self.assertEqual(len(self.ids(self.get("subjects/"))), 2)

    def test_timetable_filters(self):
        self.assertEqual(sorted(self.ids(self.get("lessons/"))), sorted([self.lesson_a.id, self.lesson_b.id]))
        self.assertEqual(self.ids(self.get(f"lessons/?subject={self.physics.id}")), [self.lesson_b.id])

    def test_reports(self):
        self.assertEqual(self.get("analytics/admin/").status_code, 200)
        self.assertEqual(self.get(f"analytics/class/?class_room={self.class_a.id}").status_code, 200)
        self.assertEqual(self.get(f"analytics/progress/?student={self.s1.id}").status_code, 200)

    def test_own_payload_lists_the_role_and_its_permissions(self):
        me = self.get("users/me/").data
        self.assertEqual(me["roles"], ["DEPUTY_DIRECTOR"])
        self.assertEqual(set(me["permissions"]), rbac.ROLE_PERMISSIONS[rbac.DEPUTY_DIRECTOR])


class DeputyStaysInsideOwnSchool(DeputyWorld):
    def test_school_a_deputy_cannot_reach_school_b(self):
        self.assertNotIn(self.s4.id, self.ids(self.get("students/")))
        self.assertNotIn(self.tb.id, self.ids(self.get("teachers/")))
        self.assertNotIn(self.class_x.id, self.ids(self.get("classes/")))
        self.assertNotIn(self.grade_4.id, self.ids(self.get("grades/")))
        self.assertNotIn(self.ta_b.id, self.ids(self.get("attendance/teacher-attendance/")))
        self.assertNotIn(self.lesson_x.id, self.ids(self.get("lessons/")))
        for url in [
            f"students/{self.s4.id}/",
            f"teachers/{self.tb.id}/",
            f"classes/{self.class_x.id}/",
            f"grades/?student={self.s4.id}",
            f"attendance/?student={self.s4.id}",
            f"attendance/calendar/?student={self.s4.id}&month=9&year=2026",
            f"analytics/progress/?student={self.s4.id}",
            f"analytics/class/?class_room={self.class_x.id}",
        ]:
            with self.subTest(url=url):
                self.assertEqual(self.get(url).status_code, 403)

    def test_school_b_deputy_sees_only_school_b(self):
        self.as_user(self.deputy_b)
        self.assertEqual(self.ids(self.get("students/")), [self.s4.id])
        self.assertEqual(self.ids(self.get("teachers/")), [self.tb.id])
        self.assertEqual(self.ids(self.get("classes/")), [self.class_x.id])
        self.assertEqual(self.ids(self.get("lessons/")), [self.lesson_x.id])
        self.assertEqual(self.get(f"students/{self.s1.id}/").status_code, 403)
        self.assertEqual(self.get(f"teachers/{self.t1.id}/").status_code, 403)

    def test_cannot_schedule_lessons_in_another_school(self):
        lesson = {
            "class_room": self.class_x.id, "subject": self.math.id, "teacher": self.tb.id,
            "room": "9", "date": "2026-09-22", "start_time": "10:00", "end_time": "10:45",
        }
        self.assertEqual(self.client.post("/api/v1/lessons/", lesson).status_code, 403)
        self.assertEqual(self.client.patch(f"/api/v1/lessons/{self.lesson_x.id}/", {"room": "2"}).status_code, 403)
        self.assertEqual(self.client.delete(f"/api/v1/lessons/{self.lesson_x.id}/").status_code, 403)


class DeputyManagesOnlyTheTimetable(DeputyWorld):
    def test_creates_updates_and_deletes_lessons(self):
        lesson = {
            "class_room": self.class_a.id, "subject": self.math.id, "teacher": self.t1.id,
            "room": "201", "date": "2026-09-20", "start_time": "11:00", "end_time": "11:45",
        }
        created = self.client.post("/api/v1/lessons/", lesson)
        self.assertEqual(created.status_code, 201)
        url = f"/api/v1/lessons/{created.data['id']}/"
        self.assertEqual(self.client.patch(url, {"room": "202"}).status_code, 200)
        self.assertEqual(self.client.delete(url).status_code, 204)

    def test_grades_are_read_only(self):
        self.assertEqual(self.client.post("/api/v1/grades/", self.grade_payload(self.s1, self.math)).status_code, 403)
        self.assertEqual(self.client.patch(f"/api/v1/grades/{self.grade_1.id}/", {"value": 2}).status_code, 403)
        self.assertEqual(self.client.delete(f"/api/v1/grades/{self.grade_1.id}/").status_code, 403)
        self.assertEqual(Grade.objects.get(pk=self.grade_1.id).value, 8)

    def test_attendance_is_read_only_and_cannot_be_corrected(self):
        record = {"student": self.s1.id, "class_room": self.class_a.id, "date": "2026-09-16", "status": "ABSENT"}
        self.assertEqual(self.client.post("/api/v1/attendance/", record).status_code, 403)
        self.assertEqual(self.client.patch(f"/api/v1/attendance/{self.att_1.id}/", {"status": "ABSENT"}).status_code, 403)
        self.assertEqual(self.client.delete(f"/api/v1/attendance/{self.att_1.id}/").status_code, 403)
        teacher_record = {"teacher": self.t1.id, "date": "2026-09-16", "status": "ABSENT"}
        self.assertEqual(self.client.post("/api/v1/attendance/teacher-attendance/", teacher_record).status_code, 403)
        self.assertEqual(self.client.patch(f"/api/v1/attendance/teacher-attendance/{self.ta_a.id}/", {"status": "ABSENT"}).status_code, 403)

    def test_homework_is_read_only_and_teachers_keep_theirs(self):
        homework = {"lesson": self.lesson_a.id, "title": "Yangi", "deadline": "2026-12-01T10:00:00Z"}
        self.assertEqual(self.client.post("/api/v1/assignments/", homework).status_code, 403)
        self.assertEqual(self.client.delete(f"/api/v1/assignments/{self.hw_a.id}/").status_code, 403)
        self.assertEqual(self.client.post(f"/api/v1/submissions/{self.sub_a.id}/grade/", {"score": 90}).status_code, 403)
        # ...and giving a deputy to the school changed nothing for the teacher who owns the lesson
        self.as_user(self.t1_user)
        self.assertEqual(self.client.post("/api/v1/assignments/", homework).status_code, 201)


class DeputyIsNotAnAdmin(DeputyWorld):
    def test_no_user_role_permission_or_authentication_management(self):
        teacher, student = self.t1_user.id, self.s1_user.id
        checks = [
            ("get", "users/", None),
            ("get", "roles/", None),
            ("get", "permissions/", None),
            ("post", f"users/{teacher}/roles/", {"role": "ADMIN"}),
            ("post", f"users/{teacher}/permissions/", {"permission": "create_grade"}),
            ("delete", f"users/{teacher}/roles/TEACHER/", None),
            ("post", f"auth/users/{teacher}/deactivate/", None),
            ("post", f"auth/users/{teacher}/activate/", None),
            ("post", f"auth/users/{student}/reset-password/", {"new_password": "Str0ngPass!99"}),
            ("post", "auth/register/student/", {"username": "n", "password": PASSWORD, "student_code": "S-9"}),
            ("patch", f"schools/{self.school_a.id}/", {"name": "Renamed"}),
        ]
        for method, url, body in checks:
            with self.subTest(url=url):
                response = getattr(self.client, method)(f"/api/v1/{url}", body) if body else getattr(self.client, method)(f"/api/v1/{url}")
                self.assertEqual(response.status_code, 403)

    def test_cannot_create_delete_or_edit_students_teachers_classes_or_subjects(self):
        checks = [
            ("patch", f"students/{self.s1.id}/", {"age": 12}),
            ("delete", f"students/{self.s1.id}/", None),
            ("post", f"students/{self.s1.id}/transfer/", {"new_class": self.class_b.id}),
            ("patch", f"teachers/{self.t1.id}/", {"experience_years": 9}),
            ("delete", f"teachers/{self.t1.id}/", None),
            ("post", "classes/", {"school": self.school_a.id, "name": "10-A", "grade": 10, "academic_year": self.year.id}),
            ("delete", f"classes/{self.class_a.id}/", None),
            ("post", "subjects/", {"name": "Kimyo"}),
            ("post", "notifications/announcements/", {"title": "x", "content": "y", "target": "ALL"}),
        ]
        for method, url, body in checks:
            with self.subTest(url=url):
                response = getattr(self.client, method)(f"/api/v1/{url}", body) if body else getattr(self.client, method)(f"/api/v1/{url}")
                self.assertEqual(response.status_code, 403)

    def test_anonymous_requests_get_401(self):
        self.client.force_authenticate(None)
        for url in ["students/", "teachers/", "classes/", "grades/", "attendance/teacher-attendance/", "analytics/admin/"]:
            with self.subTest(url=url):
                self.assertEqual(self.get(url).status_code, 401)
