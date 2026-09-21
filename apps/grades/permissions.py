from rest_framework.permissions import SAFE_METHODS, BasePermission

from common.permissions import user_role


class CanManageGrade(BasePermission):
    """SUPERADMIN can only look at grades (via the class -> student -> subject
    drill-down) — never create/edit them. That stays with ADMIN/TEACHER.
    ADMIN (School Admin/Director) is confined to their own school; SUPERADMIN
    stays global/unrestricted."""

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return user_role(request.user) in {"ADMIN", "TEACHER"}

    def has_object_permission(self, request, view, obj):
        role = user_role(request.user)
        if role == "SUPERADMIN":
            return True
        if role == "ADMIN":
            return bool(request.user.school_id) and obj.student.school_id == request.user.school_id
        if request.method in SAFE_METHODS:
            return self._can_view(request.user, role, obj)
        if role == "TEACHER":
            return obj.teacher and obj.teacher.user_id == request.user.id
        return False

    def _can_view(self, user, role, obj):
        if role == "STUDENT":
            return obj.student.user_id == user.id
        if role == "PARENT":
            return obj.student.parent_links.filter(parent__user=user).exists()
        if role == "TEACHER":
            return obj.teacher and obj.teacher.user_id == user.id
        return False
