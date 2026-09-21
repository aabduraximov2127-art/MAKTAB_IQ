from django.shortcuts import get_object_or_404
from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from common.permissions import user_role
from common.realtime import push_message_to_chat

from .models import ChatMember, ChatRoom, Message
from .permissions import CanCreateChatRoom, IsChatMember
from .services import moderate_message
from .serializers import ChatMemberSerializer, ChatRoomSerializer, MessageSerializer


class ChatRoomViewSet(viewsets.ModelViewSet):
    serializer_class = ChatRoomSerializer
    permission_classes = [permissions.IsAuthenticated, CanCreateChatRoom]

    def get_queryset(self):
        return ChatRoom.objects.filter(members__user=self.request.user).distinct().prefetch_related("members")

    def perform_create(self, serializer):
        room = serializer.save()
        ChatMember.objects.get_or_create(chat_room=room, user=self.request.user)

    @action(detail=True, methods=["post"], permission_classes=[permissions.IsAuthenticated])
    def add_member(self, request, pk=None):
        room = get_object_or_404(ChatRoom, pk=pk)
        role = user_role(request.user)
        target_id = request.data.get("user")

        if role not in {"ADMIN", "SUPERADMIN", "TEACHER"}:
            if role != "STUDENT" or not room.members.filter(user=request.user).exists():
                self.permission_denied(request)
            from apps.users.models import StudentProfile

            class_room_id = getattr(
                getattr(request.user, "student_profile", None), "class_room_id", None
            )
            is_classmate = bool(class_room_id) and StudentProfile.objects.filter(
                user_id=target_id, class_room_id=class_room_id
            ).exists()
            if not is_classmate:
                self.permission_denied(request)

        member, created = ChatMember.objects.get_or_create(chat_room=room, user_id=target_id)
        return Response(ChatMemberSerializer(member).data, status=201 if created else 200)

    @action(detail=False, methods=["get"])
    def class_group(self, request):
        """Get-or-create the student's own class group chat and make sure every
        current classmate is a member. STUDENT-only — everyone else's chat
        management is untouched."""
        if user_role(request.user) != "STUDENT":
            self.permission_denied(request)

        from apps.users.models import StudentProfile

        class_room = getattr(getattr(request.user, "student_profile", None), "class_room", None)
        if class_room is None:
            return Response(
                {"success": False, "message": "Sizga sinf biriktirilmagan", "errors": {}}, status=400
            )

        room, _created = ChatRoom.objects.get_or_create(
            room_type=ChatRoom.RoomType.CLASS_GENERAL,
            class_room=class_room,
            defaults={"name": f"{class_room.name} sinf chati"},
        )
        existing_member_ids = set(room.members.values_list("user_id", flat=True))
        classmate_ids = set(
            StudentProfile.objects.filter(class_room=class_room).values_list("user_id", flat=True)
        )
        missing = classmate_ids - existing_member_ids
        if missing:
            ChatMember.objects.bulk_create([ChatMember(chat_room=room, user_id=uid) for uid in missing])

        return Response(ChatRoomSerializer(room).data)


class MessageViewSet(viewsets.ModelViewSet):
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated, IsChatMember]
    filterset_fields = ["chat_room"]

    def get_queryset(self):
        role = user_role(self.request.user)
        if role == "SUPERADMIN":
            return Message.objects.select_related("sender", "chat_room")
        if role == "ADMIN":
            # Moderation view: messages in any chat that has at least one member
            # from the Admin/Director's own school.
            return Message.objects.filter(
                chat_room__members__user__school=self.request.user.school
            ).distinct().select_related("sender", "chat_room")
        return Message.objects.filter(chat_room__members__user=self.request.user).select_related(
            "sender", "chat_room"
        )

    def perform_create(self, serializer):
        chat_room = serializer.validated_data["chat_room"]
        self.check_object_permissions(self.request, chat_room)
        message = serializer.save(sender=self.request.user)
        push_message_to_chat(
            chat_room.id,
            {
                "id": message.id,
                "chat_room": chat_room.id,
                "sender": message.sender_id,
                "sender_name": message.sender.get_full_name(),
                "text": message.text,
                "created_at": message.created_at.isoformat(),
            },
        )
        moderate_message(message)
