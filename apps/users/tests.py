from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.classes.models import AcademicYear, ClassRoom
from apps.schools.models import School

from .models import ParentProfile, ParentStudent, StudentProfile, TeacherProfile, User


class StudentAccessPermissionTests(APITestCase):
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

        self.student_user = User.objects.create_user(
            username="student1", password="Str0ngPass!23", role=User.Role.STUDENT
        )
        self.student_profile = StudentProfile.objects.create(
            user=self.student_user, school=self.school, class_room=self.class_a, student_code="S-0001"
        )

        self.other_student_user = User.objects.create_user(
            username="student2", password="Str0ngPass!23", role=User.Role.STUDENT
        )
        self.other_student_profile = StudentProfile.objects.create(
            user=self.other_student_user, school=self.school, class_room=self.class_a, student_code="S-0002"
        )

        self.admin_user = User.objects.create_user(
            username="admin1", password="Str0ngPass!23", role=User.Role.ADMIN, is_staff=True, school=self.school
        )

        self.parent_user = User.objects.create_user(
            username="parent1", password="Str0ngPass!23", role=User.Role.PARENT
        )
        self.parent_profile = ParentProfile.objects.create(user=self.parent_user)
        ParentStudent.objects.create(parent=self.parent_profile, student=self.student_profile)

    def test_student_list_shows_classmates_but_retrieve_stays_self_only(self):
        # Needed so a student can pick a classmate to start a chat with — full
        # detail access (CanAccessStudentProfile) is unaffected: still self-only.
        other_class_user = User.objects.create_user(
            username="student9", password="Str0ngPass!23", role=User.Role.STUDENT
        )
        StudentProfile.objects.create(
            user=other_class_user, school=self.school, class_room=self.class_b, student_code="S-0009"
        )

        self.client.force_authenticate(self.student_user)
        list_response = self.client.get("/api/v1/students/")
        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        ids = [s["id"] for s in list_response.data["results"]]
        self.assertIn(self.student_profile.id, ids)
        self.assertIn(self.other_student_profile.id, ids)  # classmate, same class_a
        self.assertEqual(len(ids), 2)  # other_class_user's profile (class_b) excluded

        detail_response = self.client.get(
            reverse("students:student-detail", args=[self.other_student_profile.id])
        )
        self.assertEqual(detail_response.status_code, status.HTTP_403_FORBIDDEN)

    def test_student_cannot_view_other_student_profile(self):
        self.client.force_authenticate(self.student_user)
        url = reverse("students:student-detail", args=[self.other_student_profile.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_student_can_view_own_profile(self):
        self.client.force_authenticate(self.student_user)
        url = reverse("students:student-detail", args=[self.student_profile.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_student_cannot_transfer_self(self):
        self.client.force_authenticate(self.student_user)
        url = reverse("students:student-transfer", args=[self.student_profile.id])
        response = self.client.post(url, {"new_class": self.class_b.id, "reason": "test"})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_transfer_student(self):
        self.client.force_authenticate(self.admin_user)
        url = reverse("students:student-transfer", args=[self.student_profile.id])
        response = self.client.post(url, {"new_class": self.class_b.id, "reason": "admin decision"})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.student_profile.refresh_from_db()
        self.assertEqual(self.student_profile.class_room_id, self.class_b.id)

    def test_parent_can_view_own_child_but_not_others(self):
        self.client.force_authenticate(self.parent_user)

        url_own = reverse("students:student-detail", args=[self.student_profile.id])
        response_own = self.client.get(url_own)
        self.assertEqual(response_own.status_code, status.HTTP_200_OK)

        url_other = reverse("students:student-detail", args=[self.other_student_profile.id])
        response_other = self.client.get(url_other)
        self.assertEqual(response_other.status_code, status.HTTP_403_FORBIDDEN)

    def test_passport_hidden_from_student(self):
        self.student_profile.passport_number = "AB1234567"
        self.student_profile.save(update_fields=["passport_number"])
        self.client.force_authenticate(self.student_user)
        url = reverse("students:student-detail", args=[self.student_profile.id])
        response = self.client.get(url)
        self.assertNotIn("passport_number", response.data)

    def test_parent_can_edit_own_child_profile(self):
        self.client.force_authenticate(self.parent_user)
        url = reverse("students:student-detail", args=[self.student_profile.id])
        response = self.client.patch(url, {"phone": "+998900000011", "age": 16})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.student_profile.refresh_from_db()
        self.student_profile.user.refresh_from_db()
        self.assertEqual(self.student_profile.user.phone, "+998900000011")
        self.assertEqual(self.student_profile.age, 16)

    def test_parent_cannot_edit_other_students_profile(self):
        self.client.force_authenticate(self.parent_user)
        url = reverse("students:student-detail", args=[self.other_student_profile.id])
        response = self.client.patch(url, {"phone": "+998900000099"})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_parent_cannot_delete_student(self):
        self.client.force_authenticate(self.parent_user)
        url = reverse("students:student-detail", args=[self.student_profile.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_parent_cannot_change_class_room_via_update(self):
        self.client.force_authenticate(self.parent_user)
        url = reverse("students:student-detail", args=[self.student_profile.id])
        response = self.client.patch(url, {"class_room": self.class_b.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.student_profile.refresh_from_db()
        self.assertEqual(self.student_profile.class_room_id, self.class_a.id)

    def test_student_cannot_edit_own_profile(self):
        self.client.force_authenticate(self.student_user)
        url = reverse("students:student-detail", args=[self.student_profile.id])
        response = self.client.patch(url, {"phone": "+998900000022"})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_student_cannot_delete_own_profile(self):
        self.client.force_authenticate(self.student_user)
        url = reverse("students:student-detail", args=[self.student_profile.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_me_endpoint_has_no_update_method(self):
        # /me/ only exposes GET — there is no way for a student to PATCH their own
        # role/school/is_active through it.
        self.client.force_authenticate(self.student_user)
        response = self.client.patch(reverse("users:me"), {"role": "ADMIN"})
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)


class TeacherViewSetStudentScopingTests(APITestCase):
    """Point 9 of the student permission spec: a student may only see teachers
    actually teaching their own class (subject teachers or curator)."""

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

        self.own_teacher_user = User.objects.create_user(
            username="teacher_own", password="Str0ngPass!23", role=User.Role.TEACHER
        )
        self.own_teacher = TeacherProfile.objects.create(user=self.own_teacher_user, teacher_id="T-0001")
        self.class_a.curator = self.own_teacher
        self.class_a.save(update_fields=["curator"])

        self.other_teacher_user = User.objects.create_user(
            username="teacher_other", password="Str0ngPass!23", role=User.Role.TEACHER
        )
        self.other_teacher = TeacherProfile.objects.create(user=self.other_teacher_user, teacher_id="T-0002")
        self.class_b.curator = self.other_teacher
        self.class_b.save(update_fields=["curator"])

        self.student_user = User.objects.create_user(
            username="student1", password="Str0ngPass!23", role=User.Role.STUDENT
        )
        StudentProfile.objects.create(
            user=self.student_user, school=self.school, class_room=self.class_a, student_code="S-0001"
        )

    def test_student_sees_only_own_class_teachers(self):
        self.client.force_authenticate(self.student_user)
        response = self.client.get("/api/v1/teachers/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        teacher_ids = [t["id"] for t in response.data["results"]]
        self.assertIn(self.own_teacher.id, teacher_ids)
        self.assertNotIn(self.other_teacher.id, teacher_ids)

    def test_admin_still_sees_all_teachers(self):
        admin = User.objects.create_user(username="admin1", password="Str0ngPass!23", role=User.Role.ADMIN)
        self.client.force_authenticate(admin)
        response = self.client.get("/api/v1/teachers/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        teacher_ids = [t["id"] for t in response.data["results"]]
        self.assertIn(self.own_teacher.id, teacher_ids)
        self.assertIn(self.other_teacher.id, teacher_ids)


class SchoolAdminScopingTests(APITestCase):
    """School Admin / Director must only ever see or manage their own school's
    students, teachers, and accounts — SuperAdmin stays global/unrestricted."""

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

        self.student_a_user = User.objects.create_user(
            username="student_a", password="Str0ngPass!23", role=User.Role.STUDENT, school=self.school_a
        )
        self.student_a = StudentProfile.objects.create(
            user=self.student_a_user, school=self.school_a, class_room=self.class_a, student_code="A-0001"
        )
        self.student_b_user = User.objects.create_user(
            username="student_b", password="Str0ngPass!23", role=User.Role.STUDENT, school=self.school_b
        )
        self.student_b = StudentProfile.objects.create(
            user=self.student_b_user, school=self.school_b, class_room=self.class_b, student_code="B-0001"
        )

        self.teacher_a_user = User.objects.create_user(
            username="teacher_a", password="Str0ngPass!23", role=User.Role.TEACHER, school=self.school_a
        )
        self.teacher_a = TeacherProfile.objects.create(
            user=self.teacher_a_user, school=self.school_a, teacher_id="TA-0001"
        )
        self.teacher_b_user = User.objects.create_user(
            username="teacher_b", password="Str0ngPass!23", role=User.Role.TEACHER, school=self.school_b
        )
        self.teacher_b = TeacherProfile.objects.create(
            user=self.teacher_b_user, school=self.school_b, teacher_id="TB-0001"
        )

    # -- students --------------------------------------------------------- #
    def test_admin_sees_only_own_school_students(self):
        self.client.force_authenticate(self.admin_a)
        response = self.client.get("/api/v1/students/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = [s["id"] for s in response.data["results"]]
        self.assertIn(self.student_a.id, ids)
        self.assertNotIn(self.student_b.id, ids)

    def test_admin_cannot_view_other_school_student(self):
        self.client.force_authenticate(self.admin_a)
        url = reverse("students:student-detail", args=[self.student_b.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_update_own_school_student(self):
        self.client.force_authenticate(self.admin_a)
        url = reverse("students:student-detail", args=[self.student_a.id])
        response = self.client.patch(url, {"phone": "+998900000001"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_admin_cannot_update_other_school_student(self):
        self.client.force_authenticate(self.admin_a)
        url = reverse("students:student-detail", args=[self.student_b.id])
        response = self.client.patch(url, {"phone": "+998900000002"})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_creates_student_defaults_to_own_school(self):
        self.client.force_authenticate(self.admin_a)
        response = self.client.post(
            "/api/v1/auth/register/student/",
            {
                "username": "newstudent",
                "password": "Str0ngPass!23",
                "first_name": "Yangi",
                "last_name": "Student",
                "student_code": "A-9999",
                "class_room": self.class_a.id,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        new_profile = StudentProfile.objects.get(student_code="A-9999")
        self.assertEqual(new_profile.school_id, self.school_a.id)

    def test_admin_cannot_create_student_for_other_school(self):
        self.client.force_authenticate(self.admin_a)
        response = self.client.post(
            "/api/v1/auth/register/student/",
            {
                "username": "sneaky",
                "password": "Str0ngPass!23",
                "first_name": "X",
                "last_name": "Y",
                "student_code": "B-9999",
                "school": self.school_b.id,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_cannot_transfer_other_school_student(self):
        self.client.force_authenticate(self.admin_a)
        url = reverse("students:student-transfer", args=[self.student_b.id])
        response = self.client.post(url, {"new_class": self.class_b.id})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_cannot_transfer_student_into_other_school_class(self):
        self.client.force_authenticate(self.admin_a)
        url = reverse("students:student-transfer", args=[self.student_a.id])
        response = self.client.post(url, {"new_class": self.class_b.id})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.student_a.refresh_from_db()
        self.assertEqual(self.student_a.class_room_id, self.class_a.id)

    def test_superadmin_sees_all_schools_students(self):
        self.client.force_authenticate(self.superadmin)
        response = self.client.get("/api/v1/students/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = [s["id"] for s in response.data["results"]]
        self.assertIn(self.student_a.id, ids)
        self.assertIn(self.student_b.id, ids)

    # -- teachers ----------------------------------------------------------#
    def test_admin_sees_only_own_school_teachers(self):
        self.client.force_authenticate(self.admin_a)
        response = self.client.get("/api/v1/teachers/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = [t["id"] for t in response.data["results"]]
        self.assertIn(self.teacher_a.id, ids)
        self.assertNotIn(self.teacher_b.id, ids)

    def test_admin_cannot_view_other_school_teacher(self):
        self.client.force_authenticate(self.admin_a)
        response = self.client.get(f"/api/v1/teachers/{self.teacher_b.id}/")
        self.assertIn(response.status_code, (403, 404))

    def test_admin_cannot_update_other_school_teacher(self):
        self.client.force_authenticate(self.admin_a)
        response = self.client.patch(f"/api/v1/teachers/{self.teacher_b.id}/", {"experience_years": 99})
        self.assertIn(response.status_code, (403, 404))

    # -- account management (activate/deactivate/password) ---------------- #
    def test_admin_cannot_deactivate_other_school_user(self):
        self.client.force_authenticate(self.admin_a)
        response = self.client.post(f"/api/v1/auth/users/{self.student_b_user.id}/deactivate/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.student_b_user.refresh_from_db()
        self.assertTrue(self.student_b_user.is_active)

    def test_admin_can_deactivate_own_school_user(self):
        self.client.force_authenticate(self.admin_a)
        response = self.client.post(f"/api/v1/auth/users/{self.student_a_user.id}/deactivate/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_admin_cannot_reset_password_for_other_school_user(self):
        self.client.force_authenticate(self.admin_a)
        response = self.client.post(
            f"/api/v1/auth/users/{self.student_b_user.id}/reset-password/", {"new_password": "NewStr0ngPass!23"}
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # -- users listing ------------------------------------------------------#
    def test_admin_user_list_scoped_to_own_school(self):
        self.client.force_authenticate(self.admin_a)
        response = self.client.get("/api/v1/users/?page_size=100")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = [u["id"] for u in response.data["results"]]
        self.assertIn(self.student_a_user.id, ids)
        self.assertNotIn(self.student_b_user.id, ids)

    # -- role escalation ---------------------------------------------------#
    def test_admin_cannot_escalate_role_via_student_update(self):
        # StudentProfileUpdateSerializer never exposes `role` — an ADMIN cannot
        # smuggle a role change through the one PATCH endpoint they have access to.
        self.client.force_authenticate(self.admin_a)
        url = reverse("students:student-detail", args=[self.student_a.id])
        response = self.client.patch(url, {"role": "SUPERADMIN"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.student_a_user.refresh_from_db()
        self.assertEqual(self.student_a_user.role, User.Role.STUDENT)

    def test_no_endpoint_lets_admin_write_role_field(self):
        # UserViewSet is read-only for everyone, including ADMIN — there is no API
        # surface at all that accepts a `role` field for an existing user.
        self.client.force_authenticate(self.admin_a)
        response = self.client.patch(f"/api/v1/users/{self.student_a_user.id}/", {"role": "SUPERADMIN"})
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
