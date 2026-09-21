from rest_framework import status
from rest_framework.test import APITestCase

from apps.classes.models import AcademicYear, ClassRoom
from apps.schools.models import School
from apps.subjects.models import Subject
from apps.users.models import TeacherProfile, User

from .models import Lesson


class LessonConflictTests(APITestCase):
    def setUp(self):
        self.school = School.objects.create(name="School #1")
        self.academic_year = AcademicYear.objects.create(
            name="2026-2027", start_date="2026-09-01", end_date="2027-05-31", is_active=True
        )
        self.class_a = ClassRoom.objects.create(
            school=self.school, name="9-A", grade=9, academic_year=self.academic_year
        )
        self.class_b = ClassRoom.objects.create(
            school=self.school, name="9-B", grade=9, academic_year=self.academic_year
        )
        self.subject = Subject.objects.create(name="Matematika")

        self.admin = User.objects.create_user(
            username="admin", password="Str0ngPass!23", role=User.Role.ADMIN, school=self.school
        )

        self.teacher_user = User.objects.create_user(
            username="teacher1", password="Str0ngPass!23", role=User.Role.TEACHER
        )
        self.teacher = TeacherProfile.objects.create(user=self.teacher_user, teacher_id="T-0001")

        Lesson.objects.create(
            class_room=self.class_a,
            subject=self.subject,
            teacher=self.teacher,
            room="101",
            date="2026-09-15",
            start_time="09:00",
            end_time="09:45",
        )

    def test_teacher_double_booking_rejected(self):
        self.client.force_authenticate(self.admin)
        response = self.client.post(
            "/api/v1/lessons/",
            {
                "class_room": self.class_b.id,
                "subject": self.subject.id,
                "teacher": self.teacher.id,
                "room": "202",
                "date": "2026-09-15",
                "start_time": "09:15",
                "end_time": "10:00",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_room_double_booking_rejected(self):
        other_teacher_user = User.objects.create_user(
            username="teacher2", password="Str0ngPass!23", role=User.Role.TEACHER
        )
        other_teacher = TeacherProfile.objects.create(user=other_teacher_user, teacher_id="T-0002")

        self.client.force_authenticate(self.admin)
        response = self.client.post(
            "/api/v1/lessons/",
            {
                "class_room": self.class_b.id,
                "subject": self.subject.id,
                "teacher": other_teacher.id,
                "room": "101",
                "date": "2026-09-15",
                "start_time": "09:15",
                "end_time": "10:00",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_non_conflicting_lesson_created(self):
        self.client.force_authenticate(self.admin)
        response = self.client.post(
            "/api/v1/lessons/",
            {
                "class_room": self.class_b.id,
                "subject": self.subject.id,
                "teacher": self.teacher.id,
                "room": "202",
                "date": "2026-09-15",
                "start_time": "10:00",
                "end_time": "10:45",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
