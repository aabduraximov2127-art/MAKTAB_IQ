from rest_framework import status
from rest_framework.test import APITestCase

from apps.classes.models import AcademicYear, ClassRoom
from apps.schools.models import School
from apps.users.models import StudentProfile, User

from .models import ChatMember, ChatRoom, Message


class ChatPermissionTests(APITestCase):
    def setUp(self):
        self.student1 = User.objects.create_user(username="s1", password="Str0ngPass!23", role=User.Role.STUDENT)
        self.student2 = User.objects.create_user(username="s2", password="Str0ngPass!23", role=User.Role.STUDENT)
        self.room = ChatRoom.objects.create(room_type=ChatRoom.RoomType.PRIVATE, name="Room 1")
        ChatMember.objects.create(chat_room=self.room, user=self.student1)

    def test_non_member_cannot_list_room_messages(self):
        Message.objects.create(chat_room=self.room, sender=self.student1, text="Salom")
        self.client.force_authenticate(self.student2)
        response = self.client.get(f"/api/v1/chat/messages/?chat_room={self.room.id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 0)

    def test_non_member_cannot_send_message(self):
        self.client.force_authenticate(self.student2)
        response = self.client.post(
            "/api/v1/chat/messages/", {"chat_room": self.room.id, "text": "Salom"}
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_member_can_send_message(self):
        self.client.force_authenticate(self.student1)
        response = self.client.post(
            "/api/v1/chat/messages/", {"chat_room": self.room.id, "text": "Salom"}
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


class StudentClassChatTests(APITestCase):
    """New capability: a student may start a private chat with a classmate and
    has an auto-provisioned whole-class group chat. Other roles' chat
    permissions are untouched."""

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

        self.student1_user = User.objects.create_user(
            username="student1", password="Str0ngPass!23", role=User.Role.STUDENT
        )
        self.student1 = StudentProfile.objects.create(
            user=self.student1_user, school=self.school, class_room=self.class_a, student_code="S-0001"
        )
        self.student2_user = User.objects.create_user(
            username="student2", password="Str0ngPass!23", role=User.Role.STUDENT
        )
        self.student2 = StudentProfile.objects.create(
            user=self.student2_user, school=self.school, class_room=self.class_a, student_code="S-0002"
        )
        self.other_class_user = User.objects.create_user(
            username="student3", password="Str0ngPass!23", role=User.Role.STUDENT
        )
        self.other_class_student = StudentProfile.objects.create(
            user=self.other_class_user, school=self.school, class_room=self.class_b, student_code="S-0003"
        )

    def test_student_can_create_private_room_and_add_classmate(self):
        self.client.force_authenticate(self.student1_user)
        create_response = self.client.post("/api/v1/chat/", {"room_type": "PRIVATE", "name": "Salom"})
        self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)
        room_id = create_response.data["id"]

        add_response = self.client.post(f"/api/v1/chat/{room_id}/add_member/", {"user": self.student2_user.id})
        self.assertIn(add_response.status_code, (200, 201))
        self.assertTrue(ChatMember.objects.filter(chat_room_id=room_id, user=self.student2_user).exists())

    def test_student_cannot_add_non_classmate_to_room(self):
        self.client.force_authenticate(self.student1_user)
        create_response = self.client.post("/api/v1/chat/", {"room_type": "PRIVATE", "name": "Salom"})
        room_id = create_response.data["id"]

        add_response = self.client.post(f"/api/v1/chat/{room_id}/add_member/", {"user": self.other_class_user.id})
        self.assertEqual(add_response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(ChatMember.objects.filter(chat_room_id=room_id, user=self.other_class_user).exists())

    def test_student_cannot_create_class_general_room_directly(self):
        self.client.force_authenticate(self.student1_user)
        response = self.client.post(
            "/api/v1/chat/", {"room_type": "CLASS_GENERAL", "class_room": self.class_a.id}
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_class_group_endpoint_creates_and_joins_all_classmates(self):
        self.client.force_authenticate(self.student1_user)
        response = self.client.get("/api/v1/chat/class_group/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        room_id = response.data["id"]
        self.assertEqual(response.data["room_type"], "CLASS_GENERAL")

        room = ChatRoom.objects.get(pk=room_id)
        member_user_ids = set(room.members.values_list("user_id", flat=True))
        self.assertEqual(member_user_ids, {self.student1_user.id, self.student2_user.id})
        self.assertNotIn(self.other_class_user.id, member_user_ids)

        # Calling again returns the same room (idempotent) instead of duplicating it.
        second_response = self.client.get("/api/v1/chat/class_group/")
        self.assertEqual(second_response.data["id"], room_id)
        self.assertEqual(ChatRoom.objects.filter(room_type="CLASS_GENERAL", class_room=self.class_a).count(), 1)

    def test_other_class_student_gets_own_separate_group(self):
        self.client.force_authenticate(self.student1_user)
        self.client.get("/api/v1/chat/class_group/")

        self.client.force_authenticate(self.other_class_user)
        response = self.client.get("/api/v1/chat/class_group/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        room = ChatRoom.objects.get(pk=response.data["id"])
        self.assertEqual(room.class_room_id, self.class_b.id)
        self.assertEqual(list(room.members.values_list("user_id", flat=True)), [self.other_class_user.id])
