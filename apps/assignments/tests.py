from rest_framework import status
from rest_framework.test import APITestCase

from apps.classes.models import AcademicYear, ClassRoom
from apps.lessons.models import Lesson
from apps.schools.models import School
from apps.subjects.models import Subject
from apps.users.models import StudentProfile, TeacherProfile, User

from .models import Assignment, AssignmentSubmission


class AssignmentSubmissionTests(APITestCase):
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

        self.lesson = Lesson.objects.create(
            class_room=self.class_a,
            subject=self.subject,
            teacher=self.teacher,
            room="101",
            date="2026-09-15",
            start_time="09:00",
            end_time="09:45",
        )
        self.assignment = Assignment.objects.create(
            lesson=self.lesson, teacher=self.teacher, title="Uy vazifa 1", deadline="2026-12-31T23:59:00Z"
        )

        self.student_user = User.objects.create_user(
            username="student1", password="Str0ngPass!23", role=User.Role.STUDENT
        )
        self.student = StudentProfile.objects.create(
            user=self.student_user, school=self.school, class_room=self.class_a, student_code="S-0001"
        )

    def test_student_can_submit_assignment(self):
        self.client.force_authenticate(self.student_user)
        url = f"/api/v1/assignments/{self.assignment.id}/submit/"
        response = self.client.post(url, {"answer": "Mening javobim"})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(AssignmentSubmission.objects.count(), 1)

    def test_teacher_cannot_submit_assignment(self):
        self.client.force_authenticate(self.teacher_user)
        url = f"/api/v1/assignments/{self.assignment.id}/submit/"
        response = self.client.post(url, {"answer": "..."})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_teacher_can_grade_submission(self):
        submission = AssignmentSubmission.objects.create(
            assignment=self.assignment, student=self.student, answer="javob"
        )
        self.client.force_authenticate(self.teacher_user)
        url = f"/api/v1/submissions/{submission.id}/grade/"
        response = self.client.post(url, {"score": 90})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        submission.refresh_from_db()
        self.assertEqual(submission.score, 90)
        self.assertEqual(submission.status, AssignmentSubmission.Status.GRADED)

    def test_superadmin_cannot_see_homework(self):
        superadmin = User.objects.create_user(
            username="superadmin1", password="Str0ngPass!23", role=User.Role.SUPERADMIN
        )
        self.client.force_authenticate(superadmin)
        response = self.client.get("/api/v1/assignments/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_student_does_not_see_other_classes_homework(self):
        other_class = ClassRoom.objects.create(
            school=self.school, name="9-B", grade=9, academic_year=self.academic_year
        )
        other_lesson = Lesson.objects.create(
            class_room=other_class,
            subject=self.subject,
            teacher=self.teacher,
            room="102",
            date="2026-09-15",
            start_time="10:00",
            end_time="10:45",
        )
        other_assignment = Assignment.objects.create(
            lesson=other_lesson, teacher=self.teacher, title="Boshqa klass uy vazifasi", deadline="2026-12-31T23:59:00Z"
        )
        self.client.force_authenticate(self.student_user)
        response = self.client.get("/api/v1/assignments/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = [a["id"] for a in response.data["results"]]
        self.assertIn(self.assignment.id, ids)
        self.assertNotIn(other_assignment.id, ids)

    def test_student_cannot_see_other_students_submission(self):
        other_student_user = User.objects.create_user(
            username="student2", password="Str0ngPass!23", role=User.Role.STUDENT
        )
        other_student = StudentProfile.objects.create(
            user=other_student_user, school=self.school, class_room=self.class_a, student_code="S-0002"
        )
        other_submission = AssignmentSubmission.objects.create(
            assignment=self.assignment, student=other_student, answer="boshqa javob"
        )
        self.client.force_authenticate(self.student_user)
        response = self.client.get(f"/api/v1/submissions/{other_submission.id}/")
        # Someone else's object: refused (403), not disguised as "not found".
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
