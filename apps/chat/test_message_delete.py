"""Deleting a chat message: only its author may do it, and the school director and the class
teacher (curator) — nobody else — are told on Telegram what was deleted."""

from unittest import mock

from rest_framework.test import APITestCase

from apps.classes.models import AcademicYear, ClassRoom
from apps.notifications.models import Notification
from apps.schools.models import School
from apps.users.models import ParentProfile, ParentStudent, StudentProfile, TeacherProfile, User

from .models import ChatMember, ChatRoom, Message

PASSWORD = "Str0ngPass!23"


class MessageDeleteFixture(APITestCase):
    def user(self, username, role, **extra):
        return User.objects.create_user(username=username, password=PASSWORD, role=role, school=self.school, **extra)

    def login(self, user):
        self.client.force_authenticate(User.objects.get(pk=user.pk))

    def setUp(self):
        self.school = School.objects.create(name="School A")
        self.other_school = School.objects.create(name="School B")
        year = AcademicYear.objects.create(name="2026-2027", start_date="2026-09-01", end_date="2027-05-31")

        self.director = self.user("director", User.Role.DIRECTOR, first_name="Akmal", last_name="Nurmatov", telegram_chat_id="900")
        self.curator_a = self.user("curator_a", User.Role.TEACHER, first_name="Olim", last_name="Sattorov", phone="+998901111111", telegram_chat_id="901")
        self.curator_b = self.user("curator_b", User.Role.TEACHER, first_name="Nodira", last_name="Aliyeva", telegram_chat_id="902")
        self.bystander = self.user("teacher_c", User.Role.TEACHER, telegram_chat_id="903")
        self.admin = self.user("adm", User.Role.ADMIN, telegram_chat_id="904")
        self.foreign_director = User.objects.create_user(
            username="dir_b", password=PASSWORD, role=User.Role.DIRECTOR, school=self.other_school, telegram_chat_id="999"
        )
        profile_a = TeacherProfile.objects.create(user=self.curator_a, school=self.school, teacher_id="T-1")
        profile_b = TeacherProfile.objects.create(user=self.curator_b, school=self.school, teacher_id="T-2")
        self.class_a = ClassRoom.objects.create(school=self.school, name="9-A", grade=9, academic_year=year, curator=profile_a)
        self.class_b = ClassRoom.objects.create(school=self.school, name="9-B", grade=9, academic_year=year, curator=profile_b)

        self.author = self.user("aziz", User.Role.STUDENT, first_name="Aziz", last_name="Karimov", phone="+998902222222")
        self.friend = self.user("malika", User.Role.STUDENT, first_name="Malika", last_name="Nazarova", telegram_chat_id="905")
        self.author_profile = StudentProfile.objects.create(user=self.author, school=self.school, class_room=self.class_a, student_code="S-1")
        StudentProfile.objects.create(user=self.friend, school=self.school, class_room=self.class_b, student_code="S-2")

        self.room = ChatRoom.objects.create(room_type=ChatRoom.RoomType.PRIVATE, name="dm")
        ChatMember.objects.create(chat_room=self.room, user=self.author)
        ChatMember.objects.create(chat_room=self.room, user=self.friend)

    def write(self, sender, text, room=None):
        return Message.objects.create(chat_room=room or self.room, sender=sender, text=text)

    def delete_as(self, user, message):
        self.login(user)
        with mock.patch("apps.notifications.tasks.send_telegram_message") as telegram:
            response = self.client.delete(f"/api/v1/chat/messages/{message.id}/")
        return response, telegram

    @staticmethod
    def chats(telegram):
        return {call.args[0]: call.args[1] for call in telegram.call_args_list}


class WhoMayDeleteTests(MessageDeleteFixture):
    def test_the_author_deletes_their_own_message(self):
        message = self.write(self.author, "Xato yozibman")
        response, _ = self.delete_as(self.author, message)
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Message.objects.filter(pk=message.pk).exists())
        self.login(self.friend)
        self.assertEqual(self.client.get(f"/api/v1/chat/messages/?chat_room={self.room.id}").data["results"], [])

    def test_nobody_else_can_delete_it_not_even_a_member_or_a_moderator(self):
        message = self.write(self.author, "Salom")
        for who in (self.friend, self.admin, self.director, self.curator_a, self.bystander):
            with self.subTest(user=who.username):
                response, _ = self.delete_as(who, message)
                self.assertEqual(response.status_code, 403)
        self.assertTrue(Message.objects.filter(pk=message.pk).exists())

    def test_messages_cannot_be_edited_by_anybody(self):
        message = self.write(self.author, "Salom")
        for user in (self.author, self.friend):
            self.login(user)
            with self.subTest(user=user.username):
                self.assertEqual(self.client.patch(f"/api/v1/chat/messages/{message.id}/", {"text": "endi boshqa"}).status_code, 405)
                self.assertEqual(self.client.put(f"/api/v1/chat/messages/{message.id}/", {"chat_room": self.room.id, "text": "x"}).status_code, 405)
        self.assertEqual(Message.objects.get(pk=message.pk).text, "Salom")

    def test_sending_and_reading_still_work(self):
        self.login(self.author)
        sent = self.client.post("/api/v1/chat/messages/", {"chat_room": self.room.id, "text": "Salom"})
        self.assertEqual(sent.status_code, 201)
        self.assertEqual(len(self.client.get(f"/api/v1/chat/messages/?chat_room={self.room.id}").data["results"]), 1)

    def test_anonymous_gets_401(self):
        message = self.write(self.author, "Salom")
        self.client.force_authenticate(None)
        self.assertEqual(self.client.delete(f"/api/v1/chat/messages/{message.id}/").status_code, 401)


class WhoIsToldTests(MessageDeleteFixture):
    def test_the_director_and_the_class_teacher_are_told_on_telegram_and_nobody_else(self):
        message = self.write(self.author, "Bu test xabar")
        response, telegram = self.delete_as(self.author, message)
        self.assertEqual(response.status_code, 204)

        sent = self.chats(telegram)
        self.assertEqual(set(sent), {"900", "901"})  # director and 9-A's curator — no other chat id
        for text in sent.values():
            for fragment in ("Chatda xabar o'chirildi", "Aziz Karimov", "9-A", "O'quvchi", "Malika Nazarova", "Bu test xabar"):
                self.assertIn(fragment, text)
        # the director gets the full picture, the class teacher the essentials
        for fragment in ("@aziz", "+998902222222", "Sinf rahbari: Olim Sattorov"):
            self.assertIn(fragment, sent["900"])
        self.assertNotIn("@aziz", sent["901"])

        told = set(Notification.objects.values_list("user__username", flat=True))
        self.assertEqual(told, {"director", "curator_a"})  # the in-app copy goes to the same two people
        # not the other pupil, the other class's teacher, a bystander, the admin or another school's director
        self.assertFalse(Notification.objects.filter(user__in=[self.friend, self.curator_b, self.bystander, self.admin, self.foreign_director]).exists())

    def test_a_swearing_message_is_marked_as_such(self):
        message = self.write(self.author, "sen ahmoqsan")
        _, telegram = self.delete_as(self.author, message)
        for text in self.chats(telegram).values():
            self.assertIn("sen ahmoqsan", text)
            self.assertIn("so'kinish", text)

    def test_a_clean_message_carries_no_swearing_note(self):
        message = self.write(self.author, "Salom, dars qachon?")
        _, telegram = self.delete_as(self.author, message)
        for text in self.chats(telegram).values():
            self.assertNotIn("so'kinish", text)

    def test_in_a_class_chat_that_classes_teacher_hears_too(self):
        room = ChatRoom.objects.create(room_type=ChatRoom.RoomType.CLASS_GENERAL, name="9-B sinf chati", class_room=self.class_b)
        ChatMember.objects.create(chat_room=room, user=self.author)
        message = self.write(self.author, "Salom 9-B", room=room)
        _, telegram = self.delete_as(self.author, message)
        self.assertEqual(set(self.chats(telegram)), {"900", "901", "902"})  # director, own curator, the class chat's curator
        self.assertIn("Sinf chati", self.chats(telegram)["902"])

    def test_a_parents_message_reaches_their_childs_class_teacher(self):
        parent = self.user("parent", User.Role.PARENT, first_name="Dilorom", last_name="Karimova")
        ParentStudent.objects.create(parent=ParentProfile.objects.create(user=parent), student=self.author_profile)
        room = ChatRoom.objects.create(room_type=ChatRoom.RoomType.PARENT_TEACHER, name="")
        ChatMember.objects.create(chat_room=room, user=parent)
        ChatMember.objects.create(chat_room=room, user=self.curator_b)
        message = self.write(parent, "Salom ustoz", room=room)
        _, telegram = self.delete_as(parent, message)
        # the director and 9-A's teacher (her child's class) — not 9-B's teacher, who is merely in the chat
        self.assertEqual(set(self.chats(telegram)), {"900", "901"})
        self.assertIn("Dilorom Karimova", self.chats(telegram)["901"])

    def test_a_teacher_deleting_in_the_staff_room_only_tells_the_director(self):
        room = ChatRoom.objects.create(room_type=ChatRoom.RoomType.STAFF_GENERAL, name="O'qituvchilar xonasi")
        for member in (self.curator_a, self.curator_b, self.director):
            ChatMember.objects.create(chat_room=room, user=member)
        message = self.write(self.curator_b, "Yigilish soat 3 da", room=room)
        _, telegram = self.delete_as(self.curator_b, message)
        self.assertEqual(set(self.chats(telegram)), {"900"})
        self.assertIn("O'qituvchilar xonasi", self.chats(telegram)["900"])

    def test_the_director_deleting_their_own_message_tells_nobody(self):
        room = ChatRoom.objects.create(room_type=ChatRoom.RoomType.STAFF_GENERAL, name="O'qituvchilar xonasi")
        ChatMember.objects.create(chat_room=room, user=self.director)
        message = self.write(self.director, "Ertaga yigilish", room=room)
        response, telegram = self.delete_as(self.director, message)
        self.assertEqual(response.status_code, 204)
        telegram.assert_not_called()
        self.assertFalse(Notification.objects.exists())

    def test_without_telegram_the_bell_still_rings(self):
        User.objects.filter(pk__in=[self.director.pk, self.curator_a.pk]).update(telegram_chat_id=None)
        message = self.write(self.author, "Salom")
        _, telegram = self.delete_as(self.author, message)
        telegram.assert_not_called()
        self.assertEqual(set(Notification.objects.values_list("user__username", flat=True)), {"director", "curator_a"})


class SideEffectsTests(MessageDeleteFixture):
    def test_the_other_members_see_it_vanish_live(self):
        message = self.write(self.author, "Salom")
        self.login(self.author)
        with mock.patch("apps.chat.views.push_message_deleted_to_chat") as push, mock.patch("apps.notifications.tasks.send_telegram_message"):
            self.client.delete(f"/api/v1/chat/messages/{message.id}/")
        push.assert_called_once_with(self.room.id, message.id)

    def test_the_deletion_is_audited_without_the_text(self):
        from common.models import AuditLog

        message = self.write(self.author, "Sir matn")
        self.delete_as(self.author, message)
        entry = AuditLog.objects.get(action="CHAT_MESSAGE_DELETED")
        self.assertEqual(entry.actor_id, self.author.id)
        self.assertIn(f"message={message.id}", entry.description)
        self.assertNotIn("Sir matn", entry.description)

    def test_a_failing_alert_never_turns_the_delete_into_an_error(self):
        message = self.write(self.author, "Salom")
        self.login(self.author)
        with mock.patch("apps.notifications.tasks.notify_message_deleted.delay", side_effect=RuntimeError("broker down")):
            with self.assertLogs("apps.chat.views", level="ERROR"):  # logged, not raised
                response = self.client.delete(f"/api/v1/chat/messages/{message.id}/")
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Message.objects.filter(pk=message.pk).exists())

    def test_a_failing_live_push_neither_blocks_the_delete_nor_the_alert(self):
        message = self.write(self.author, "Salom")
        self.login(self.author)
        with mock.patch("apps.chat.views.push_message_deleted_to_chat", side_effect=RuntimeError("redis down")):
            with mock.patch("apps.notifications.tasks.send_telegram_message") as telegram:
                with self.assertLogs("apps.chat.views", level="ERROR"):
                    response = self.client.delete(f"/api/v1/chat/messages/{message.id}/")
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Message.objects.filter(pk=message.pk).exists())
        self.assertEqual(set(self.chats(telegram)), {"900", "901"})  # the director and the class teacher still hear about it
