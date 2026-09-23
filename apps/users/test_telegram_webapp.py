import hashlib
import hmac
import json
import time
from urllib.parse import urlencode

from django.test import SimpleTestCase, override_settings
from rest_framework.test import APITestCase

from .models import User
from .telegram_webapp import telegram_chat_id_from, verify_init_data

TEST_BOT_TOKEN = "123456:test-bot-token"


def sign_init_data(fields, bot_token=TEST_BOT_TOKEN):
    """Build a genuinely-signed initData string the way Telegram's client would."""
    check_pairs = list(fields.items())
    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(check_pairs))
    secret_key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    fields = dict(fields)
    fields["hash"] = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
    return urlencode(fields)


def make_init_data(tg_id=555, bot_token=TEST_BOT_TOKEN, **overrides):
    fields = {
        "query_id": "AAEfake",
        "user": json.dumps({"id": tg_id, "first_name": "Test", "username": "tguser"}),
        "auth_date": str(int(time.time())),
    }
    fields.update(overrides)
    return sign_init_data(fields, bot_token=bot_token)


@override_settings(TELEGRAM_BOT_TOKEN=TEST_BOT_TOKEN)
class VerifyInitDataTests(SimpleTestCase):
    def test_genuinely_signed_data_is_accepted(self):
        verified = verify_init_data(make_init_data(tg_id=42))
        self.assertIsNotNone(verified)
        self.assertEqual(verified["user"]["id"], 42)
        self.assertEqual(telegram_chat_id_from(verified), "42")

    def test_tampered_field_is_rejected(self):
        raw = make_init_data(tg_id=42)
        tampered = raw.replace("Test", "Mall") if "Test" in raw else raw + "x"
        self.assertIsNone(verify_init_data(tampered))

    def test_wrong_bot_token_is_rejected(self):
        signed_by_someone_else = make_init_data(tg_id=42, bot_token="999:someone-elses-token")
        self.assertIsNone(verify_init_data(signed_by_someone_else))

    def test_missing_hash_is_rejected(self):
        self.assertIsNone(verify_init_data("query_id=x&auth_date=123"))

    def test_expired_auth_date_is_rejected(self):
        stale = make_init_data(tg_id=42, auth_date=str(int(time.time()) - 999_999))
        self.assertIsNone(verify_init_data(stale))

    def test_future_auth_date_is_rejected(self):
        future = make_init_data(tg_id=42, auth_date=str(int(time.time()) + 999_999))
        self.assertIsNone(verify_init_data(future))

    def test_blank_or_missing_init_data(self):
        self.assertIsNone(verify_init_data(""))
        self.assertIsNone(verify_init_data(None))

    def test_no_bot_token_configured_rejects_everything(self):
        with override_settings(TELEGRAM_BOT_TOKEN=""):
            self.assertIsNone(verify_init_data(make_init_data(tg_id=42)))

    def test_malformed_user_json_is_rejected(self):
        raw = sign_init_data({"user": "{not json", "auth_date": str(int(time.time()))})
        self.assertIsNone(verify_init_data(raw))


@override_settings(TELEGRAM_BOT_TOKEN=TEST_BOT_TOKEN)
class TelegramAuthViewTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="linked", password="Str0ngPass!23", role=User.Role.STUDENT, telegram_chat_id="777",
        )

    def test_linked_chat_gets_signed_in_silently(self):
        response = self.client.post("/api/v1/auth/telegram/", {"init_data": make_init_data(tg_id=777)})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["linked"])
        self.assertIn("access", response.data)

        me = self.client.get("/api/v1/users/me/", HTTP_AUTHORIZATION=f"Bearer {response.data['access']}")
        self.assertEqual(me.data["username"], "linked")

    def test_unlinked_chat_reports_not_linked_without_tokens(self):
        response = self.client.post("/api/v1/auth/telegram/", {"init_data": make_init_data(tg_id=999)})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.data["linked"])
        self.assertNotIn("access", response.data)

    def test_invalid_init_data_is_rejected(self):
        response = self.client.post("/api/v1/auth/telegram/", {"init_data": "garbage"})
        self.assertEqual(response.status_code, 400)

    def test_deactivated_linked_user_is_not_signed_in(self):
        self.user.is_deactivated = True
        self.user.save(update_fields=["is_deactivated"])
        response = self.client.post("/api/v1/auth/telegram/", {"init_data": make_init_data(tg_id=777)})
        self.assertFalse(response.data["linked"])


@override_settings(TELEGRAM_BOT_TOKEN=TEST_BOT_TOKEN)
class TelegramWebAppLoginViewTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="alice", password="Str0ngPass!23", role=User.Role.STUDENT)

    def _login(self, tg_id, username, password):
        return self.client.post(
            "/api/v1/auth/telegram/login/",
            {"init_data": make_init_data(tg_id=tg_id), "username": username, "password": password},
        )

    def test_correct_credentials_link_and_return_tokens(self):
        response = self._login(111, "alice", "Str0ngPass!23")
        self.assertEqual(response.status_code, 200)
        self.assertIn("access", response.data)
        self.user.refresh_from_db()
        self.assertEqual(self.user.telegram_chat_id, "111")

    def test_wrong_password_is_rejected_and_not_linked(self):
        response = self._login(111, "alice", "wrong-password")
        self.assertEqual(response.status_code, 400)
        self.user.refresh_from_db()
        self.assertIsNone(self.user.telegram_chat_id)

    def test_tampered_init_data_is_rejected_even_with_right_password(self):
        raw = make_init_data(tg_id=111) + "0"
        response = self.client.post(
            "/api/v1/auth/telegram/login/", {"init_data": raw, "username": "alice", "password": "Str0ngPass!23"}
        )
        self.assertEqual(response.status_code, 400)

    def test_relinking_moves_chat_from_previous_owner(self):
        other = User.objects.create_user(
            username="bob", password="Str0ngPass!23", role=User.Role.STUDENT, telegram_chat_id="222",
        )
        response = self._login(222, "alice", "Str0ngPass!23")
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        other.refresh_from_db()
        self.assertEqual(self.user.telegram_chat_id, "222")
        self.assertIsNone(other.telegram_chat_id)

    def test_deactivated_account_cannot_link(self):
        self.user.is_deactivated = True
        self.user.save(update_fields=["is_deactivated"])
        response = self._login(111, "alice", "Str0ngPass!23")
        self.assertEqual(response.status_code, 400)
