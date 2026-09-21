from rest_framework import status
from rest_framework.test import APITestCase

from apps.classes.models import AcademicYear, ClassRoom, Quarter
from apps.grades.models import Grade
from apps.schools.models import School
from apps.subjects.models import Subject
from apps.users.models import StudentProfile, User


class AIAssistantTests(APITestCase):
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
        self.subject = Subject.objects.create(name="Fizika")

        self.student_user = User.objects.create_user(
            username="student1", password="Str0ngPass!23", role=User.Role.STUDENT
        )
        self.student = StudentProfile.objects.create(
            user=self.student_user, school=self.school, class_room=self.class_a, student_code="S-0001"
        )
        Grade.objects.create(
            student=self.student, subject=self.subject, academic_year=self.academic_year, quarter=self.quarter, value=4
        )

    def test_student_can_ask_ai(self):
        self.client.force_authenticate(self.student_user)
        response = self.client.post("/api/v1/ai/ask/", {"question": "Nyuton qonunlari nima?"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("answer", response.data)

    def test_teacher_cannot_ask_ai(self):
        teacher_user = User.objects.create_user(username="t1", password="Str0ngPass!23", role=User.Role.TEACHER)
        self.client.force_authenticate(teacher_user)
        response = self.client.post("/api/v1/ai/ask/", {"question": "..."})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_weak_topics_detected(self):
        self.client.force_authenticate(self.student_user)
        response = self.client.get("/api/v1/ai/weak-topics/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["weak_topics"]), 1)
        self.assertEqual(response.data["weak_topics"][0]["subject_name"], "Fizika")
