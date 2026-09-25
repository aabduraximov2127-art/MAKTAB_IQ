"""The shared staff room ("O'qituvchilar xonasi") and the colleague picker behind "Ustozga yozish".

Every teacher (a class teacher is a teacher too) finds one common room per school in their chat
list and can start a private chat with any colleague. Students, parents and admins are never
part of it, and neither is anybody from another school.
"""

from rest_framework.test import APITestCase

from apps.classes.models import AcademicYear, ClassRoom
from apps.schools.models import School
from apps.users.models import StudentProfile, TeacherProfile, User

from .models import ChatMember, ChatRoom
from .services import STAFF_ROOM_ROLES

PASSWORD = "Str0ngPass!23"


class TeachersRoomFixture(APITestCase):
    def user(self, username, role, school, **extra):
        return User.objects.create_user(username=username, password=PASSWORD, role=role, school=school, **extra)

    def login(self, user):
        self.client.force_authenticate(User.objects.get(pk=user.pk))

    def setUp(self):
        self.school = School.objects.create(name="School A")
        self.other_school = School.objects.create(name="School B")
        # t1 is the class teacher (kurator) of 9-A
        self.t1 = self.user("t1", User.Role.TEACHER, self.school, first_name="Olim", last_name="Sattorov")
        self.t2 = self.user("t2", User.Role.TEACHER, self.school, first_name="Nodira", last_name="Aliyeva")
        self.foreign_teacher = self.user("t_b", User.Role.TEACHER, self.other_school)
        self.student = self.user("st", User.Role.STUDENT, self.school, first_name="Aziz", last_name="Karimov")
        self.admin = self.user("adm", User.Role.ADMIN, self.school)
        year = AcademicYear.objects.create(name="2026-2027", start_date="2026-09-01", end_date="2027-05-31")
        profile = TeacherProfile.objects.create(user=self.t1, school=self.school, teacher_id="T-1")
        self.class_a = ClassRoom.objects.create(school=self.school, name="9-A", grade=9, academic_year=year, curator=profile)
        StudentProfile.objects.create(user=self.student, school=self.school, class_room=self.class_a, student_code="S-1")

    def staff_ids(self):
        """Everybody of school A who is meant to be in the room."""
        return set(
            User.objects.filter(school=self.school, role__in=STAFF_ROOM_ROLES).values_list("id", flat=True)
        )


class StaffRoomTests(TeachersRoomFixture):
    def test_teachers_share_one_room_of_their_school(self):
        self.login(self.t1)
        room = self.client.get("/api/v1/chat/staff_room/").data
        members = {m["user"] for m in room["members"]}
        self.assertEqual(members, self.staff_ids())
        self.assertLessEqual({self.t1.id, self.t2.id}, members)
        self.assertTrue(members.isdisjoint({self.student.id, self.admin.id, self.foreign_teacher.id}))
        self.assertEqual(room["room_type"], "STAFF_GENERAL")

        self.login(self.t2)
        again = self.client.get("/api/v1/chat/staff_room/").data
        self.assertEqual(again["id"], room["id"])  # one room, not one per person
        self.assertEqual(ChatRoom.objects.filter(room_type="STAFF_GENERAL").count(), 1)

    def test_each_school_has_its_own_room(self):
        self.login(self.t1)
        mine = self.client.get("/api/v1/chat/staff_room/").data["id"]
        self.login(self.foreign_teacher)
        theirs = self.client.get("/api/v1/chat/staff_room/").data
        self.assertNotEqual(mine, theirs["id"])
        self.assertEqual({m["user"] for m in theirs["members"]}, {self.foreign_teacher.id})

    def test_room_shows_up_in_the_chat_list_and_follows_the_staff(self):
        self.login(self.t2)
        listed = self.client.get("/api/v1/chat/").data["results"]
        self.assertEqual([r["room_type"] for r in listed], ["STAFF_GENERAL"])
        newcomer = self.user("t_new", User.Role.TEACHER, self.school)
        User.objects.filter(pk=self.t2.pk).update(is_active=False)
        self.login(self.t1)
        self.client.get("/api/v1/chat/")
        members = set(ChatMember.objects.filter(chat_room__room_type="STAFF_GENERAL").values_list("user_id", flat=True))
        self.assertIn(newcomer.id, members)
        self.assertNotIn(self.t2.id, members)

    def test_students_and_admin_have_no_staff_room(self):
        for who in (self.student, self.admin):
            self.login(who)
            with self.subTest(user=who.username):
                self.assertEqual(self.client.get("/api/v1/chat/staff_room/").status_code, 403)
                self.assertEqual(self.client.get("/api/v1/chat/staff/").status_code, 403)
        self.assertFalse(ChatRoom.objects.filter(room_type="STAFF_GENERAL").exists())
        self.client.force_authenticate(None)
        self.assertEqual(self.client.get("/api/v1/chat/staff_room/").status_code, 401)

    def test_teachers_talk_in_the_room(self):
        self.login(self.t1)
        room_id = self.client.get("/api/v1/chat/staff_room/").data["id"]
        posted = self.client.post("/api/v1/chat/messages/", {"chat_room": room_id, "text": "Ertaga yigilish"})
        self.assertEqual(posted.status_code, 201)
        self.login(self.t2)
        seen = self.client.get(f"/api/v1/chat/messages/?chat_room={room_id}").data["results"]
        self.assertEqual([m["text"] for m in seen], ["Ertaga yigilish"])
        self.assertEqual(self.client.post("/api/v1/chat/messages/", {"chat_room": room_id, "text": "Boldi"}).status_code, 201)

    def test_outsiders_cannot_read_or_join_the_room_and_it_cannot_be_tampered_with(self):
        self.login(self.t1)
        room_id = self.client.get("/api/v1/chat/staff_room/").data["id"]
        self.login(self.student)
        self.assertEqual(self.client.get(f"/api/v1/chat/messages/?chat_room={room_id}").data["results"], [])
        self.assertEqual(self.client.post("/api/v1/chat/messages/", {"chat_room": room_id, "text": "salom"}).status_code, 403)
        self.login(self.t2)  # members cannot pull anyone in, rename or delete it, nor fake another one
        self.assertEqual(self.client.post(f"/api/v1/chat/{room_id}/add_member/", {"user": self.student.id}).status_code, 403)
        self.assertEqual(self.client.patch(f"/api/v1/chat/{room_id}/", {"name": "x"}).status_code, 403)
        self.assertEqual(self.client.delete(f"/api/v1/chat/{room_id}/").status_code, 403)
        self.assertEqual(self.client.post("/api/v1/chat/", {"room_type": "STAFF_GENERAL", "name": "fake"}).status_code, 403)


class ColleaguePickerTests(TeachersRoomFixture):
    def test_class_teacher_picks_any_colleague_of_the_school(self):
        self.login(self.t1)
        response = self.client.get("/api/v1/chat/staff/")
        self.assertEqual(response.status_code, 200)
        ids = {person["id"] for person in response.data}
        self.assertEqual(ids, self.staff_ids() - {self.t1.id})  # not themselves, nobody from another school
        by_id = {person["id"]: person for person in response.data}
        self.assertEqual(by_id[self.t2.id], {"id": self.t2.id, "name": "Nodira Aliyeva", "role": "TEACHER"})

    def test_search_narrows_the_list(self):
        self.login(self.t1)
        found = self.client.get("/api/v1/chat/staff/?search=nodira")
        self.assertEqual([person["id"] for person in found.data], [self.t2.id])
        self.assertEqual(self.client.get("/api/v1/chat/staff/?search=zzz").data, [])

    def test_class_teacher_opens_a_private_chat_with_a_colleague_who_can_answer(self):
        self.login(self.t1)
        room = self.client.post("/api/v1/chat/", {"room_type": "PRIVATE", "name": "Olim Sattorov - Nodira Aliyeva"})
        self.assertEqual(room.status_code, 201)
        added = self.client.post(f"/api/v1/chat/{room.data['id']}/add_member/", {"user": self.t2.id})
        self.assertEqual(added.status_code, 201)
        sent = self.client.post("/api/v1/chat/messages/", {"chat_room": room.data["id"], "text": "9-A haqida gaplashamizmi?"})
        self.assertEqual(sent.status_code, 201)
        self.login(self.t2)
        listed = self.client.get("/api/v1/chat/").data["results"]
        self.assertIn(room.data["id"], [r["id"] for r in listed])
        answer = self.client.post("/api/v1/chat/messages/", {"chat_room": room.data["id"], "text": "Ha, albatta"})
        self.assertEqual(answer.status_code, 201)
        self.assertEqual(len(self.client.get(f"/api/v1/chat/messages/?chat_room={room.data['id']}").data["results"]), 2)
