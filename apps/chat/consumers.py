import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer

from .models import ChatRoom, Message
from .services import moderate_message


class ChatConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        user = self.scope["user"]
        self.room_id = self.scope["url_route"]["kwargs"]["room_id"]
        self.group_name = f"chat_room_{self.room_id}"

        if not user or not user.is_authenticated or not await self._is_member(user):
            await self.close()
            return

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data=None, bytes_data=None):
        if not text_data:
            return
        data = json.loads(text_data)
        text = data.get("text", "")
        if not text:
            return

        message = await self._create_message(text)
        await self.channel_layer.group_send(
            self.group_name,
            {
                "type": "chat.message",
                "payload": {
                    "id": message.id,
                    "chat_room": int(self.room_id),
                    "sender": self.scope["user"].id,
                    "sender_name": self.scope["user"].get_full_name(),
                    "text": message.text,
                    "created_at": message.created_at.isoformat(),
                },
            },
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps(event["payload"]))

    @database_sync_to_async
    def _is_member(self, user):
        return ChatRoom.objects.filter(id=self.room_id, members__user=user).exists()

    @database_sync_to_async
    def _create_message(self, text):
        message = Message.objects.create(chat_room_id=self.room_id, sender=self.scope["user"], text=text)
        moderate_message(message)
        return message
