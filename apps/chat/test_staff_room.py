"""Director <-> teachers communication: the shared staff room, private chats with teachers,
and the swearing alert that always reaches the director."""

from unittest import mock

from rest_framework.test import APITestCase

from apps.classes.models import AcademicYear, ClassRoom
from apps.notifications.models import Notification
from apps.schools.models import School
from apps.users.models import StudentProfile, TeacherProfile, User

from .models import ChatMember, ChatRoom, ModerationIncident

PASSWORD = "Str0ngPass!23"


class StaffFixture(APITestCase):
    def user(self, username, role, school, **extra):
        return User.objects.create_user(username=username, password=PASSWORD, role=role, school=school, **extra)

    def login(self, user):
        self.client.force_authenticate(User.objects.get(pk=user.pk))

    def setUp(self):
        self.school = School.objects.create(name="School A")
        self.other_school = School.objects.create(name="School B")
        self.director = self.user(
            "director", User.Role.DIRECTOR, self.school, first_name="Akmal", last_name="Nurmatov", telegram_chat_id="900"
        )
        self.t1 = self.user(
            "t1", User.Role.TEACHER, self.school,
            first_name="Olim", last_name="Sattorov", phone="+998901111111", telegram_chat_id="901",
        )
        self.t2 = self.user("t2", User.Role.TEACHER, self.school)
        self.foreign_teacher = self.user("t_b", User.Role.TEACHER, self.other_school)
        self.foreign_director = self.user("dir_b", User.Role.DIRECTOR, self.other_school, telegram_chat_id="999")
        self.student = self.user(
            "st", User.Role.STUDENT, self.school, first_name="Aziz", last_name="Karimov", phone="+998902222222"
        )
        self.admin = self.user("adm", User.Role.ADMIN, self.school)
        year = AcademicYear.objects.create(name="2026-2027", start_date="2026-09-01", end_date="2027-05-31")
        profile = TeacherProfile.objects.create(user=self.t1, school=self.school, teacher_id="T-1")
        self.class_a = ClassRoom.objects.create(
            school=self.school, name="9-A", grade=9, academic_year=year, curator=profile
        )
        StudentProfile.objects.create(user=self.student, school=self.school, class_room=self.class_a, student_code="S-1")


class StaffRoomTests(StaffFixture):
    def test_director_and_teachers_share_one_room_of_their_school(self):
        self.login(self.director)
        room = self.client.get("/api/v1/chat/staff_room/").data
        members = {m["user"] for m in room["members"]}
        # not the student, the admin or the other school
        self.assertEqual(members, {self.director.id, self.t1.id, self.t2.id})
        self.assertEqual(room["room_type"], "STAFF_GENERAL")

        self.login(self.t1)
        again = self.client.get("/api/v1/chat/staff_room/").data
        self.assertEqual(again["id"], room["id"])  # one room, not one per person
        self.assertEqual(ChatRoom.objects.filter(room_type="STAFF_GENERAL").count(), 1)

    def test_each_school_has_its_own_room(self):
        self.login(self.director)
        mine = self.client.get("/api/v1/chat/staff_room/").data["id"]
        self.login(self.foreign_director)
        theirs = self.client.get("/api/v1/chat/staff_room/").data
        self.assertNotEqual(mine, theirs["id"])
        self.assertEqual({m["user"] for m in theirs["members"]}, {self.foreign_director.id, self.foreign_teacher.id})

    def test_room_shows_up_in_the_chat_list_and_follows_the_staff(self):
        self.login(self.t2)
        listed = self.client.get("/api/v1/chat/").data["results"]
        self.assertEqual([r["room_type"] for r in listed], ["STAFF_GENERAL"])
        newcomer = self.user("t_new", User.Role.TEACHER, self.school)
        User.objects.filter(pk=self.t2.pk).update(is_active=False)
        self.login(self.director)
        self.client.get("/api/v1/chat/")
        members = set(ChatMember.objects.filter(chat_room__room_type="STAFF_GENERAL").values_list("user_id", flat=True))
        self.assertIn(newcomer.id, members)
        self.assertNotIn(self.t2.id, members)

    def test_students_and_admin_have_no_staff_room(self):
        for who in (self.student, self.admin):
            self.login(who)
            with self.subTest(user=who.username):
                self.assertEqual(self.client.get("/api/v1/chat/staff_room/").status_code, 403)
        self.assertFalse(ChatRoom.objects.filter(room_type="STAFF_GENERAL").exists())

    def test_director_and_a_teacher_talk_in_the_room(self):
        self.login(self.director)
        room_id = self.client.get("/api/v1/chat/staff_room/").data["id"]
        posted = self.client.post("/api/v1/chat/messages/", {"chat_room": room_id, "text": "Ertaga yigilish"})
        self.assertEqual(posted.status_code, 201)
        self.login(self.t1)
        seen = self.client.get(f"/api/v1/chat/messages/?chat_room={room_id}").data["results"]
        self.assertEqual([m["text"] for m in seen], ["Ertaga yigilish"])
        reply = self.client.post("/api/v1/chat/messages/", {"chat_room": room_id, "text": "Boldi"})
        self.assertEqual(reply.status_code, 201)

    def test_outsiders_cannot_read_or_join_the_room(self):
        self.login(self.director)
        room_id = self.client.get("/api/v1/chat/staff_room/").data["id"]
        self.login(self.student)
        self.assertEqual(self.client.get(f"/api/v1/chat/messages/?chat_room={room_id}").data["results"], [])
        self.assertEqual(self.client.post("/api/v1/chat/messages/", {"chat_room": room_id, "text": "salom"}).status_code, 403)
        # staff themselves cannot pull anyone in, rename or delete it, nor fake another one
        self.login(self.t1)
        self.assertEqual(self.client.post(f"/api/v1/chat/{room_id}/add_member/", {"user": self.student.id}).status_code, 403)
        self.assertEqual(self.client.patch(f"/api/v1/chat/{room_id}/", {"name": "x"}).status_code, 403)
        self.assertEqual(self.client.delete(f"/api/v1/chat/{room_id}/").status_code, 403)
        self.assertEqual(self.client.post("/api/v1/chat/", {"room_type": "STAFF_GENERAL", "name": "fake"}).status_code, 403)


class DirectorPrivateChatTests(StaffFixture):
    def test_director_opens_a_private_chat_with_a_teacher_who_can_answer(self):
        self.login(self.director)
        room = self.client.post("/api/v1/chat/", {"room_type": "PRIVATE", "name": "Olim Sattorov"})
        self.assertEqual(room.status_code, 201)
        added = self.client.post(f"/api/v1/chat/{room.data['id']}/add_member/", {"user": self.t1.id})
        self.assertEqual(added.status_code, 201)
        sent = self.client.post("/api/v1/chat/messages/", {"chat_room": room.data["id"], "text": "Hisobotni yuboring"})
        self.assertEqual(sent.status_code, 201)
        self.login(self.t1)
        answer = self.client.post("/api/v1/chat/messages/", {"chat_room": room.data["id"], "text": "Xop boladi"})
        self.assertEqual(answer.status_code, 201)
        self.assertEqual(len(self.client.get(f"/api/v1/chat/messages/?chat_room={room.data['id']}").data["results"]), 2)


class DirectorProfanityAlertTests(StaffFixture):
    def _incident_in(self, sender, room, text):
        self.login(sender)
        with mock.patch("apps.notifications.tasks.send_telegram_message") as tg:
            response = self.client.post("/api/v1/chat/messages/", {"chat_room": room.id, "text": text})
        self.assertEqual(response.status_code, 201)
        return tg

    def _private(self, *members):
        room = ChatRoom.objects.create(room_type=ChatRoom.RoomType.PRIVATE, name="dm")
        for member in members:
            ChatMember.objects.create(chat_room=room, user=member)
        return room

    def test_director_gets_every_incident_with_writer_details_and_the_text(self):
        pal = self.user("pal", User.Role.STUDENT, self.school, first_name="Malika", last_name="Nazarova")
        StudentProfile.objects.create(user=pal, school=self.school, class_room=self.class_a, student_code="S-2")
        tg = self._incident_in(self.student, self._private(self.student, pal), "sen ahmoqsan")

        sent = {call.args[0]: call.args[1] for call in tg.call_args_list}
        self.assertIn("900", sent)  # the director's Telegram
        director_text = sent["900"]
        expected = (
            "Aziz Karimov", "O'quvchi", "9-A", "@st", "+998902222222",
            "Olim Sattorov", "+998901111111", "Malika Nazarova", "sen ahmoqsan",
        )
        for fragment in expected:
            self.assertIn(fragment, director_text)
        self.assertIn("901", sent)  # the class teacher still hears about it too
        self.assertNotIn("Login:", sent["901"])  # ...with the shorter teacher text
        self.assertTrue(Notification.objects.filter(user=self.director).exists())
        self.assertNotIn("999", sent)  # another school's director is not told

    def test_a_teacher_swearing_alerts_the_director(self):
        tg = self._incident_in(self.t1, self._private(self.t1, self.t2), "fuck this")
        self.assertIn("900", {call.args[0] for call in tg.call_args_list})
        text = next(call.args[1] for call in tg.call_args_list if call.args[0] == "900")
        self.assertIn("Olim Sattorov", text)
        self.assertIn("O'qituvchi", text)

    def test_swearing_in_the_staff_room_alerts_director_but_not_the_whole_staff(self):
        self.login(self.director)
        room_id = self.client.get("/api/v1/chat/staff_room/").data["id"]
        tg = self._incident_in(self.t1, ChatRoom.objects.get(pk=room_id), "ты сука")
        chat_ids = {call.args[0] for call in tg.call_args_list}
        self.assertEqual(chat_ids, {"900"})
        self.assertEqual(ModerationIncident.objects.count(), 1)
        self.assertFalse(Notification.objects.filter(user=self.t2).exists())

    def test_directors_own_swearing_reaches_admin_not_himself(self):
        tg = self._incident_in(self.director, self._private(self.director, self.t1), "fuck")
        chat_ids = {call.args[0] for call in tg.call_args_list}
        self.assertNotIn("900", chat_ids)
        self.assertTrue(Notification.objects.filter(user=self.admin).exists())


class StaffDirectoryTests(StaffFixture):
    def names(self, response):
        return sorted(person["name"] for person in response.data)

    def test_director_can_pick_any_teacher_of_the_school(self):
        self.login(self.director)
        response = self.client.get("/api/v1/chat/staff/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(sorted(p["id"] for p in response.data), sorted([self.t1.id, self.t2.id]))
        self.assertEqual({p["role"] for p in response.data}, {"TEACHER"})  # not himself, no other school

    def test_class_teacher_sees_colleagues_and_the_director(self):
        self.login(self.t1)
        response = self.client.get("/api/v1/chat/staff/")
        by_id = {p["id"]: p["role"] for p in response.data}
        self.assertEqual(by_id, {self.director.id: "DIRECTOR", self.t2.id: "TEACHER"})

    def test_search_narrows_the_list(self):
        self.login(self.director)
        found = self.client.get("/api/v1/chat/staff/?search=olim")
        self.assertEqual([p["id"] for p in found.data], [self.t1.id])

    def test_students_and_admin_are_refused(self):
        for who in (self.student, self.admin):
            self.login(who)
            with self.subTest(user=who.username):
                self.assertEqual(self.client.get("/api/v1/chat/staff/").status_code, 403)
        self.client.force_authenticate(None)
        self.assertEqual(self.client.get("/api/v1/chat/staff/").status_code, 401)
