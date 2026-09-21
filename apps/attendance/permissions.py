from rest_framework.permissions import SAFE_METHODS, BasePermission

from common.permissions import user_role


class CanManageAttendance(BasePermission):
    """SUPERADMIN has no place in attendance at all (student or teacher, view or
    write) — that's delegated entirely to ADMIN/TEACHER. STUDENT/PARENT keep
    reading their own records via the view-level queryset scoping."""

    def has_permission(self, request, view):
        role = user_role(request.user)
        if role == "SUPERADMIN":
            return False
        if request.method in SAFE_METHODS:
            return True
        return role in {"ADMIN", "TEACHER"}


class CanSubmitParentReason(BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.student.parent_links.filter(parent__user=request.user).exists()


class CanAccessTeacherAttendance(BasePermission):
    """SUPERADMIN is excluded entirely; ADMIN marks it, TEACHER may only read
    their own record (enforced via the view's queryset)."""

    def has_permission(self, request, view):
        role = user_role(request.user)
        if role == "SUPERADMIN":
            return False
        if request.method in SAFE_METHODS:
            return role in {"ADMIN", "TEACHER"}
        return role == "ADMIN"
