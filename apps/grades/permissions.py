from rest_framework.permissions import SAFE_METHODS, BasePermission

from common import access, rbac
from common.rbac import (
    CREATE_GRADE,
    DELETE_GRADE,
    MANAGE_ACADEMIC_RECORDS,
    UPDATE_GRADE,
    VIEW_ALL_GRADES,
    VIEW_ASSIGNED_GRADES,
    VIEW_CHILD_GRADES,
    VIEW_CLASS_REPORTS,
    VIEW_OWN_GRADES,
)

GRADE_VIEW_PERMISSIONS = (
    VIEW_ALL_GRADES,
    VIEW_OWN_GRADES,
    VIEW_CHILD_GRADES,
    VIEW_ASSIGNED_GRADES,
    VIEW_CLASS_REPORTS,
)

_WRITE_PERMISSION = {"POST": CREATE_GRADE, "PUT": UPDATE_GRADE, "PATCH": UPDATE_GRADE, "DELETE": DELETE_GRADE}


class CanManageGrade(BasePermission):
    """Reading needs one of the ``view_*_grades`` permissions; writing needs the matching
    ``create_grade`` / ``update_grade`` / ``delete_grade``.

    SUPERADMIN can only look at grades (via the class -> student -> subject drill-down) —
    it holds no write permission. Directors / deputy directors are read-only as well. A
    school-wide writer (admin) is confined to their own school; a teacher may only change
    a grade they gave themselves."""

    def has_permission(self, request, view):
        user = request.user
        if not (user and user.is_authenticated):
            return False
        if request.method in SAFE_METHODS:
            return rbac.has_any_perm(user, *GRADE_VIEW_PERMISSIONS)
        needed = _WRITE_PERMISSION.get(request.method)
        return needed is not None and rbac.has_perm(user, needed)

    def has_object_permission(self, request, view, obj):
        user = request.user
        if request.method in SAFE_METHODS:
            from .models import Grade

            return access.grades_scope(user, Grade.objects.filter(pk=obj.pk)).exists()
        if rbac.has_perm(user, MANAGE_ACADEMIC_RECORDS):
            # school-wide writer (admin): only inside their own school
            return access.same_school(user, obj.student.school_id)
        # a teacher only changes a grade they gave themselves
        return bool(obj.teacher and obj.teacher.user_id == user.id)
