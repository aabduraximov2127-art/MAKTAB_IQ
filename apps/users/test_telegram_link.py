from django.core.cache import cache
from rest_framework.test import APITestCase

from .models import User
from .telegram_link import LINK_BLOCKED, LINK_INVALID, LINK_OK, MAX_WRONG_ATTEMPTS, issue_code, link_with_code


class TelegramLinkTests(APITestCase):
    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user(username="u1", password="Str0ngPass!23", role=User.Role.STUDENT)
        self.other = User.objects.create_user(username="u2", password="Str0ngPass!23", role=User.Role.TEACHER)

    def test_website_issues_code_and_bot_code_links_account(self):
        self.client.force_authenticate(self.user)
        response = self.client.post("/api/v1/users/me/telegram-link-code/")
        self.assertEqual(response.status_code, 200)
        code = response.data["code"]
        self.assertEqual(len(code), 6)

        self.assertFalse(self.client.get("/api/v1/users/me/telegram-status/").data["linked"])
        self.assertFalse(self.client.get("/api/v1/users/me/").data["telegram_linked"])

        status, user = link_with_code(code, 12345)  # what the bot calls
        self.assertEqual(status, LINK_OK)
        self.assertEqual(user.id, self.user.id)

        # a real JWT request loads the user fresh from the DB on every call
        self.client.force_authenticate(User.objects.get(pk=self.user.pk))
        self.assertTrue(self.client.get("/api/v1/users/me/telegram-status/").data["linked"])
        self.assertTrue(self.client.get("/api/v1/users/me/").data["telegram_linked"])
        self.user.refresh_from_db()
        self.assertEqual(self.user.telegram_chat_id, "12345")

    def test_code_is_single_use(self):
        code = issue_code(self.user)
        self.assertEqual(link_with_code(code, 1)[0], LINK_OK)
        self.assertEqual(link_with_code(code, 2)[0], LINK_INVALID)

    def test_wrong_code_is_rejected(self):
        issue_code(self.user)
        status, user = link_with_code("000000", 1)
        self.assertEqual(status, LINK_INVALID)
        self.assertIsNone(user)
        self.assertEqual(link_with_code("abc", 1)[0], LINK_INVALID)

    def test_new_code_invalidates_previous_one(self):
        first = issue_code(self.user)
        second = issue_code(self.user)
        self.assertNotEqual(first, second)
        self.assertEqual(link_with_code(first, 1)[0], LINK_INVALID)
        self.assertEqual(link_with_code(second, 1)[0], LINK_OK)

    def test_brute_force_is_blocked_per_chat(self):
        code = issue_code(self.user)
        for _ in range(MAX_WRONG_ATTEMPTS):
            link_with_code("999999" if code != "999999" else "999998", 7)
        self.assertEqual(link_with_code(code, 7)[0], LINK_BLOCKED)
        self.assertEqual(link_with_code(code, 8)[0], LINK_OK)  # another chat is unaffected

    def test_chat_moves_to_new_account_instead_of_crashing_on_unique(self):
        link_with_code(issue_code(self.user), 555)
        link_with_code(issue_code(self.other), 555)
        self.user.refresh_from_db()
        self.other.refresh_from_db()
        self.assertIsNone(self.user.telegram_chat_id)
        self.assertEqual(self.other.telegram_chat_id, "555")

    def test_unlink_endpoint(self):
        link_with_code(issue_code(self.user), 42)
        self.client.force_authenticate(self.user)
        response = self.client.post("/api/v1/users/me/telegram-unlink/")
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertIsNone(self.user.telegram_chat_id)
