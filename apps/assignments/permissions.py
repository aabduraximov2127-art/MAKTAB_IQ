from rest_framework.permissions import SAFE_METHODS, BasePermission

from common.permissions import user_role


class CanManageAssignment(BasePermission):
    """SUPERADMIN doesn't need homework at all — it's an ADMIN/TEACHER/STUDENT/
    PARENT concern. ADMIN (School Admin/Director) is confined to their own school."""

    def has_permission(self, request, view):
        role = user_role(request.user)
        if role == "SUPERADMIN":
            return False
        if request.method in SAFE_METHODS:
            return True
        return role in {"ADMIN", "TEACHER"}

    def has_object_permission(self, request, view, obj):
        role = user_role(request.user)
        if role == "ADMIN":
            return bool(request.user.school_id) and obj.lesson.class_room.school_id == request.user.school_id
        if request.method in SAFE_METHODS:
            return True
        return obj.teacher.user_id == request.user.id
