from rest_framework.permissions import SAFE_METHODS, BasePermission

from common import access, rbac
from common.rbac import (
    MANAGE_CLASS_ATTENDANCE,
    MARK_ATTENDANCE,
    MARK_TEACHER_ATTENDANCE,
    SUBMIT_ABSENCE_REASON,
    UPDATE_ATTENDANCE,
    VIEW_ALL_ATTENDANCE,
    VIEW_ASSIGNED_ATTENDANCE,
    VIEW_CHILD_ATTENDANCE,
    VIEW_CLASS_REPORTS,
    VIEW_OWN_ATTENDANCE,
    VIEW_OWN_TEACHER_ATTENDANCE,
)

ATTENDANCE_VIEW_PERMISSIONS = (
    VIEW_ALL_ATTENDANCE,
    VIEW_OWN_ATTENDANCE,
    VIEW_CHILD_ATTENDANCE,
    VIEW_ASSIGNED_ATTENDANCE,
    VIEW_CLASS_REPORTS,
)


class CanManageAttendance(BasePermission):
    """Student attendance. Reading needs one of the ``view_*_attendance`` permissions;
    creating needs ``mark_attendance`` (or ``manage_class_attendance`` for a curator);
    changing/deleting needs ``update_attendance`` (or ``manage_class_attendance``).

    SUPERADMIN has no place in attendance at all (student or teacher, view or write) — it
    simply holds none of these permissions. STUDENT/PARENT read their own records; the
    queryset scoping (``access.attendance_scope``) decides *which* rows."""

    def has_permission(self, request, view):
        user = request.user
        if not (user and user.is_authenticated):
            return False
        if request.method in SAFE_METHODS:
            return rbac.has_any_perm(user, *ATTENDANCE_VIEW_PERMISSIONS)
        if request.method == "POST":
            return rbac.has_any_perm(user, MARK_ATTENDANCE, MANAGE_CLASS_ATTENDANCE)
        return rbac.has_any_perm(user, UPDATE_ATTENDANCE, MANAGE_CLASS_ATTENDANCE)

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True  # rows are already limited by the view's queryset
        return access.can_write_attendance(request.user, obj)


class CanSubmitParentReason(BasePermission):
    """A parent explains their own child's absence (``submit_absence_reason``)."""

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and rbac.has_perm(request.user, SUBMIT_ABSENCE_REASON))

    def has_object_permission(self, request, view, obj):
        return obj.student.parent_links.filter(parent__user=request.user).exists()


class CanAccessTeacherAttendance(BasePermission):
    """Teachers' own work attendance. Viewing: school-wide viewers (admin, director, deputy
    director) or a teacher for their own record (``view_own_teacher_attendance``); marking:
    ``mark_teacher_attendance`` (admin) only. SUPERADMIN is excluded entirely."""

    def has_permission(self, request, view):
        user = request.user
        if not (user and user.is_authenticated):
            return False
        if request.method in SAFE_METHODS:
            return rbac.has_any_perm(user, VIEW_ALL_ATTENDANCE, VIEW_OWN_TEACHER_ATTENDANCE)
        return rbac.has_perm(user, MARK_TEACHER_ATTENDANCE)
