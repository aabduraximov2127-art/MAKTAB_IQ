from rest_framework import status
from rest_framework.test import APITestCase

from apps.schools.models import School
from apps.users.models import StudentProfile, User

from .models import AcademicYear, ClassRoom


class ClassRoomAPITests(APITestCase):
    def setUp(self):
        self.school = School.objects.create(name="School #1")
        self.academic_year = AcademicYear.objects.create(
            name="2026-2027", start_date="2026-09-01", end_date="2027-05-31", is_active=True
        )
        self.admin = User.objects.create_user(
            username="admin", password="Str0ngPass!23", role=User.Role.ADMIN, school=self.school
        )
        self.student = User.objects.create_user(username="student", password="Str0ngPass!23", role=User.Role.STUDENT)

    def test_admin_can_create_class(self):
        self.client.force_authenticate(self.admin)
        response = self.client.post(
            "/api/v1/classes/",
            {"school": self.school.id, "name": "9-A", "grade": 9, "academic_year": self.academic_year.id},
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_student_cannot_create_class(self):
        self.client.force_authenticate(self.student)
        response = self.client.post(
            "/api/v1/classes/",
            {"school": self.school.id, "name": "9-B", "grade": 9, "academic_year": self.academic_year.id},
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_student_only_sees_own_class(self):
        own_class = ClassRoom.objects.create(
            school=self.school, name="9-A", grade=9, academic_year=self.academic_year
        )
        ClassRoom.objects.create(school=self.school, name="9-B", grade=9, academic_year=self.academic_year)
        StudentProfile.objects.create(
            user=self.student, school=self.school, class_room=own_class, student_code="S-0001"
        )

        self.client.force_authenticate(self.student)
        response = self.client.get("/api/v1/classes/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        names = [c["name"] for c in response.data["results"]]
        self.assertEqual(names, ["9-A"])


class SchoolAdminClassScopingTests(APITestCase):
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
        self.admin_a = User.objects.create_user(
            username="admin_a", password="Str0ngPass!23", role=User.Role.ADMIN, school=self.school_a
        )
        self.superadmin = User.objects.create_user(
            username="superadmin1", password="Str0ngPass!23", role=User.Role.SUPERADMIN
        )

    def test_admin_sees_only_own_school_classes(self):
        self.client.force_authenticate(self.admin_a)
        response = self.client.get("/api/v1/classes/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = [c["id"] for c in response.data["results"]]
        self.assertIn(self.class_a.id, ids)
        self.assertNotIn(self.class_b.id, ids)

    def test_admin_cannot_view_other_school_class(self):
        self.client.force_authenticate(self.admin_a)
        response = self.client.get(f"/api/v1/classes/{self.class_b.id}/")
        self.assertIn(response.status_code, (403, 404))

    def test_admin_creates_class_in_own_school(self):
        self.client.force_authenticate(self.admin_a)
        response = self.client.post(
            "/api/v1/classes/",
            {"school": self.school_a.id, "name": "10-B", "grade": 10, "academic_year": self.academic_year.id},
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_admin_cannot_create_class_for_other_school(self):
        self.client.force_authenticate(self.admin_a)
        response = self.client.post(
            "/api/v1/classes/",
            {"school": self.school_b.id, "name": "10-C", "grade": 10, "academic_year": self.academic_year.id},
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_cannot_update_other_school_class(self):
        self.client.force_authenticate(self.admin_a)
        response = self.client.patch(f"/api/v1/classes/{self.class_b.id}/", {"name": "Hacked"})
        self.assertIn(response.status_code, (403, 404))

    def test_superadmin_sees_all_schools_classes(self):
        self.client.force_authenticate(self.superadmin)
        response = self.client.get("/api/v1/classes/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = [c["id"] for c in response.data["results"]]
        self.assertIn(self.class_a.id, ids)
        self.assertIn(self.class_b.id, ids)
