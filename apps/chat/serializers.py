from rest_framework import serializers

from .models import ChatMember, ChatRoom, Message


class ChatMemberSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source="user.get_full_name", read_only=True)

    class Meta:
        model = ChatMember
        fields = ("id", "chat_room", "user", "user_name", "created_at")
        read_only_fields = ("id", "created_at")


class MessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.CharField(source="sender.get_full_name", read_only=True)

    class Meta:
        model = Message
        fields = ("id", "chat_room", "sender", "sender_name", "text", "attachment", "is_read", "created_at")
        read_only_fields = ("id", "sender", "is_read", "created_at")


class ChatRoomSerializer(serializers.ModelSerializer):
    members = ChatMemberSerializer(many=True, read_only=True)
    last_message = serializers.SerializerMethodField()

    class Meta:
        model = ChatRoom
        fields = ("id", "room_type", "name", "class_room", "members", "last_message", "created_at")
        read_only_fields = ("id", "created_at")

    def get_last_message(self, obj):
        message = obj.messages.order_by("-created_at").first()
        return MessageSerializer(message).data if message else None
