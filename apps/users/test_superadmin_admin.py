"""SUPERADMIN and ADMIN: what each may do — checked on the backend.

SuperAdmin runs the whole system: system dashboard, schools, administrator accounts, user
accounts, roles and permissions. It does not run a school's daily work (that is the Admin's).
Admin runs ONE school: its pupils, teachers, classes, subjects, attendance and grades; it cannot
see another school, administer roles / global permissions, manage administrators or create /
delete schools.
"""

from apps.classes.models import ClassRoom
from apps.lessons.models import Lesson
from apps.schools.models import School
from apps.subjects.models import Subject
from common import rbac

from .models import StudentProfile, TeacherProfile, User
from .test_rbac import PASSWORD, R, SchoolWorld


def payload(**extra):
    base = {"username": "new.admin", "password": PASSWORD, "first_name": "Yangi", "last_name": "Admin", "phone": "901234567", "email": "a@x.uz"}
    base.update(extra)
    return base


# ---------------------------------------------------------------------------
# SUPERADMIN
# ---------------------------------------------------------------------------
class SuperAdminDashboardTests(SchoolWorld):
    def setUp(self):
        super().setUp()
        self.as_user(self.superadmin)

    def test_system_dashboard_totals_and_one_row_per_school(self):
        data = self.client.get("/api/v1/analytics/system/").data
        self.assertEqual(data["total_schools"], 2)
        self.assertEqual(data["total_admins"], 2)          # admin_a, admin_b
        self.assertEqual(data["total_students"], 4)        # s1..s4
        self.assertEqual(data["total_teachers"], 3)
        self.assertEqual(data["total_classes"], 3)
        rows = {row["name"]: row for row in data["schools"]}
        self.assertEqual((rows["School A"]["students"], rows["School A"]["teachers"], rows["School A"]["classes"], rows["School A"]["admins"]), (3, 3, 2, 1))
        self.assertEqual((rows["School B"]["students"], rows["School B"]["teachers"], rows["School B"]["classes"], rows["School B"]["admins"]), (1, 0, 1, 1))

    def test_only_the_superadmin_sees_the_system_dashboard(self):
        for who in (self.admin_a, self.director, self.deputy, self.t1_user, self.s1_user, self.p1_user):
            self.as_user(who)
            with self.subTest(user=who.username):
                self.assertEqual(self.client.get("/api/v1/analytics/system/").status_code, 403)
        self.client.force_authenticate(None)
        self.assertEqual(self.client.get("/api/v1/analytics/system/").status_code, 401)

    def test_can_open_any_single_school_through_the_school_dashboard(self):
        one = self.client.get(f"/api/v1/analytics/admin/?school={self.school_b.id}").data
        self.assertEqual((one["total_students"], one["total_teachers"], one["total_classes"]), (1, 0, 1))
        self.assertEqual(one["active_users"], User.objects.filter(is_active=True, school=self.school_b).count())


class SuperAdminSchoolsTests(SchoolWorld):
    def setUp(self):
        super().setUp()
        self.as_user(self.superadmin)

    def test_adds_edits_and_deletes_an_empty_school(self):
        created = self.client.post("/api/v1/schools/", {"name": "School C", "address": "Toshkent"})
        self.assertEqual(created.status_code, 201)
        url = f"/api/v1/schools/{created.data['id']}/"
        self.assertEqual(self.client.patch(url, {"address": "Samarqand"}).status_code, 200)
        self.assertEqual(self.client.get("/api/v1/schools/").data["count"], 3)
        self.assertEqual(self.client.delete(url).status_code, 204)
        self.assertFalse(School.objects.filter(pk=created.data["id"]).exists())

    def test_edits_any_school(self):
        self.assertEqual(self.client.patch(f"/api/v1/schools/{self.school_b.id}/", {"name": "School B2"}).status_code, 200)

    def test_deleting_a_school_that_still_has_data_needs_force(self):
        url = f"/api/v1/schools/{self.school_a.id}/"
        refused = self.client.delete(url)
        self.assertEqual(refused.status_code, 409)
        self.assertEqual(refused.data["errors"]["dependents"]["classes"], 2)
        self.assertTrue(School.objects.filter(pk=self.school_a.id).exists())
        self.assertEqual(self.client.delete(url + "?force=true").status_code, 204)
        self.assertFalse(School.objects.filter(pk=self.school_a.id).exists())
        self.assertFalse(ClassRoom.objects.filter(name__in=["9-A", "9-B"]).exists())  # classes went with it
        self.assertTrue(School.objects.filter(pk=self.school_b.id).exists())  # nothing else was touched


class SuperAdminAdministratorsTests(SchoolWorld):
    def setUp(self):
        super().setUp()
        self.as_user(self.superadmin)

    def test_creates_an_administrator_for_a_school(self):
        created = self.client.post("/api/v1/users/", payload(school=self.school_b.id))
        self.assertEqual(created.status_code, 201)
        admin = User.objects.get(username="new.admin")
        self.assertEqual((admin.role, admin.school_id, admin.phone), (R.ADMIN, self.school_b.id, "+998901234567"))
        self.assertTrue(admin.check_password(PASSWORD))
        self.assertEqual(created.data["roles"], ["ADMIN"])
        self.assertNotIn("password", created.data)

    def test_creation_is_validated(self):
        self.assertEqual(self.client.post("/api/v1/users/", payload(school=self.school_a.id, username="admin_a")).status_code, 400)  # taken
        self.assertEqual(self.client.post("/api/v1/users/", payload(school=self.school_a.id, password="123")).status_code, 400)      # weak
        self.assertEqual(self.client.post("/api/v1/users/", payload()).status_code, 400)                                             # no school
        self.assertEqual(self.client.post("/api/v1/users/", payload(school=999999)).status_code, 400)                                # no such school
        # a role cannot be smuggled in: it is always an administrator
        self.client.post("/api/v1/users/", payload(school=self.school_a.id, role="SUPERADMIN"))
        self.assertEqual(User.objects.get(username="new.admin").role, R.ADMIN)

    def test_lists_administrators_of_every_school(self):
        listed = self.client.get("/api/v1/users/?role=ADMIN&page_size=100").data["results"]
        self.assertEqual(sorted(u["username"] for u in listed), ["admin_a", "admin_b"])

    def test_edits_an_administrator_and_moves_them_to_another_school(self):
        url = f"/api/v1/users/{self.admin_a.id}/"
        moved = self.client.patch(url, {"first_name": "Aziz", "email": "aziz@x.uz", "phone": "911112233", "school": self.school_b.id})
        self.assertEqual(moved.status_code, 200)
        admin = User.objects.get(pk=self.admin_a.pk)
        self.assertEqual((admin.first_name, admin.school_id, admin.phone), ("Aziz", self.school_b.id, "+998911112233"))
        self.assertEqual(self.client.patch(url, {"phone": "12"}).status_code, 400)
        # login, role and password are not editable here
        self.client.patch(url, {"username": "hacker", "role": "SUPERADMIN", "password": "Xx123456!!"})
        admin.refresh_from_db()
        self.assertEqual((admin.username, admin.role), ("admin_a", R.ADMIN))
        self.assertTrue(admin.check_password(PASSWORD))

    def test_only_administrator_accounts_can_be_edited_through_it(self):
        for user in (self.t1_user, self.s1_user, self.director):
            with self.subTest(user=user.username):
                self.assertEqual(self.client.patch(f"/api/v1/users/{user.id}/", {"first_name": "X"}).status_code, 403)

    def test_blocks_and_unblocks_an_administrator(self):
        blocked = self.client.post(f"/api/v1/auth/users/{self.admin_b.id}/deactivate/")
        self.assertEqual(blocked.status_code, 200)
        self.assertFalse(User.objects.get(pk=self.admin_b.pk).is_active)
        login = self.client.post("/api/v1/auth/login/", {"username": "admin_b", "password": PASSWORD})
        self.assertIn(login.status_code, (400, 401))  # a blocked account cannot sign in
        self.assertEqual(self.client.post(f"/api/v1/auth/users/{self.admin_b.id}/activate/").status_code, 200)
        self.assertTrue(User.objects.get(pk=self.admin_b.pk).is_active)

    def test_deletes_an_administrator(self):
        self.assertEqual(self.client.delete(f"/api/v1/users/{self.admin_b.id}/").status_code, 204)
        self.assertFalse(User.objects.filter(pk=self.admin_b.pk).exists())

    def test_the_actions_are_audited(self):
        from common.models import AuditLog

        created = self.client.post("/api/v1/users/", payload(school=self.school_a.id))
        self.client.patch(f"/api/v1/users/{created.data['id']}/", {"first_name": "Q"})
        self.client.delete(f"/api/v1/users/{created.data['id']}/")
        actions = list(AuditLog.objects.filter(target="new.admin").values_list("action", flat=True))
        self.assertEqual(sorted(actions), ["ADMIN_CREATED", "ADMIN_UPDATED", "USER_DELETED"])


class SuperAdminUsersTests(SchoolWorld):
    def setUp(self):
        super().setUp()
        self.as_user(self.superadmin)

    def test_sees_every_user_of_every_school(self):
        listed = {u["username"] for u in self.client.get("/api/v1/users/?page_size=100").data["results"]}
        self.assertTrue({"s1", "s4", "t1", "admin_a", "admin_b", "director", "super"} <= listed)

    def test_blocks_any_user(self):
        for user in (self.s4_user, self.t2_user, self.admin_a):
            with self.subTest(user=user.username):
                self.assertEqual(self.client.post(f"/api/v1/auth/users/{user.id}/deactivate/").status_code, 200)

    def test_deletes_a_teacher_together_with_the_profile(self):
        self.assertEqual(self.client.delete(f"/api/v1/users/{self.t3_user.id}/").status_code, 204)
        self.assertFalse(User.objects.filter(pk=self.t3_user.pk).exists())
        self.assertFalse(TeacherProfile.objects.filter(pk=self.t3.pk).exists())

    def test_cannot_delete_itself_or_another_superadmin(self):
        other = self.make_user("super2", R.SUPERADMIN, self.school_a)
        self.assertEqual(self.client.delete(f"/api/v1/users/{self.superadmin.id}/").status_code, 403)
        self.assertEqual(self.client.delete(f"/api/v1/users/{other.id}/").status_code, 403)
        self.assertTrue(User.objects.filter(pk__in=[self.superadmin.pk, other.pk]).count() == 2)


class SuperAdminSettingsTests(SchoolWorld):
    def test_manages_roles_and_permissions_but_not_the_school_day(self):
        self.as_user(self.superadmin)
        self.assertEqual(self.client.get("/api/v1/roles/").status_code, 200)
        self.assertEqual(self.client.get("/api/v1/permissions/").status_code, 200)
        self.assertEqual(self.client.post(f"/api/v1/users/{self.t3_user.id}/roles/", {"role": "PARENT"}).status_code, 200)
        # ...while the day-to-day school work stays with the admin
        record = {"student": self.s1.id, "class_room": self.class_a.id, "date": "2026-09-16", "status": "ABSENT"}
        self.assertEqual(self.client.post("/api/v1/attendance/", record).status_code, 403)
        self.assertEqual(self.client.post("/api/v1/grades/", self.grade_payload(self.s1, self.math)).status_code, 403)

    def test_the_permission_sets(self):
        superadmin = rbac.ROLE_PERMISSIONS[rbac.SUPERADMIN]
        admin = rbac.ROLE_PERMISSIONS[rbac.ADMIN]
        system = {"manage_schools", "manage_admins", "delete_users", "view_system_stats", "manage_roles", "manage_permissions"}
        self.assertTrue(system <= superadmin)
        self.assertEqual(admin & system, set())
        # nobody but the SuperAdmin holds the system level by default
        for role, perms in rbac.ROLE_PERMISSIONS.items():
            if role != rbac.SUPERADMIN:
                self.assertEqual(perms & system, set(), role)

    def test_system_permissions_can_only_be_granted_by_the_superadmin(self):
        self.as_user(self.admin_a)  # an admin cannot grant them at all
        url = f"/api/v1/users/{self.t3_user.id}/permissions/"
        for codename in ("manage_schools", "manage_admins", "delete_users", "view_system_stats"):
            self.assertEqual(self.client.post(url, {"permission": codename}).status_code, 403)


# ---------------------------------------------------------------------------
# ADMIN
# ---------------------------------------------------------------------------
class AdminOwnSchoolTests(SchoolWorld):
    def setUp(self):
        super().setUp()
        self.as_user(self.admin_a)

    def test_dashboard_counts_only_its_own_school(self):
        for n in range(3):  # accounts elsewhere must not inflate School A's numbers
            self.make_user(f"other{n}", R.TEACHER, self.school_b)
        data = self.client.get("/api/v1/analytics/admin/").data
        self.assertEqual((data["total_students"], data["total_teachers"], data["total_classes"]), (3, 3, 2))
        self.assertEqual(data["active_users"], User.objects.filter(is_active=True, school=self.school_a).count())
        self.assertIn("attendance_percentage", data)
        # asking for another school's numbers changes nothing
        again = self.client.get(f"/api/v1/analytics/admin/?school={self.school_b.id}").data
        self.assertEqual((again["total_students"], again["total_classes"]), (3, 2))

    def test_no_system_dashboard(self):
        self.assertEqual(self.client.get("/api/v1/analytics/system/").status_code, 403)

    def test_cannot_create_or_delete_schools_but_can_edit_its_own(self):
        self.assertEqual(self.client.post("/api/v1/schools/", {"name": "Rogue"}).status_code, 403)
        self.assertEqual(self.client.delete(f"/api/v1/schools/{self.school_a.id}/").status_code, 403)
        self.assertEqual(self.client.delete(f"/api/v1/schools/{self.school_a.id}/?force=true").status_code, 403)
        self.assertTrue(School.objects.filter(pk=self.school_a.id).exists())
        self.assertEqual(self.client.patch(f"/api/v1/schools/{self.school_a.id}/", {"address": "Yangi ko'cha"}).status_code, 200)
        self.assertEqual(self.client.patch(f"/api/v1/schools/{self.school_b.id}/", {"address": "hack"}).status_code, 403)
        self.assertEqual(self.client.delete(f"/api/v1/schools/{self.school_b.id}/").status_code, 403)

    def test_sees_no_other_school(self):
        self.assertEqual(self.ids(self.client.get("/api/v1/schools/")), [self.school_a.id])
        self.assertNotIn(self.s4.id, self.ids(self.client.get("/api/v1/students/")))
        self.assertNotIn(self.class_x.id, self.ids(self.client.get("/api/v1/classes/")))
        for url in (f"students/{self.s4.id}/", f"grades/?student={self.s4.id}", f"attendance/?student={self.s4.id}"):
            self.assertEqual(self.client.get(f"/api/v1/{url}").status_code, 403, url)

    def test_supervises_attendance_and_grades(self):
        self.assertEqual(sorted(self.ids(self.client.get("/api/v1/grades/"))), sorted([self.grade_1.id, self.grade_3.id]))
        self.assertEqual(sorted(self.ids(self.client.get("/api/v1/attendance/"))), sorted([self.att_1.id, self.att_3.id]))
        self.assertEqual(self.client.get("/api/v1/attendance/teacher-attendance/").status_code, 200)
        self.assertEqual(self.client.get("/api/v1/analytics/admin/").status_code, 200)


class AdminStudentsTests(SchoolWorld):
    def setUp(self):
        super().setUp()
        self.as_user(self.admin_a)

    def test_adds_edits_assigns_and_deletes_a_student(self):
        new = {"username": "kid", "password": PASSWORD, "first_name": "K", "last_name": "D", "student_code": "S-77"}
        created = self.client.post("/api/v1/auth/register/student/", new)
        self.assertEqual(created.status_code, 201)
        profile = StudentProfile.objects.get(student_code="S-77")
        self.assertEqual(profile.school_id, self.school_a.id)  # always its own school
        self.assertEqual(self.client.patch(f"/api/v1/students/{profile.id}/", {"first_name": "Kamol"}).status_code, 200)
        assigned = self.client.post(f"/api/v1/students/{profile.id}/transfer/", {"new_class": self.class_b.id})
        self.assertEqual(assigned.status_code, 201)
        self.assertEqual(StudentProfile.objects.get(pk=profile.pk).class_room_id, self.class_b.id)
        self.assertEqual(self.client.delete(f"/api/v1/students/{profile.id}/").status_code, 204)
        # the login goes with the profile — nobody is left able to sign in
        self.assertFalse(User.objects.filter(username="kid").exists())

    def test_cannot_touch_another_schools_students(self):
        self.assertEqual(self.client.patch(f"/api/v1/students/{self.s4.id}/", {"first_name": "X"}).status_code, 403)
        self.assertEqual(self.client.delete(f"/api/v1/students/{self.s4.id}/").status_code, 403)
        self.assertTrue(User.objects.filter(pk=self.s4_user.pk).exists())
        new = {"username": "kid2", "password": PASSWORD, "student_code": "S-78", "school": self.school_b.id}
        self.assertEqual(self.client.post("/api/v1/auth/register/student/", new).status_code, 403)


class AdminTeachersTests(SchoolWorld):
    def setUp(self):
        super().setUp()
        self.as_user(self.admin_a)

    def teacher(self, **extra):
        body = {"username": "newteacher", "password": PASSWORD, "first_name": "Nodir", "last_name": "Aliyev", "phone": "907771122",
                "email": "n@x.uz", "experience_years": 4, "subjects": [self.math.id]}
        body.update(extra)
        return body

    def test_adds_a_teacher_with_a_login_in_its_own_school(self):
        created = self.client.post("/api/v1/teachers/", self.teacher())
        self.assertEqual(created.status_code, 201)
        user = User.objects.get(username="newteacher")
        profile = user.teacher_profile
        self.assertEqual((user.role, user.school_id, profile.school_id), (R.TEACHER, self.school_a.id, self.school_a.id))
        self.assertEqual(user.phone, "+998907771122")
        self.assertTrue(user.check_password(PASSWORD))
        self.assertRegex(profile.teacher_id, r"^T-\d{4}$")
        self.assertEqual(list(profile.subjects.values_list("id", flat=True)), [self.math.id])
        self.assertEqual(created.data["user"]["username"], "newteacher")
        self.assertNotIn("password", created.data)

    def test_a_school_admin_cannot_create_a_teacher_for_another_school(self):
        self.assertEqual(self.client.post("/api/v1/teachers/", self.teacher(school=self.school_b.id)).status_code, 403)
        self.assertFalse(User.objects.filter(username="newteacher").exists())
        # leaving the school out means "mine"
        self.client.post("/api/v1/teachers/", self.teacher())
        self.assertEqual(User.objects.get(username="newteacher").school_id, self.school_a.id)

    def test_creation_is_validated(self):
        self.assertEqual(self.client.post("/api/v1/teachers/", self.teacher(username="t1")).status_code, 400)          # login taken
        self.assertEqual(self.client.post("/api/v1/teachers/", self.teacher(password="123")).status_code, 400)          # weak password
        self.assertEqual(self.client.post("/api/v1/teachers/", self.teacher(teacher_id="T-1")).status_code, 400)        # code taken
        body = self.teacher()
        del body["password"]
        self.assertEqual(self.client.post("/api/v1/teachers/", body).status_code, 400)                                  # no password
        self.assertEqual(self.client.post("/api/v1/teachers/", self.teacher(phone="12")).status_code, 400)
        self.assertEqual(TeacherProfile.objects.count(), 3)  # nothing half-created

    def test_a_superadmin_must_name_the_school(self):
        self.as_user(self.superadmin)
        self.assertEqual(self.client.post("/api/v1/teachers/", self.teacher()).status_code, 400)
        created = self.client.post("/api/v1/teachers/", self.teacher(school=self.school_b.id))
        self.assertEqual(created.status_code, 201)
        self.assertEqual(User.objects.get(username="newteacher").school_id, self.school_b.id)

    def test_edits_a_teacher_and_assigns_subjects(self):
        url = f"/api/v1/teachers/{self.t3.id}/"
        changed = self.client.patch(url, {"first_name": "Yangi", "phone": "905554433", "email": "t3@x.uz", "experience_years": 9, "subjects": [self.math.id, self.physics.id]})
        self.assertEqual(changed.status_code, 200)
        user = User.objects.get(pk=self.t3_user.pk)
        self.assertEqual((user.first_name, user.phone, user.email), ("Yangi", "+998905554433", "t3@x.uz"))
        self.assertEqual(TeacherProfile.objects.get(pk=self.t3.pk).subjects.count(), 2)
        # login and password are not editable here
        self.assertEqual(self.client.patch(url, {"username": "hacker"}).status_code, 400)
        self.assertEqual(self.client.patch(url, {"password": "Xx123456!!"}).status_code, 400)
        self.assertEqual(User.objects.get(pk=self.t3_user.pk).username, "t3")

    def test_assigns_a_teacher_to_a_class_as_its_curator(self):
        assigned = self.client.patch(f"/api/v1/classes/{self.class_a.id}/", {"curator": self.t3.id})
        self.assertEqual(assigned.status_code, 200)
        self.assertEqual(ClassRoom.objects.get(pk=self.class_a.id).curator_id, self.t3.id)

    def test_deleting_a_teacher_removes_the_login_too(self):
        self.assertEqual(self.client.delete(f"/api/v1/teachers/{self.t3.id}/").status_code, 204)
        self.assertFalse(User.objects.filter(pk=self.t3_user.pk).exists())
        self.assertFalse(TeacherProfile.objects.filter(pk=self.t3.pk).exists())

    def test_cannot_touch_another_schools_teachers(self):
        tb_user, tb = self.make_teacher("t_b", self.school_b, "T-B")
        self.assertNotIn(tb.id, self.ids(self.client.get("/api/v1/teachers/")))
        self.assertEqual(self.client.patch(f"/api/v1/teachers/{tb.id}/", {"first_name": "X"}).status_code, 403)
        self.assertEqual(self.client.delete(f"/api/v1/teachers/{tb.id}/").status_code, 403)
        self.assertTrue(User.objects.filter(pk=tb_user.pk).exists())

    def test_other_roles_cannot_add_teachers(self):
        for who in (self.t1_user, self.director, self.deputy, self.s1_user):
            self.as_user(who)
            with self.subTest(user=who.username):
                self.assertEqual(self.client.post("/api/v1/teachers/", self.teacher(username=f"x{who.id}")).status_code, 403)


class AdminClassesAndSubjectsTests(SchoolWorld):
    def setUp(self):
        super().setUp()
        self.as_user(self.admin_a)

    def test_classes_create_edit_assign_curator_delete(self):
        body = {"school": self.school_a.id, "name": "10-Q", "grade": 10, "academic_year": self.year.id}
        created = self.client.post("/api/v1/classes/", body)
        self.assertEqual(created.status_code, 201)
        url = f"/api/v1/classes/{created.data['id']}/"
        self.assertEqual(self.client.patch(url, {"name": "10-R", "curator": self.t3.id}).status_code, 200)
        self.assertEqual(ClassRoom.objects.get(pk=created.data["id"]).curator_id, self.t3.id)
        self.assertEqual(self.client.delete(url).status_code, 204)
        self.assertEqual(self.client.post("/api/v1/classes/", dict(body, school=self.school_b.id)).status_code, 403)
        self.assertEqual(self.client.patch(f"/api/v1/classes/{self.class_x.id}/", {"name": "hack"}).status_code, 403)
        self.assertEqual(self.client.delete(f"/api/v1/classes/{self.class_x.id}/").status_code, 403)

    def test_subjects_create_edit_delete(self):
        created = self.client.post("/api/v1/subjects/", {"name": "Kimyo"})
        self.assertEqual(created.status_code, 201)
        url = f"/api/v1/subjects/{created.data['id']}/"
        self.assertEqual(self.client.patch(url, {"name": "Kimyo 2"}).status_code, 200)
        self.assertEqual(self.client.delete(url).status_code, 204)

    def test_assigns_a_teacher_to_a_subject(self):
        self.assertEqual(self.client.patch(f"/api/v1/teachers/{self.t3.id}/", {"subjects": [self.physics.id]}).status_code, 200)
        self.assertIn(self.physics.id, self.t3.subjects.values_list("id", flat=True))

    def test_a_subject_other_schools_depend_on_is_protected(self):
        # The catalogue is shared, so renaming / deleting "Matematika" would break School B's data.
        tb_user, tb = self.make_teacher("t_b", self.school_b, "T-B", [self.math])
        Lesson.objects.create(class_room=self.class_x, subject=self.math, teacher=tb, room="1", date="2026-09-15", start_time="09:00", end_time="09:45")
        url = f"/api/v1/subjects/{self.math.id}/"
        self.assertEqual(self.client.patch(url, {"name": "Renamed"}).status_code, 403)
        self.assertEqual(self.client.delete(url).status_code, 403)
        self.assertTrue(Subject.objects.filter(pk=self.math.id, name="Matematika").exists())
        # the SuperAdmin still may
        self.as_user(self.superadmin)
        self.assertEqual(self.client.patch(url, {"name": "Algebra"}).status_code, 200)

    def test_a_subject_only_its_own_school_uses_can_still_be_changed(self):
        # physics is used by t2 / lesson_b of School A only
        self.assertEqual(self.client.patch(f"/api/v1/subjects/{self.physics.id}/", {"description": "Fizika asoslari"}).status_code, 200)


class AdminLimitsTests(SchoolWorld):
    """What an Admin must never do: touch administrators / SuperAdmins, hand out roles or
    permissions, create or delete users through the directory."""

    def setUp(self):
        super().setUp()
        self.as_user(self.admin_a)
        self.admin_a2 = self.make_user("admin_a2", R.ADMIN, self.school_a)

    def test_cannot_manage_other_administrators_or_the_superadmin(self):
        for target in (self.admin_a2, self.admin_b, self.superadmin):
            with self.subTest(target=target.username):
                self.assertEqual(self.client.post(f"/api/v1/auth/users/{target.id}/deactivate/").status_code, 403)
                self.assertEqual(self.client.post(f"/api/v1/auth/users/{target.id}/reset-password/", {"new_password": "Xx123456!!"}).status_code, 403)
                self.assertTrue(User.objects.get(pk=target.pk).is_active)
        # not even itself
        self.assertEqual(self.client.post(f"/api/v1/auth/users/{self.admin_a.id}/deactivate/").status_code, 403)

    def test_still_manages_the_accounts_of_its_school(self):
        self.assertEqual(self.client.post(f"/api/v1/auth/users/{self.t3_user.id}/deactivate/").status_code, 200)
        self.assertEqual(self.client.post(f"/api/v1/auth/users/{self.t3_user.id}/activate/").status_code, 200)
        self.assertEqual(self.client.post(f"/api/v1/auth/users/{self.s1_user.id}/reset-password/", {"new_password": "Xx123456!!"}).status_code, 200)

    def test_the_user_directory_is_read_only_for_an_admin(self):
        self.assertEqual(self.client.post("/api/v1/users/", payload(school=self.school_a.id)).status_code, 403)
        self.assertEqual(self.client.patch(f"/api/v1/users/{self.admin_a2.id}/", {"first_name": "X"}).status_code, 403)
        self.assertEqual(self.client.delete(f"/api/v1/users/{self.t3_user.id}/").status_code, 403)
        self.assertEqual(self.client.delete(f"/api/v1/users/{self.admin_a2.id}/").status_code, 403)
        self.assertTrue(User.objects.filter(pk__in=[self.t3_user.pk, self.admin_a2.pk]).count() == 2)

    def test_the_directory_never_shows_superadmins_or_other_schools(self):
        listed = {u["username"] for u in self.client.get("/api/v1/users/?page_size=100").data["results"]}
        self.assertNotIn("super", listed)
        self.assertNotIn("admin_b", listed)
        self.assertNotIn("s4", listed)
        self.assertIn("t1", listed)

    def test_cannot_change_roles_or_permissions(self):
        url = f"/api/v1/users/{self.t3_user.id}"
        self.assertEqual(self.client.post(f"{url}/roles/", {"role": "PARENT"}).status_code, 403)
        self.assertEqual(self.client.post(f"{url}/permissions/", {"permission": "transfer_students"}).status_code, 403)
        self.assertEqual(self.client.get("/api/v1/permissions/").status_code, 403)
        self.assertEqual(self.client.get("/api/v1/roles/").status_code, 403)

    def test_anonymous_requests_get_401(self):
        self.client.force_authenticate(None)
        for method, url in [("post", "/api/v1/users/"), ("delete", f"/api/v1/users/{self.t3_user.id}/"), ("post", "/api/v1/schools/"), ("post", "/api/v1/teachers/")]:
            with self.subTest(url=url):
                self.assertEqual(getattr(self.client, method)(url, {}).status_code, 401)
