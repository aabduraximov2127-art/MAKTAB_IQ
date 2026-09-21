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
