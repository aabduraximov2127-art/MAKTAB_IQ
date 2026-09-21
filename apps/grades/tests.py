from rest_framework import status
from rest_framework.test import APITestCase

from apps.classes.models import AcademicYear, ClassRoom, Quarter
from apps.schools.models import School
from apps.subjects.models import Subject
from apps.users.models import StudentProfile, TeacherProfile, User

from .models import Grade


class GradePermissionTests(APITestCase):
    def setUp(self):
        self.school = School.objects.create(name="School #1")
        self.academic_year = AcademicYear.objects.create(
            name="2026-2027", start_date="2026-09-01", end_date="2027-05-31", is_active=True
        )
        self.quarter1 = Quarter.objects.create(
            academic_year=self.academic_year, number=1, start_date="2026-09-01", end_date="2026-10-30"
        )
        self.class_a = ClassRoom.objects.create(
            school=self.school, name="9-A", grade=9, academic_year=self.academic_year
        )
        self.subject = Subject.objects.create(name="Matematika")

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

        self.grade1 = Grade.objects.create(
            student=self.student1,
            subject=self.subject,
            teacher=self.teacher,
            academic_year=self.academic_year,
            quarter=self.quarter1,
            value=8,
        )

    def test_teacher_can_create_grade(self):
        self.client.force_authenticate(self.teacher_user)
        response = self.client.post(
            "/api/v1/grades/",
            {
                "student": self.student2.id,
                "subject": self.subject.id,
                "academic_year": self.academic_year.id,
                "quarter": self.quarter1.id,
                "value": 9,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_student_cannot_see_other_students_grade(self):
        self.client.force_authenticate(self.student2_user)
        response = self.client.get("/api/v1/grades/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        student_ids = [g["student"] for g in response.data["results"]]
        self.assertNotIn(self.student1.id, student_ids)

    def test_student_cannot_create_grade(self):
        self.client.force_authenticate(self.student1_user)
        response = self.client.post(
            "/api/v1/grades/",
            {
                "student": self.student1.id,
                "subject": self.subject.id,
                "academic_year": self.academic_year.id,
                "quarter": self.quarter1.id,
                "value": 9,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_student_cannot_update_own_grade(self):
        self.client.force_authenticate(self.student1_user)
        response = self.client.patch(f"/api/v1/grades/{self.grade1.id}/", {"value": 10})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.grade1.refresh_from_db()
        self.assertEqual(self.grade1.value, 8)

    def test_student_cannot_delete_own_grade(self):
        self.client.force_authenticate(self.student1_user)
        response = self.client.delete(f"/api/v1/grades/{self.grade1.id}/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_student_cannot_fetch_other_students_annual_grades(self):
        self.client.force_authenticate(self.student2_user)
        response = self.client.get(
            f"/api/v1/grades/annual/?student={self.student1.id}&academic_year={self.academic_year.id}"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["results"], [])

    def test_superadmin_can_view_but_not_create_grade(self):
        superadmin = User.objects.create_user(
            username="superadmin1", password="Str0ngPass!23", role=User.Role.SUPERADMIN
        )
        self.client.force_authenticate(superadmin)

        list_response = self.client.get("/api/v1/grades/")
        self.assertEqual(list_response.status_code, status.HTTP_200_OK)

        create_response = self.client.post(
            "/api/v1/grades/",
            {
                "student": self.student1.id,
                "subject": self.subject.id,
                "academic_year": self.academic_year.id,
                "quarter": self.quarter1.id,
                "value": 9,
            },
        )
        self.assertEqual(create_response.status_code, status.HTTP_403_FORBIDDEN)

    def test_annual_average_calculation(self):
        Quarter.objects.filter(academic_year=self.academic_year).delete()
        q1 = Quarter.objects.create(
            academic_year=self.academic_year, number=1, start_date="2026-09-01", end_date="2026-10-30"
        )
        q2 = Quarter.objects.create(
            academic_year=self.academic_year, number=2, start_date="2026-11-01", end_date="2026-12-30"
        )
        q3 = Quarter.objects.create(
            academic_year=self.academic_year, number=3, start_date="2027-01-10", end_date="2027-03-15"
        )
        q4 = Quarter.objects.create(
            academic_year=self.academic_year, number=4, start_date="2027-03-20", end_date="2027-05-25"
        )
        Grade.objects.all().delete()
        for quarter, value in [(q1, 8), (q2, 9), (q3, 8), (q4, 10)]:
            Grade.objects.create(
                student=self.student1,
                subject=self.subject,
                teacher=self.teacher,
                academic_year=self.academic_year,
                quarter=quarter,
                value=value,
            )

        self.client.force_authenticate(self.teacher_user)
        response = self.client.get(
            f"/api/v1/grades/annual/?student={self.student1.id}&academic_year={self.academic_year.id}"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        result = response.data["results"][0]
        self.assertEqual(result["annual_average"], 8.75)


class SchoolAdminGradeScopingTests(APITestCase):
    def setUp(self):
        self.school_a = School.objects.create(name="School A")
        self.school_b = School.objects.create(name="School B")
        self.academic_year = AcademicYear.objects.create(
            name="2026-2027", start_date="2026-09-01", end_date="2027-05-31", is_active=True
        )
        self.quarter1 = Quarter.objects.create(
            academic_year=self.academic_year, number=1, start_date="2026-09-01", end_date="2026-10-30"
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

        self.grade_a = Grade.objects.create(
            student=self.student_a,
            subject=self.subject,
            teacher=self.teacher_a,
            academic_year=self.academic_year,
            quarter=self.quarter1,
            value=8,
        )
        self.grade_b = Grade.objects.create(
            student=self.student_b,
            subject=self.subject,
            academic_year=self.academic_year,
            quarter=self.quarter1,
            value=7,
        )

    def test_admin_sees_only_own_school_grades(self):
        self.client.force_authenticate(self.admin_a)
        response = self.client.get("/api/v1/grades/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        student_ids = [g["student"] for g in response.data["results"]]
        self.assertIn(self.student_a.id, student_ids)
        self.assertNotIn(self.student_b.id, student_ids)

    def test_admin_cannot_view_other_school_grade(self):
        # Cross-school access is excluded at the queryset level, so DRF's default
        # get_object() 404s before ever reaching object-level permission checks —
        # an acceptable "denied" per the school-object-security spec (403 or 404).
        self.client.force_authenticate(self.admin_a)
        response = self.client.get(f"/api/v1/grades/{self.grade_b.id}/")
        self.assertIn(response.status_code, (status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND))

    def test_admin_cannot_create_grade_for_other_school_student(self):
        self.client.force_authenticate(self.admin_a)
        response = self.client.post(
            "/api/v1/grades/",
            {
                "student": self.student_b.id,
                "subject": self.subject.id,
                "academic_year": self.academic_year.id,
                "quarter": self.quarter1.id,
                "value": 9,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_override_own_school_grade_with_audit_log(self):
        from common.models import AuditLog

        self.client.force_authenticate(self.admin_a)
        response = self.client.patch(f"/api/v1/grades/{self.grade_a.id}/", {"value": 10})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(AuditLog.objects.filter(action="GRADE_OVERRIDE", actor=self.admin_a).exists())
