import logging

from .moderation import find_profanity
from .models import ModerationIncident

logger = logging.getLogger(__name__)


def moderate_message(message):
    """Flag ``message`` if it contains swearing/insults and alert the responsible teachers.

    Never raises: moderation must not break chat delivery.
    """
    try:
        words = find_profanity(message.text)
        if not words or message.sender_id is None:
            return None
        incident = ModerationIncident.objects.create(
            message=message, chat_room_id=message.chat_room_id, sender_id=message.sender_id, matched_words=words
        )
        from apps.notifications.tasks import notify_profanity_incident

        notify_profanity_incident.delay(incident.id)
        return incident
    except Exception:  # noqa: BLE001
        logger.exception("Chat moderation failed for message %s", getattr(message, "id", None))
        return None


STAFF_ROOM_NAME = "O'qituvchilar xonasi"
# Roles (stored or extra) that share the staff room and can be picked in "Ustozga yozish".
STAFF_ROOM_ROLES = ("TEACHER", "DIRECTOR")


def staff_members(user):
    """Active staff of ``user``'s school (``STAFF_ROOM_ROLES``, stored role or extra role)."""
    from django.contrib.auth import get_user_model
    from django.db.models import Q

    User = get_user_model()
    return (
        User.objects.filter(is_active=True, school_id=user.school_id)
        .filter(Q(role__in=STAFF_ROOM_ROLES) | Q(groups__name__in=STAFF_ROOM_ROLES))
        .distinct()
    )


def sync_staff_room(user):
    """Get-or-create the shared staff room of ``user``'s school and make its membership match
    the current staff exactly (new teachers join, removed ones leave).

    A room belongs to a school through its members — every member of a staff room comes from
    the same school — so no extra column is needed; ``school_id=None`` covers installs without
    schools. Called for every user holding ``use_staff_chat``.
    """
    from .models import ChatMember, ChatRoom

    staff_ids = set(staff_members(user).values_list("id", flat=True))
    staff_ids.add(user.id)

    room = (
        ChatRoom.objects.filter(room_type=ChatRoom.RoomType.STAFF_GENERAL, members__user__school_id=user.school_id)
        .order_by("id")
        .first()
    )
    if room is None:
        room = ChatRoom.objects.create(room_type=ChatRoom.RoomType.STAFF_GENERAL, name=STAFF_ROOM_NAME)

    current = set(room.members.values_list("user_id", flat=True))
    missing = staff_ids - current
    if missing:
        ChatMember.objects.bulk_create([ChatMember(chat_room=room, user_id=uid) for uid in missing])
    stale = current - staff_ids
    if stale:
        room.members.filter(user_id__in=stale).delete()
    return room
