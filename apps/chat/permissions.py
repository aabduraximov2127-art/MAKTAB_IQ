from rest_framework.permissions import SAFE_METHODS, BasePermission

from common import rbac
from common.rbac import CREATE_CHAT_ROOMS, CREATE_PRIVATE_CHAT, USE_CHAT


class IsChatMember(BasePermission):
    def has_object_permission(self, request, view, obj):
        chat_room = obj if obj.__class__.__name__ == "ChatRoom" else obj.chat_room
        return chat_room.members.filter(user=request.user).exists()


class CanUseChat(BasePermission):
    """Chat is for signed-in users holding ``use_chat`` (every role by default)."""

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and rbac.has_perm(request.user, USE_CHAT))


class CanCreateChatRoom(BasePermission):
    """``create_chat_rooms`` (admin, superadmin, teacher) keeps unrestricted room management.
    ``create_private_chat`` (student) may only POST a new PRIVATE room — membership of
    classmates is enforced separately in the view — PATCH/DELETE stay closed."""

    def has_permission(self, request, view):
        user = request.user
        if not (user and user.is_authenticated):
            return False
        if request.method in SAFE_METHODS:
            return rbac.has_perm(user, USE_CHAT)
        if rbac.has_perm(user, CREATE_CHAT_ROOMS):
            return True
        if request.method == "POST" and rbac.has_perm(user, CREATE_PRIVATE_CHAT):
            return request.data.get("room_type") == "PRIVATE"
        return False
