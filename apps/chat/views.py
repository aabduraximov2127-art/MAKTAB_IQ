import logging

from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from common import access, rbac
from common.rbac import CREATE_CHAT_ROOMS, CREATE_PRIVATE_CHAT, MODERATE_CHAT, USE_STAFF_CHAT, VIEW_CLASSMATES
from common.audit import log_action
from common.realtime import push_message_deleted_to_chat, push_message_to_chat
from common.guards import ForbidOutOfScopeMixin

from .models import ChatMember, ChatRoom, Message
from .permissions import CanCreateChatRoom, CanUseChat, IsChatMember, IsMessageAuthor
from .services import deletion_snapshot, moderate_message, staff_members, sync_staff_room
from .serializers import ChatMemberSerializer, ChatRoomSerializer, MessageSerializer


logger = logging.getLogger(__name__)


class ChatRoomViewSet(ForbidOutOfScopeMixin, viewsets.ModelViewSet):
    serializer_class = ChatRoomSerializer
    permission_classes = [permissions.IsAuthenticated, CanCreateChatRoom]

    def get_queryset(self):
        return ChatRoom.objects.filter(members__user=self.request.user).distinct().prefetch_related("members")

    def list(self, request, *args, **kwargs):
        # Staff always find the shared staff room in their list, with membership kept in step
        # with the current staff.
        if rbac.has_perm(request.user, USE_STAFF_CHAT):
            sync_staff_room(request.user)
        return super().list(request, *args, **kwargs)

    def perform_create(self, serializer):
        if serializer.validated_data.get("room_type") == ChatRoom.RoomType.STAFF_GENERAL:
            self.permission_denied(self.request, message="Xodimlar xonasi avtomatik yaratiladi.")
        room = serializer.save()
        ChatMember.objects.get_or_create(chat_room=room, user=self.request.user)

    def _guard_staff_room(self, room):
        if room.room_type == ChatRoom.RoomType.STAFF_GENERAL and not rbac.has_perm(self.request.user, MODERATE_CHAT):
            self.permission_denied(self.request, message="Xodimlar xonasini o'zgartirib yoki o'chirib bo'lmaydi.")

    def perform_update(self, serializer):
        self._guard_staff_room(serializer.instance)
        serializer.save()

    def perform_destroy(self, instance):
        self._guard_staff_room(instance)
        instance.delete()

    @action(detail=False, methods=["get"])
    def staff(self, request):
        """Colleagues (staff of the caller's school) a private chat can be started with — the
        picker behind "Ustozga yozish"."""
        if not rbac.has_perm(request.user, USE_STAFF_CHAT):
            self.permission_denied(request)
        people = staff_members(request.user).exclude(pk=request.user.pk).order_by("first_name", "last_name", "id")
        search = (request.query_params.get("search") or "").strip()
        if search:
            people = people.filter(Q(first_name__icontains=search) | Q(last_name__icontains=search) | Q(username__icontains=search))
        return Response(
            [
                {
                    "id": person.id,
                    "name": person.get_full_name() or person.username,
                    "role": "DIRECTOR" if person.role == person.Role.DIRECTOR else "TEACHER",
                }
                for person in people
            ]
        )

    @action(detail=False, methods=["get"])
    def staff_room(self, request):
        """The staff room of the caller's school (created / synced on demand)."""
        if not rbac.has_perm(request.user, USE_STAFF_CHAT):
            self.permission_denied(request)
        return Response(ChatRoomSerializer(sync_staff_room(request.user)).data)

    @action(detail=True, methods=["post"], permission_classes=[permissions.IsAuthenticated, CanUseChat])
    def add_member(self, request, pk=None):
        room = get_object_or_404(ChatRoom, pk=pk)
        user = request.user
        target_id = request.data.get("user")
        if room.room_type == ChatRoom.RoomType.STAFF_GENERAL:
            self.permission_denied(request, message="Xodimlar xonasi a'zolari avtomatik boshqariladi.")
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
    """Chat messages: members read and send; the AUTHOR may delete their own message (and only
    theirs). Editing is not offered — a text changed after posting would dodge the swearing check.
    Deleting tells the school director and the class teacher (curator) on Telegram — and only them —
    what was deleted, by whom and in which chat; the other members just see the message disappear."""

    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated, CanUseChat, IsChatMember, IsMessageAuthor]
    filterset_fields = ["chat_room"]
    http_method_names = ["get", "post", "delete", "head", "options"]

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

    def perform_destroy(self, instance):
        from apps.notifications.tasks import notify_message_deleted

        snapshot = deletion_snapshot(instance)  # the text is gone with the row, so keep it for the alert
        room_id, message_id = instance.chat_room_id, instance.id
        if instance.attachment:
            instance.attachment.delete(save=False)
        instance.delete()

        log_action(
            self.request.user,
            "CHAT_MESSAGE_DELETED",
            target=f"chat {room_id}",
            description=f"message={message_id} flagged={snapshot['flagged']}",
            request=self.request,
        )
        # The message is already gone: a failing live push or alert must not turn the delete into an error.
        try:
            push_message_deleted_to_chat(room_id, message_id)
        except Exception:  # noqa: BLE001
            logger.exception("Could not push the deletion of message %s to the chat room", message_id)
        try:
            notify_message_deleted.delay(snapshot)
        except Exception:  # noqa: BLE001
            logger.exception("Could not send the 'message deleted' alert for message %s", message_id)
