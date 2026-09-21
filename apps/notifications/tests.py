from rest_framework import status
from rest_framework.test import APITestCase

from apps.users.models import User

from .models import Announcement, Notification, NotificationType


class NotificationAPITests(APITestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username="u1", password="Str0ngPass!23", role=User.Role.STUDENT)
        self.user2 = User.objects.create_user(username="u2", password="Str0ngPass!23", role=User.Role.STUDENT)
        self.admin = User.objects.create_user(username="admin", password="Str0ngPass!23", role=User.Role.ADMIN)
        Notification.objects.create(user=self.user1, title="T1", message="M1", type=NotificationType.GRADE)
        Notification.objects.create(user=self.user2, title="T2", message="M2", type=NotificationType.GRADE)

    def test_user_only_sees_own_notifications(self):
        self.client.force_authenticate(self.user1)
        response = self.client.get("/api/v1/notifications/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)

    def test_mark_all_read(self):
        self.client.force_authenticate(self.user1)
        response = self.client.post("/api/v1/notifications/mark_all_read/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(Notification.objects.filter(user=self.user1, is_read=False).exists())

    def test_only_admin_can_create_announcement(self):
        self.client.force_authenticate(self.user1)
        response = self.client.post(
            "/api/v1/notifications/announcements/", {"title": "E'lon", "content": "Matn"}
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_authenticate(self.admin)
        response = self.client.post(
            "/api/v1/notifications/announcements/", {"title": "E'lon", "content": "Matn"}
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Announcement.objects.count(), 1)
