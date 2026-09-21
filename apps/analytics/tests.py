from rest_framework import status
from rest_framework.test import APITestCase

from apps.classes.models import AcademicYear, ClassRoom, Quarter
from apps.grades.models import Grade
from apps.schools.models import School
from apps.subjects.models import Subject
from apps.users.models import StudentProfile, User


class StudentProgressTests(APITestCase):
    def setUp(self):
        self.school = School.objects.create(name="School #1")
        self.academic_year = AcademicYear.objects.create(
            name="2026-2027", start_date="2026-09-01", end_date="2027-05-31", is_active=True
        )
        self.quarter = Quarter.objects.create(
            academic_year=self.academic_year, number=1, start_date="2026-09-01", end_date="2026-10-30"
        )
        self.class_a = ClassRoom.objects.create(
            school=self.school, name="9-A", grade=9, academic_year=self.academic_year
        )
        self.subject = Subject.objects.create(name="Matematika")

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

        Grade.objects.create(
            student=self.student1,
            subject=self.subject,
            academic_year=self.academic_year,
            quarter=self.quarter,
            value=9,
        )

    def test_student_sees_own_progress(self):
        self.client.force_authenticate(self.student1_user)
        response = self.client.get("/api/v1/analytics/progress/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["average_grade"], 9)

    def test_student_cannot_see_other_students_progress(self):
        self.client.force_authenticate(self.student1_user)
        response = self.client.get(f"/api/v1/analytics/progress/?student={self.student2.id}")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_analytics_requires_admin(self):
        self.client.force_authenticate(self.student1_user)
        response = self.client.get("/api/v1/analytics/admin/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
