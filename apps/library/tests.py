from rest_framework import status
from rest_framework.test import APITestCase

from apps.users.models import User

from .models import LibraryMaterial


class LibraryMaterialAPITests(APITestCase):
    def setUp(self):
        self.teacher = User.objects.create_user(username="teacher", password="Str0ngPass!23", role=User.Role.TEACHER)
        self.student = User.objects.create_user(username="student", password="Str0ngPass!23", role=User.Role.STUDENT)

    def test_teacher_can_upload_material(self):
        self.client.force_authenticate(self.teacher)
        response = self.client.post(
            "/api/v1/library/", {"title": "Algebra kitobi", "material_type": "BOOK"}
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_student_can_view_but_not_upload(self):
        LibraryMaterial.objects.create(title="Fizika PDF", material_type="PDF")
        self.client.force_authenticate(self.student)
        list_response = self.client.get("/api/v1/library/")
        self.assertEqual(list_response.status_code, status.HTTP_200_OK)

        create_response = self.client.post(
            "/api/v1/library/", {"title": "Yangi kitob", "material_type": "BOOK"}
        )
        self.assertEqual(create_response.status_code, status.HTTP_403_FORBIDDEN)

    def test_superadmin_can_view_but_not_upload(self):
        LibraryMaterial.objects.create(title="Tarix kitobi", material_type="BOOK")
        superadmin = User.objects.create_user(
            username="superadmin1", password="Str0ngPass!23", role=User.Role.SUPERADMIN
        )
        self.client.force_authenticate(superadmin)

        list_response = self.client.get("/api/v1/library/")
        self.assertEqual(list_response.status_code, status.HTTP_200_OK)

        create_response = self.client.post(
            "/api/v1/library/", {"title": "Yangi kitob", "material_type": "BOOK"}
        )
        self.assertEqual(create_response.status_code, status.HTTP_403_FORBIDDEN)
