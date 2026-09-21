from rest_framework import status
from rest_framework.test import APITestCase

from apps.users.models import User

from .models import Subject


class SubjectAPITests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_user(username="admin", password="Str0ngPass!23", role=User.Role.ADMIN)
        self.student = User.objects.create_user(username="student", password="Str0ngPass!23", role=User.Role.STUDENT)

    def test_admin_can_create_subject(self):
        self.client.force_authenticate(self.admin)
        response = self.client.post("/api/v1/subjects/", {"name": "Matematika"})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_student_can_list_subjects(self):
        Subject.objects.create(name="Fizika")
        self.client.force_authenticate(self.student)
        response = self.client.get("/api/v1/subjects/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_student_cannot_create_subject(self):
        self.client.force_authenticate(self.student)
        response = self.client.post("/api/v1/subjects/", {"name": "Kimyo"})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
