from rest_framework.permissions import BasePermission

from common.permissions import user_role


class CanManageLibrary(BasePermission):
    """SUPERADMIN may only browse the library, never upload/edit/delete —
    that's left to ADMIN/TEACHER."""

    def has_permission(self, request, view):
        return user_role(request.user) in {"ADMIN", "TEACHER"}
