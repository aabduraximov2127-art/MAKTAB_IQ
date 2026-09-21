from rest_framework import status
from rest_framework.test import APITestCase

from apps.users.models import User

from .models import School


class SchoolAPITests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_user(username="admin", password="Str0ngPass!23", role=User.Role.ADMIN)
        self.teacher = User.objects.create_user(username="teacher", password="Str0ngPass!23", role=User.Role.TEACHER)

    def test_admin_can_create_school(self):
        self.client.force_authenticate(self.admin)
        response = self.client.post("/api/v1/schools/", {"name": "Maktab 1"})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_teacher_cannot_create_school(self):
        self.client.force_authenticate(self.teacher)
        response = self.client.post("/api/v1/schools/", {"name": "Maktab 2"})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_anyone_authenticated_can_list_schools(self):
        School.objects.create(name="Maktab 3")
        self.client.force_authenticate(self.teacher)
        response = self.client.get("/api/v1/schools/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class SchoolAdminSettingsScopingTests(APITestCase):
    def setUp(self):
        self.school_a = School.objects.create(name="School A")
        self.school_b = School.objects.create(name="School B")
        self.admin_a = User.objects.create_user(
            username="admin_a", password="Str0ngPass!23", role=User.Role.ADMIN, school=self.school_a
        )

    def test_admin_can_update_own_school(self):
        self.client.force_authenticate(self.admin_a)
        response = self.client.patch(f"/api/v1/schools/{self.school_a.id}/", {"phone": "+998900000000"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_admin_cannot_update_other_school(self):
        # Excluded at the queryset level (own-school-only list), so this 404s
        # before reaching the object-level check — an acceptable "denied" per
        # the school-object-security spec (403 or 404).
        self.client.force_authenticate(self.admin_a)
        response = self.client.patch(f"/api/v1/schools/{self.school_b.id}/", {"phone": "+998900000001"})
        self.assertIn(response.status_code, (status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND))
        self.school_b.refresh_from_db()
        self.assertNotEqual(self.school_b.phone, "+998900000001")

    def test_admin_school_list_scoped_to_own_school(self):
        self.client.force_authenticate(self.admin_a)
        response = self.client.get("/api/v1/schools/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = [s["id"] for s in response.data["results"]]
        self.assertEqual(ids, [self.school_a.id])
