from django.core.exceptions import ValidationError
from django.test import SimpleTestCase
from rest_framework.test import APITestCase

from common.validators import normalize_uz_phone

from .models import StudentProfile, User


class NormalizePhoneTests(SimpleTestCase):
    def test_accepts_common_formats(self):
        for raw in ["+998901234567", "998901234567", "901234567", "+998 90 123 45 67", "(90) 123-45-67"]:
            self.assertEqual(normalize_uz_phone(raw), "+998901234567", raw)

    def test_blank_is_allowed(self):
        self.assertEqual(normalize_uz_phone(""), "")
        self.assertEqual(normalize_uz_phone("   "), "")

    def test_rejects_wrong_length(self):
        for raw in ["+99890123", "+9989012345678", "12345"]:
            with self.assertRaises(ValidationError):
                normalize_uz_phone(raw)


class PhoneApiTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_user(username="adm", password="Str0ngPass!23", role=User.Role.SUPERADMIN)
        self.client.force_authenticate(self.admin)

    def _register(self, phone, code):
        return self.client.post(
            "/api/v1/auth/register/student/",
            {"username": f"u{code}", "password": "Str0ngPass!23", "first_name": "A", "last_name": "B",
             "student_code": code, "phone": phone},
        )

    def test_register_normalizes_phone(self):
        response = self._register("90 123 45 67", "P-1")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(StudentProfile.objects.get(student_code="P-1").user.phone, "+998901234567")

    def test_register_rejects_incomplete_phone(self):
        response = self._register("+99890", "P-2")
        self.assertEqual(response.status_code, 400)

    def test_register_without_phone_is_fine(self):
        self.assertEqual(self._register("", "P-3").status_code, 201)

    def test_patch_rejects_incomplete_phone(self):
        profile = StudentProfile.objects.create(
            user=User.objects.create_user(username="st", password="Str0ngPass!23", role=User.Role.STUDENT),
            student_code="P-4",
        )
        response = self.client.patch(f"/api/v1/students/{profile.id}/", {"phone": "+9989"})
        self.assertEqual(response.status_code, 400)
        ok = self.client.patch(f"/api/v1/students/{profile.id}/", {"phone": "+998 91 111 22 33"})
        self.assertEqual(ok.status_code, 200)
        profile.user.refresh_from_db()
        self.assertEqual(profile.user.phone, "+998911112233")
