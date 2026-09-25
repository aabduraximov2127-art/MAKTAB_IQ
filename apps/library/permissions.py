from rest_framework.permissions import BasePermission

from common import rbac
from common.rbac import MANAGE_LIBRARY, MANAGE_USERS


class CanManageLibrary(BasePermission):
    """Uploading / editing / deleting library material needs ``manage_library`` (teacher,
    admin); SUPERADMIN may only browse. Material is edited or removed by whoever uploaded it,
    or by a user administrator (``manage_users``)."""

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and rbac.has_perm(request.user, MANAGE_LIBRARY))

    def has_object_permission(self, request, view, obj):
        user = request.user
        return obj.uploaded_by_id == user.id or rbac.has_perm(user, MANAGE_USERS)
