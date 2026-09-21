from rest_framework import status
from rest_framework.test import APITestCase

from apps.classes.models import AcademicYear, ClassRoom
from apps.schools.models import School
from apps.subjects.models import Subject
from apps.users.models import StudentProfile, TeacherProfile, User

from .models import Question, Quiz


class QuizScoringTests(APITestCase):
    def setUp(self):
        self.school = School.objects.create(name="School #1")
        self.academic_year = AcademicYear.objects.create(
            name="2026-2027", start_date="2026-09-01", end_date="2027-05-31", is_active=True
        )
        self.class_a = ClassRoom.objects.create(
            school=self.school, name="9-A", grade=9, academic_year=self.academic_year
        )
        self.subject = Subject.objects.create(name="Matematika")

        self.teacher_user = User.objects.create_user(
            username="teacher1", password="Str0ngPass!23", role=User.Role.TEACHER
        )
        self.teacher = TeacherProfile.objects.create(user=self.teacher_user, teacher_id="T-0001")

        self.student_user = User.objects.create_user(
            username="student1", password="Str0ngPass!23", role=User.Role.STUDENT
        )
        self.student = StudentProfile.objects.create(
            user=self.student_user, school=self.school, class_room=self.class_a, student_code="S-0001"
        )

        self.quiz = Quiz.objects.create(
            title="Test 1",
            subject=self.subject,
            class_room=self.class_a,
            teacher=self.teacher,
            deadline="2026-12-31T23:59:00Z",
        )
        self.q1 = Question.objects.create(
            quiz=self.quiz, question="2+2=?", options=["3", "4", "5"], correct_answer=1, points=5
        )
        self.q2 = Question.objects.create(
            quiz=self.quiz, question="3+3=?", options=["6", "7", "8"], correct_answer=0, points=5
        )

    def test_student_correct_answer_calculates_score(self):
        self.client.force_authenticate(self.student_user)
        url = f"/api/v1/quizzes/{self.quiz.id}/submit/"
        response = self.client.post(
            url, {"answers": {str(self.q1.id): 1, str(self.q2.id): 2}}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["score"], 5)
        self.assertEqual(response.data["max_score"], 10)

    def test_correct_answer_hidden_from_student_view(self):
        self.client.force_authenticate(self.student_user)
        response = self.client.get(f"/api/v1/quizzes/{self.quiz.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotIn("correct_answer", response.data["questions"][0])

    def test_teacher_sees_correct_answer(self):
        self.client.force_authenticate(self.teacher_user)
        response = self.client.get(f"/api/v1/quizzes/{self.quiz.id}/")
        self.assertIn("correct_answer", response.data["questions"][0])

    def test_superadmin_cannot_see_quizzes(self):
        superadmin = User.objects.create_user(
            username="superadmin1", password="Str0ngPass!23", role=User.Role.SUPERADMIN
        )
        self.client.force_authenticate(superadmin)
        response = self.client.get("/api/v1/quizzes/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
