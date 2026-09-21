from unittest import mock

from django.test import SimpleTestCase
from rest_framework.test import APITestCase

from apps.classes.models import AcademicYear, ClassRoom
from apps.notifications.models import Notification, NotificationType
from apps.schools.models import School
from apps.users.models import StudentProfile, TeacherProfile, User

from .models import ChatMember, ChatRoom, ModerationIncident
from .moderation import find_profanity


class ProfanityDetectionTests(SimpleTestCase):
    def test_detects_swearing_in_three_languages_and_scripts(self):
        bad = [
            "sen ahmoqsan",
            "Siktir ket",
            "o'zi ahmoq",
            "q0toq",
            "ты сука",
            "хуйня какая-то",
            "пошёл нахуй",
            "ебаный",
            "идиот",
            "blyat",
            "you are a bitch",
            "fuuuck you",
            "sh1t",
            "f u c k",
        ]
        for text in bad:
            self.assertTrue(find_profanity(text), f"should be flagged: {text!r}")

    def test_clean_text_is_not_flagged(self):
        good = [
            "Assalomu alaykum",
            "salom, uy vazifasi qanday?",
            "bugun dars bormi",
            "classic",
            "Scunthorpe",
            "blade runner",
            "hue color",
            "shiitake",
            "assam tea",
            "Hello class",
            "passport",
            "sikl",
            "sikka",
            "кот дома",
            "математика",
            "хорошо",
            "Russia",
            "matematika 5 baho",
        ]
        for text in good:
            self.assertEqual(find_profanity(text), [], f"should be clean: {text!r}")


class ProfanityReportingTests(APITestCase):
    def setUp(self):
        self.school = School.objects.create(name="School #1")
        year = AcademicYear.objects.create(name="2026-2027", start_date="2026-09-01", end_date="2027-05-31")

        self.curator_user = User.objects.create_user(
            username="curator", password="Str0ngPass!23", role=User.Role.TEACHER, school=self.school,
            first_name="Olim", last_name="Sattorov", telegram_chat_id="555",
        )
        curator = TeacherProfile.objects.create(user=self.curator_user, school=self.school, teacher_id="T-1")
        self.class_a = ClassRoom.objects.create(
            school=self.school, name="9-A", grade=9, academic_year=year, curator=curator
        )
        self.offender = User.objects.create_user(
            username="offender", password="Str0ngPass!23", role=User.Role.STUDENT, school=self.school,
            first_name="Aziz", last_name="Karimov",
        )
        StudentProfile.objects.create(user=self.offender, school=self.school, class_room=self.class_a, student_code="S-1")
        self.victim = User.objects.create_user(
            username="victim", password="Str0ngPass!23", role=User.Role.STUDENT, school=self.school,
            first_name="Malika", last_name="Nazarova",
        )
        StudentProfile.objects.create(user=self.victim, school=self.school, class_room=self.class_a, student_code="S-2")

        self.room = ChatRoom.objects.create(room_type=ChatRoom.RoomType.PRIVATE, name="dm")
        ChatMember.objects.create(chat_room=self.room, user=self.offender)
        ChatMember.objects.create(chat_room=self.room, user=self.victim)

    def _send(self, text):
        self.client.force_authenticate(self.offender)
        return self.client.post("/api/v1/chat/messages/", {"chat_room": self.room.id, "text": text})

    def test_swearing_notifies_class_curator_on_telegram_with_sender_and_target(self):
        with mock.patch("apps.notifications.tasks.send_telegram_message") as tg:
            response = self._send("sen ahmoqsan")
        self.assertEqual(response.status_code, 201)

        self.assertEqual(ModerationIncident.objects.count(), 1)
        notification = Notification.objects.get(user=self.curator_user)
        self.assertEqual(notification.type, NotificationType.CHAT_MESSAGE)

        tg.assert_called_once()
        chat_id, text = tg.call_args.args
        self.assertEqual(chat_id, "555")
        self.assertIn("Aziz Karimov", text)  # who wrote it
        self.assertIn("Malika Nazarova", text)  # who it was written to
        self.assertIn("sen ahmoqsan", text)  # the message itself
        self.assertIn("9-A", text)

    def test_clean_message_sends_nothing(self):
        with mock.patch("apps.notifications.tasks.send_telegram_message") as tg:
            response = self._send("Salom, dars qachon?")
        self.assertEqual(response.status_code, 201)
        self.assertFalse(ModerationIncident.objects.exists())
        tg.assert_not_called()

    def test_teacher_without_telegram_still_gets_in_app_notification(self):
        User.objects.filter(pk=self.curator_user.pk).update(telegram_chat_id=None)
        with mock.patch("apps.notifications.tasks.send_telegram_message") as tg:
            self._send("ты сука")
        tg.assert_not_called()
        self.assertTrue(Notification.objects.filter(user=self.curator_user).exists())

    def test_falls_back_to_school_admin_when_no_teacher_found(self):
        admin = User.objects.create_user(
            username="dir", password="Str0ngPass!23", role=User.Role.ADMIN, school=self.school, telegram_chat_id="777"
        )
        self.class_a.curator = None
        self.class_a.save()
        with mock.patch("apps.notifications.tasks.send_telegram_message") as tg:
            self._send("fuck you")
        tg.assert_called_once()
        self.assertEqual(tg.call_args.args[0], "777")
        self.assertTrue(Notification.objects.filter(user=admin).exists())
