"""Linking a MaktabIQ account to a Telegram chat.

Flow: the website issues a one-time 6-digit code (``issue_code``). The user sends it to the
bot (``/link 123456``, ``/start 123456`` or just ``123456``). The bot calls ``link_with_code``,
which checks the code against the one the website stored and, if it matches, saves the
chat id on the user — the website then sees ``telegram_linked = true``.
"""

import secrets

from django.core.cache import cache

CODE_TTL = 600  # seconds
MAX_WRONG_ATTEMPTS = 8  # per Telegram chat per CODE_TTL window

LINK_OK = "ok"
LINK_INVALID = "invalid"
LINK_BLOCKED = "blocked"
LINK_NO_USER = "no_user"


def _code_key(code):
    return f"telegram_link:{code}"


def _user_key(user_id):
    return f"telegram_link_user:{user_id}"


def issue_code(user):
    """Create a fresh code for ``user`` (invalidating any earlier unused one)."""
    old = cache.get(_user_key(user.id))
    if old:
        cache.delete(_code_key(old))
    for _ in range(20):
        code = f"{secrets.randbelow(1_000_000):06d}"
        if cache.get(_code_key(code)) is None:
            break
    cache.set(_code_key(code), user.id, timeout=CODE_TTL)
    cache.set(_user_key(user.id), code, timeout=CODE_TTL)
    return code


def bind_chat_id(user, chat_id):
    """Attach ``chat_id`` to ``user``, stealing it from whoever else had it first.

    ``telegram_chat_id`` is unique, so a chat can only ever belong to one account —
    used both when a code is redeemed and when the Mini App links a Telegram-verified
    identity to a password login (see ``telegram_webapp.py``).
    """
    from .models import User

    chat_id = str(chat_id)
    User.objects.filter(telegram_chat_id=chat_id).exclude(id=user.id).update(telegram_chat_id=None)
    if user.telegram_chat_id != chat_id:
        user.telegram_chat_id = chat_id
        user.save(update_fields=["telegram_chat_id"])


def link_with_code(code, chat_id):
    """Verify ``code`` and bind ``chat_id`` to the user it was issued for.

    Returns ``(status, user_or_None)``.
    """
    from .models import User

    chat_id = str(chat_id)
    attempts_key = f"telegram_attempts:{chat_id}"
    attempts = cache.get(attempts_key, 0)
    if attempts >= MAX_WRONG_ATTEMPTS:
        return LINK_BLOCKED, None

    user_id = cache.get(_code_key(code)) if code and code.isdigit() else None
    if not user_id:
        cache.set(attempts_key, attempts + 1, timeout=CODE_TTL)
        return LINK_INVALID, None

    user = User.objects.filter(id=user_id).first()
    cache.delete(_code_key(code))
    cache.delete(_user_key(user_id))
    if user is None:
        return LINK_NO_USER, None

    bind_chat_id(user, chat_id)
    cache.delete(attempts_key)
    return LINK_OK, user


def unlink_user(user):
    user.telegram_chat_id = None
    user.save(update_fields=["telegram_chat_id"])


def notify_linked(user):
    """Tell the user (in-app + real-time) that Telegram is now connected."""
    from apps.notifications.models import Notification, NotificationType
    from common.realtime import push_notification_to_user

    notification = Notification.objects.create(
        user=user,
        title="Telegram ulandi",
        message="Hisobingiz Telegram botiga muvaffaqiyatli ulandi. Endi bildirishnomalarni shu yerda ham olasiz.",
        type=NotificationType.ANNOUNCEMENT,
    )
    push_notification_to_user(
        user.id,
        {
            "id": notification.id,
            "title": notification.title,
            "message": notification.message,
            "type": notification.type,
            "created_at": notification.created_at.isoformat(),
        },
    )
