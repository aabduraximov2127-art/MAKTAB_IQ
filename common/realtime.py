from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer


def push_notification_to_user(user_id, payload):
    channel_layer = get_channel_layer()
    if channel_layer is None:
        return
    async_to_sync(channel_layer.group_send)(
        f"notifications_user_{user_id}",
        {"type": "notification.message", "payload": payload},
    )


def push_message_to_chat(chat_room_id, payload):
    channel_layer = get_channel_layer()
    if channel_layer is None:
        return
    async_to_sync(channel_layer.group_send)(
        f"chat_room_{chat_room_id}",
        {"type": "chat.message", "payload": payload},
    )


def push_message_deleted_to_chat(chat_room_id, message_id):
    """Tell everybody connected to the room that a message is gone (the chat page removes it)."""
    channel_layer = get_channel_layer()
    if channel_layer is None:
        return
    async_to_sync(channel_layer.group_send)(
        f"chat_room_{chat_room_id}",
        {"type": "chat.message", "payload": {"type": "message_deleted", "id": message_id, "chat_room": chat_room_id}},
    )
