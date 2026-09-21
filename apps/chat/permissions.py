from rest_framework.permissions import SAFE_METHODS, BasePermission

from common.permissions import user_role


class IsChatMember(BasePermission):
    def has_object_permission(self, request, view, obj):
        chat_room = obj if obj.__class__.__name__ == "ChatRoom" else obj.chat_room
        return chat_room.members.filter(user=request.user).exists()


class CanCreateChatRoom(BasePermission):
    """ADMIN/SUPERADMIN/TEACHER keep unrestricted room management (existing
    behavior). STUDENT may only POST a new PRIVATE room (membership to
    classmates is enforced separately in the view) — PATCH/DELETE stay closed."""

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        role = user_role(request.user)
        if role in {"ADMIN", "SUPERADMIN", "TEACHER"}:
            return True
        if role == "STUDENT" and request.method == "POST":
            return request.data.get("room_type") == "PRIVATE"
        return False
