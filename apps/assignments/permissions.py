from rest_framework.permissions import SAFE_METHODS, BasePermission

from common import access, rbac
from common.rbac import (
    CREATE_HOMEWORK,
    DELETE_HOMEWORK,
    MANAGE_CLASS_HOMEWORK,
    UPDATE_HOMEWORK,
    VIEW_ALL_HOMEWORK,
    VIEW_ASSIGNED_HOMEWORK,
    VIEW_CHILD_HOMEWORK,
    VIEW_CLASS_REPORTS,
    VIEW_OWN_HOMEWORK,
)

HOMEWORK_VIEW_PERMISSIONS = (
    VIEW_ALL_HOMEWORK,
    VIEW_OWN_HOMEWORK,
    VIEW_CHILD_HOMEWORK,
    VIEW_ASSIGNED_HOMEWORK,
    VIEW_CLASS_REPORTS,
)

_WRITE_PERMISSIONS = {
    "POST": (CREATE_HOMEWORK, MANAGE_CLASS_HOMEWORK),
    "PUT": (UPDATE_HOMEWORK, MANAGE_CLASS_HOMEWORK),
    "PATCH": (UPDATE_HOMEWORK, MANAGE_CLASS_HOMEWORK),
    "DELETE": (DELETE_HOMEWORK, MANAGE_CLASS_HOMEWORK),
}


class CanManageAssignment(BasePermission):
    """Homework. SUPERADMIN doesn't need homework at all — it holds no homework permission.
    Reading: ``view_*_homework``. Writing: ``create/update/delete_homework`` (a teacher on their
    own lessons, an admin inside their school) or ``manage_class_homework`` (a class teacher
    for their own class). Directors / deputy directors can read only."""

    def has_permission(self, request, view):
        user = request.user
        if not (user and user.is_authenticated):
            return False
        if request.method in SAFE_METHODS:
            return rbac.has_any_perm(user, *HOMEWORK_VIEW_PERMISSIONS)
        needed = _WRITE_PERMISSIONS.get(request.method)
        return needed is not None and rbac.has_any_perm(user, *needed)

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True  # limited to the user's scope by the view's queryset
        return can_write_assignment(request.user, obj)


def can_write_assignment(user, assignment) -> bool:
    """Edit/delete an existing assignment: its own teacher, the class teacher of that class,
    or a school-wide writer (admin) of the same school."""
    lesson = assignment.lesson
    if rbac.has_perm(user, MANAGE_CLASS_HOMEWORK) and access.curates(user, lesson.class_room):
        return True
    if rbac.has_perm(user, VIEW_ALL_HOMEWORK):
        return access.same_school(user, lesson.class_room.school_id)
    return assignment.teacher.user_id == user.id
