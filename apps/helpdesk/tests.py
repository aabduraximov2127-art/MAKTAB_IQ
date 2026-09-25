from rest_framework import status
from rest_framework.test import APITestCase

from apps.users.models import User

from .models import HelpDeskTicket


class HelpDeskTicketTests(APITestCase):
    def setUp(self):
        self.student1 = User.objects.create_user(username="s1", password="Str0ngPass!23", role=User.Role.STUDENT)
        self.student2 = User.objects.create_user(username="s2", password="Str0ngPass!23", role=User.Role.STUDENT)
        self.admin = User.objects.create_user(username="admin", password="Str0ngPass!23", role=User.Role.ADMIN)

    def test_user_can_create_ticket(self):
        self.client.force_authenticate(self.student1)
        response = self.client.post(
            "/api/v1/helpdesk/", {"title": "Login muammosi", "description": "Kira olmayapman"}
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_user_cannot_see_others_ticket(self):
        ticket = HelpDeskTicket.objects.create(user=self.student1, title="T1", description="D1")
        self.client.force_authenticate(self.student2)
        response = self.client.get(f"/api/v1/helpdesk/{ticket.id}/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_sees_all_tickets(self):
        HelpDeskTicket.objects.create(user=self.student1, title="T1", description="D1")
        HelpDeskTicket.objects.create(user=self.student2, title="T2", description="D2")
        self.client.force_authenticate(self.admin)
        response = self.client.get("/api/v1/helpdesk/")
        self.assertEqual(response.data["count"], 2)
