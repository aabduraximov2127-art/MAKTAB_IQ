from django.shortcuts import get_object_or_404
from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from common import access, rbac
from common.rbac import CREATE_CHAT_ROOMS, CREATE_PRIVATE_CHAT, MODERATE_CHAT, VIEW_CLASSMATES
from common.realtime import push_message_to_chat
from common.guards import ForbidOutOfScopeMixin

from .models import ChatMember, ChatRoom, Message
from .permissions import CanCreateChatRoom, CanUseChat, IsChatMember
from .services import moderate_message
from .serializers import ChatMemberSerializer, ChatRoomSerializer, MessageSerializer


class ChatRoomViewSet(ForbidOutOfScopeMixin, viewsets.ModelViewSet):
    serializer_class = ChatRoomSerializer
    permission_classes = [permissions.IsAuthenticated, CanCreateChatRoom]

    def get_queryset(self):
        return ChatRoom.objects.filter(members__user=self.request.user).distinct().prefetch_related("members")

    def perform_create(self, serializer):
        room = serializer.save()
        ChatMember.objects.get_or_create(chat_room=room, user=self.request.user)

    @action(detail=True, methods=["post"], permission_classes=[permissions.IsAuthenticated, CanUseChat])
    def add_member(self, request, pk=None):
        room = get_object_or_404(ChatRoom, pk=pk)
        user = request.user
        target_id = request.data.get("user")
        is_member = room.members.filter(user=user).exists()

        if rbac.has_perm(user, MODERATE_CHAT):
            pass  # admin / superadmin manage any room (existing behaviour)
        elif rbac.has_perm(user, CREATE_CHAT_ROOMS):
            # a teacher builds and manages rooms they are part of — not arbitrary ones
            if not is_member:
                self.permission_denied(request)
        else:
            if not rbac.has_perm(user, CREATE_PRIVATE_CHAT) or not is_member:
                self.permission_denied(request)
            from apps.users.models import StudentProfile

            class_room_id = access.own_class_id(user)
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
        if not rbac.has_perm(request.user, VIEW_CLASSMATES):
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


class MessageViewSet(ForbidOutOfScopeMixin, viewsets.ModelViewSet):
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated, CanUseChat, IsChatMember]
    filterset_fields = ["chat_room"]

    def get_queryset(self):
        user = self.request.user
        base = Message.objects.select_related("sender", "chat_room")
        if rbac.has_perm(user, MODERATE_CHAT):
            if rbac.is_global(user):
                return base
            # Moderation view: messages in any chat that has at least one member from the
            # admin's own school.
            return base.filter(chat_room__members__user__school=user.school).distinct()
        return base.filter(chat_room__members__user=user)

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
