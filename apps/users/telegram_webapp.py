"""Verifying Telegram Mini App (WebApp) ``initData``.

When a user opens the Mini App, Telegram hands the frontend a signed ``initData`` string
proving *which* Telegram account opened it — signed with the bot token, so only Telegram
(or someone holding the bot token) could have produced it. The backend re-derives the same
signature and compares, exactly as documented at
https://core.telegram.org/bots/webapps#validating-data-received-via-the-web-app

This is what lets the Mini App sign a user in without typing a password: Telegram has
already proven the identity, so once that Telegram chat is linked to a MaktabIQ account
(see ``telegram_link.py``), we can issue that account's JWT straight away.
"""

import hashlib
import hmac
import json
import time

from django.conf import settings

# How long a signed initData stays acceptable. Telegram re-signs it fresh every time the
# Mini App is opened, so this only bounds how long a captured initData string could be
# replayed to mint a session — not how long the resulting JWT lasts.
MAX_AUTH_AGE_SECONDS = 24 * 60 * 60


def _parse_query_string(raw):
    """Minimal, defensive query-string parser (avoids stdlib's ``strict_parsing`` edge cases
    on malformed input — we simply reject anything that doesn't split cleanly)."""
    from urllib.parse import unquote_plus

    pairs = []
    for part in raw.split("&"):
        if not part:
            continue
        if "=" not in part:
            return None
        key, _, value = part.partition("=")
        pairs.append((unquote_plus(key), unquote_plus(value)))
    return pairs


def _expected_hash(pairs, bot_token):
    data_check_string = "\n".join(f"{key}={value}" for key, value in sorted(pairs))
    secret_key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    return hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()


def verify_init_data(init_data, *, max_age=MAX_AUTH_AGE_SECONDS):
    """Return the parsed fields (with ``user`` decoded to a dict) if ``init_data`` is
    genuinely signed by Telegram with our bot token and still fresh; ``None`` otherwise.

    Never raises: any malformed or unexpected input is simply "not verified".
    """
    bot_token = settings.TELEGRAM_BOT_TOKEN
    if not bot_token or not init_data or not isinstance(init_data, str):
        return None

    pairs = _parse_query_string(init_data)
    if pairs is None:
        return None

    received_hash = None
    check_pairs = []
    for key, value in pairs:
        if key == "hash":
            received_hash = value
        else:
            check_pairs.append((key, value))
    if not received_hash:
        return None

    if not hmac.compare_digest(_expected_hash(check_pairs, bot_token), received_hash):
        return None

    data = dict(check_pairs)
    try:
        auth_date = int(data["auth_date"])
    except (KeyError, ValueError):
        return None
    if abs(time.time() - auth_date) > max_age:
        return None

    if "user" in data:
        try:
            data["user"] = json.loads(data["user"])
        except (json.JSONDecodeError, TypeError):
            return None

    return data


def telegram_chat_id_from(verified_data):
    """The id to store/match against ``User.telegram_chat_id``, from already-verified
    initData. For a private chat with the bot, the chat id equals the user's own Telegram
    id — the same id the bot itself uses when it processes ``/link`` (see bot/bot.py)."""
    user = verified_data.get("user") if verified_data else None
    tg_id = user.get("id") if isinstance(user, dict) else None
    return str(tg_id) if tg_id is not None else None
