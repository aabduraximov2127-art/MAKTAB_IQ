from rest_framework.permissions import SAFE_METHODS, BasePermission

from common import access, rbac
from common.rbac import (
    MANAGE_CLASS_STUDENTS,
    MANAGE_ROLES,
    MANAGE_STUDENTS,
    MANAGE_USERS,
    TRANSFER_STUDENTS,
    UPDATE_CHILD_PROFILE,
    UPDATE_OWN_PROFILE,
    VIEW_ALL_STUDENTS,
    VIEW_ASSIGNED_STUDENTS,
    VIEW_CHILD_PROFILE,
    VIEW_CLASS_STUDENTS,
    VIEW_CLASSMATES,
    VIEW_OWN_PROFILE,
    VIEW_SENSITIVE_STUDENT_DATA,
)

# Any of these lets a user open the student list (each then sees only its own scope).
STUDENT_LIST_PERMISSIONS = (
    VIEW_ALL_STUDENTS,
    VIEW_OWN_PROFILE,
    VIEW_CLASSMATES,
    VIEW_CHILD_PROFILE,
    VIEW_ASSIGNED_STUDENTS,
    VIEW_CLASS_STUDENTS,
)


same_school = access.same_school  # kept as a module-level name for backwards compatibility


def can_manage_user(actor, target) -> bool:
    """May ``actor`` administer (activate / deactivate / reset password / change roles of)
    ``target``? Needs ``manage_users``; school-bound admins stay inside their own school and
    can never touch a SUPERADMIN account."""
    if not rbac.has_perm(actor, MANAGE_USERS):
        return False
    if rbac.is_global(actor):
        return True
    if not access.same_school(actor, target.school_id):
        return False
    return not rbac.has_role(target, rbac.SUPERADMIN)


class IsSelfOrAdmin(BasePermission):
    """A user may act on their own account; users with ``manage_users`` may act on
    accounts they are allowed to administer."""

    def has_object_permission(self, request, view, obj):
        if obj.id == request.user.id:
            return True
        return can_manage_user(request.user, obj)


class CanViewSensitiveStudentData(BasePermission):
    """Passport/ID and health records: ``view_sensitive_student_data`` (admin/superadmin), or
    a staff account explicitly granted the Django permission of the same name."""

    def has_permission(self, request, view):
        user = request.user
        if not (user and user.is_authenticated):
            return False
        if rbac.has_perm(user, VIEW_SENSITIVE_STUDENT_DATA):
            return True
        return user.is_staff and user.has_perm("users.view_sensitive_student_data")


class CanAccessStudentProfile(BasePermission):
    """Student: self only. Parent: own children only. Teacher: students of classes they teach
    or curate. Class teacher: own class. Director / deputy / admin: their own school.
    Superadmin: everyone. (See ``common.access.can_view_student``.)"""

    def has_object_permission(self, request, view, obj):
        return access.can_view_student(request.user, obj)


class CanTransferStudent(BasePermission):
    """Class transfer needs ``transfer_students``; the per-student relation (own school, own
    class, ...) is checked in the ``transfer`` action via ``access.can_transfer_student``."""

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return rbac.has_perm(request.user, TRANSFER_STUDENTS)


class CanEditStudentProfile(BasePermission):
    """Basic profile fields (name/phone/age/photo) may be edited by ``manage_students``
    (admin/superadmin), the class teacher of the student's class, a linked PARENT
    (``update_child_profile``) or the student themselves *only* if ``update_own_profile`` was
    explicitly granted. Class transfer and student_code stay out of this serializer entirely —
    those only ever change through the dedicated ``transfer`` action."""

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        user = request.user
        if request.method in {"PATCH", "PUT"}:
            return rbac.has_any_perm(
                user, MANAGE_STUDENTS, MANAGE_CLASS_STUDENTS, UPDATE_CHILD_PROFILE, UPDATE_OWN_PROFILE
            )
        # DELETE and anything else (POST) stays with student administrators.
        return rbac.has_perm(user, MANAGE_STUDENTS)

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        return access.can_edit_student(request.user, obj, method=request.method)


class CanManageRoles(BasePermission):
    """Granting / removing roles and permissions."""

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and rbac.has_perm(request.user, MANAGE_ROLES))
