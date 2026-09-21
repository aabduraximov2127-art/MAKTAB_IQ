from rest_framework import status
from rest_framework.test import APITestCase

from apps.classes.models import AcademicYear, ClassRoom
from apps.schools.models import School
from apps.subjects.models import Subject
from apps.users.models import ParentProfile, ParentStudent, StudentProfile, TeacherProfile, User

from .models import Attendance, AttendanceStatus, TeacherAttendance


class AttendancePermissionTests(APITestCase):
    def setUp(self):
        self.school = School.objects.create(name="School #1")
        self.academic_year = AcademicYear.objects.create(
            name="2026-2027", start_date="2026-09-01", end_date="2027-05-31", is_active=True
        )
        self.class_a = ClassRoom.objects.create(
            school=self.school, name="9-A", grade=9, academic_year=self.academic_year
        )

        self.teacher_user = User.objects.create_user(
            username="teacher1", password="Str0ngPass!23", role=User.Role.TEACHER
        )
        self.teacher = TeacherProfile.objects.create(user=self.teacher_user, teacher_id="T-0001")

        self.student1_user = User.objects.create_user(
            username="student1", password="Str0ngPass!23", role=User.Role.STUDENT
        )
        self.student1 = StudentProfile.objects.create(
            user=self.student1_user, school=self.school, class_room=self.class_a, student_code="S-0001"
        )
        self.student2_user = User.objects.create_user(
            username="student2", password="Str0ngPass!23", role=User.Role.STUDENT
        )
        self.student2 = StudentProfile.objects.create(
            user=self.student2_user, school=self.school, class_room=self.class_a, student_code="S-0002"
        )

        self.parent_user = User.objects.create_user(
            username="parent1", password="Str0ngPass!23", role=User.Role.PARENT
        )
        self.parent = ParentProfile.objects.create(user=self.parent_user)
        ParentStudent.objects.create(parent=self.parent, student=self.student1)

        self.attendance1 = Attendance.objects.create(
            student=self.student1,
            class_room=self.class_a,
            date="2026-09-15",
            status=AttendanceStatus.ABSENT,
            marked_by=self.teacher,
        )
        self.attendance2 = Attendance.objects.create(
            student=self.student2,
            class_room=self.class_a,
            date="2026-09-15",
            status=AttendanceStatus.PRESENT,
            marked_by=self.teacher,
        )

    def test_parent_cannot_see_other_students_attendance(self):
        self.client.force_authenticate(self.parent_user)
        response = self.client.get("/api/v1/attendance/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        student_ids = [a["student"] for a in response.data["results"]]
        self.assertIn(self.student1.id, student_ids)
        self.assertNotIn(self.student2.id, student_ids)

    def test_parent_can_submit_absence_reason(self):
        self.client.force_authenticate(self.parent_user)
        url = f"/api/v1/attendance/{self.attendance1.id}/submit_reason/"
        response = self.client.patch(url, {"parent_reason": "Farzandim kasal edi."})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.attendance1.refresh_from_db()
        self.assertEqual(self.attendance1.parent_reason, "Farzandim kasal edi.")

    def test_parent_cannot_submit_reason_for_other_student(self):
        self.client.force_authenticate(self.parent_user)
        url = f"/api/v1/attendance/{self.attendance2.id}/submit_reason/"
        response = self.client.patch(url, {"parent_reason": "..."})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_student_cannot_mark_attendance(self):
        self.client.force_authenticate(self.student1_user)
        response = self.client.post(
            "/api/v1/attendance/",
            {"student": self.student2.id, "class_room": self.class_a.id, "date": "2026-09-16", "status": "PRESENT"},
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_student_cannot_update_own_attendance(self):
        self.client.force_authenticate(self.student1_user)
        response = self.client.patch(f"/api/v1/attendance/{self.attendance1.id}/", {"status": "PRESENT"})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.attendance1.refresh_from_db()
        self.assertEqual(self.attendance1.status, AttendanceStatus.ABSENT)

    def test_student_cannot_see_other_students_attendance(self):
        self.client.force_authenticate(self.student1_user)
        response = self.client.get("/api/v1/attendance/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        student_ids = [a["student"] for a in response.data["results"]]
        self.assertIn(self.student1.id, student_ids)
        self.assertNotIn(self.student2.id, student_ids)

    def test_superadmin_has_no_attendance_access(self):
        superadmin = User.objects.create_user(
            username="superadmin1", password="Str0ngPass!23", role=User.Role.SUPERADMIN
        )
        self.client.force_authenticate(superadmin)

        list_response = self.client.get("/api/v1/attendance/")
        self.assertEqual(list_response.status_code, status.HTTP_403_FORBIDDEN)

        create_response = self.client.post(
            "/api/v1/attendance/",
            {"student": self.student1.id, "class_room": self.class_a.id, "date": "2026-09-17", "status": "PRESENT"},
        )
        self.assertEqual(create_response.status_code, status.HTTP_403_FORBIDDEN)

        teacher_attendance_response = self.client.get("/api/v1/attendance/teacher-attendance/")
        self.assertEqual(teacher_attendance_response.status_code, status.HTTP_403_FORBIDDEN)

    def test_teacher_cannot_mark_own_attendance_only_admin_can(self):
        admin = User.objects.create_user(username="admin1", password="Str0ngPass!23", role=User.Role.ADMIN)

        self.client.force_authenticate(self.teacher_user)
        response = self.client.post(
            "/api/v1/attendance/teacher-attendance/",
            {"teacher": self.teacher.id, "date": "2026-09-17", "status": "PRESENT"},
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_authenticate(admin)
        response = self.client.post(
            "/api/v1/attendance/teacher-attendance/",
            {"teacher": self.teacher.id, "date": "2026-09-17", "status": "ABSENT"},
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_teacher_absence_triggers_notification(self):
        from apps.notifications.models import Notification

        admin = User.objects.create_user(username="admin2", password="Str0ngPass!23", role=User.Role.ADMIN)
        self.client.force_authenticate(admin)
        response = self.client.post(
            "/api/v1/attendance/teacher-attendance/",
            {"teacher": self.teacher.id, "date": "2026-09-18", "status": "ABSENT"},
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Notification.objects.filter(user=self.teacher_user).exists())


class SchoolAdminAttendanceScopingTests(APITestCase):
    def setUp(self):
        self.school_a = School.objects.create(name="School A")
        self.school_b = School.objects.create(name="School B")
        self.academic_year = AcademicYear.objects.create(
            name="2026-2027", start_date="2026-09-01", end_date="2027-05-31", is_active=True
        )
        self.class_a = ClassRoom.objects.create(
            school=self.school_a, name="9-A", grade=9, academic_year=self.academic_year
        )
        self.class_b = ClassRoom.objects.create(
            school=self.school_b, name="9-A", grade=9, academic_year=self.academic_year
        )
        self.subject = Subject.objects.create(name="Matematika")
        self.admin_a = User.objects.create_user(
            username="admin_a", password="Str0ngPass!23", role=User.Role.ADMIN, school=self.school_a
        )

        self.teacher_a_user = User.objects.create_user(
            username="teacher_a", password="Str0ngPass!23", role=User.Role.TEACHER, school=self.school_a
        )
        self.teacher_a = TeacherProfile.objects.create(
            user=self.teacher_a_user, school=self.school_a, teacher_id="TA-0001"
        )
        self.teacher_b_user = User.objects.create_user(
            username="teacher_b", password="Str0ngPass!23", role=User.Role.TEACHER, school=self.school_b
        )
        self.teacher_b = TeacherProfile.objects.create(
            user=self.teacher_b_user, school=self.school_b, teacher_id="TB-0001"
        )

        self.student_a_user = User.objects.create_user(
            username="student_a", password="Str0ngPass!23", role=User.Role.STUDENT, school=self.school_a
        )
        self.student_a = StudentProfile.objects.create(
            user=self.student_a_user, school=self.school_a, class_room=self.class_a, student_code="A-0001"
        )
        self.student_b_user = User.objects.create_user(
            username="student_b", password="Str0ngPass!23", role=User.Role.STUDENT, school=self.school_b
        )
        self.student_b = StudentProfile.objects.create(
            user=self.student_b_user, school=self.school_b, class_room=self.class_b, student_code="B-0001"
        )

        self.attendance_a = Attendance.objects.create(
            student=self.student_a, class_room=self.class_a, date="2026-09-15", status=AttendanceStatus.PRESENT
        )
        self.attendance_b = Attendance.objects.create(
            student=self.student_b, class_room=self.class_b, date="2026-09-15", status=AttendanceStatus.PRESENT
        )

    def test_admin_sees_only_own_school_attendance(self):
        self.client.force_authenticate(self.admin_a)
        response = self.client.get("/api/v1/attendance/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        student_ids = [a["student"] for a in response.data["results"]]
        self.assertIn(self.student_a.id, student_ids)
        self.assertNotIn(self.student_b.id, student_ids)

    def test_admin_cannot_mark_attendance_for_other_school_class(self):
        self.client.force_authenticate(self.admin_a)
        response = self.client.post(
            "/api/v1/attendance/",
            {
                "student": self.student_b.id,
                "class_room": self.class_b.id,
                "subject": self.subject.id,
                "date": "2026-09-16",
                "status": "PRESENT",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_cannot_update_other_school_attendance(self):
        self.client.force_authenticate(self.admin_a)
        response = self.client.patch(f"/api/v1/attendance/{self.attendance_b.id}/", {"status": "ABSENT"})
        self.assertIn(response.status_code, (403, 404))

    def test_admin_sees_only_own_school_teacher_attendance(self):
        TeacherAttendance.objects.create(teacher=self.teacher_a, date="2026-09-15", status=AttendanceStatus.PRESENT)
        TeacherAttendance.objects.create(teacher=self.teacher_b, date="2026-09-15", status=AttendanceStatus.PRESENT)

        self.client.force_authenticate(self.admin_a)
        response = self.client.get("/api/v1/attendance/teacher-attendance/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        teacher_ids = [a["teacher"] for a in response.data["results"]]
        self.assertIn(self.teacher_a.id, teacher_ids)
        self.assertNotIn(self.teacher_b.id, teacher_ids)

    def test_admin_cannot_mark_other_school_teacher_attendance(self):
        self.client.force_authenticate(self.admin_a)
        response = self.client.post(
            "/api/v1/attendance/teacher-attendance/",
            {"teacher": self.teacher_b.id, "date": "2026-09-17", "status": "ABSENT"},
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
