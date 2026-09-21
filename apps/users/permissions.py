from rest_framework.permissions import BasePermission, SAFE_METHODS

from common.permissions import user_role


class IsSelfOrAdmin(BasePermission):
    """A user may act on their own account; admins may act on anyone."""

    def has_object_permission(self, request, view, obj):
        role = user_role(request.user)
        if role in {"ADMIN", "SUPERADMIN"}:
            return True
        return obj.id == request.user.id


class CanViewSensitiveStudentData(BasePermission):
    """Passport/ID and health records: only ADMIN/SUPERADMIN or explicitly-permitted staff."""

    def has_permission(self, request, view):
        role = user_role(request.user)
        if role in {"ADMIN", "SUPERADMIN"}:
            return True
        return request.user.is_staff and request.user.has_perm("users.view_sensitive_student_data")


def same_school(user, obj_school_id):
    """ADMIN is confined to their own school; SUPERADMIN stays global/unrestricted.
    Any other role reaching this helper is a bug in the caller, so it defaults closed."""
    role = user_role(user)
    if role == "SUPERADMIN":
        return True
    if role == "ADMIN":
        return bool(user.school_id) and user.school_id == obj_school_id
    return False


class CanAccessStudentProfile(BasePermission):
    """Student: self only. Parent: own children only. Teacher: own class students.
    Superadmin: everyone. Admin: everyone in their own school only."""

    def has_object_permission(self, request, view, obj):
        user = request.user
        role = user_role(user)

        if role in {"ADMIN", "SUPERADMIN"}:
            return same_school(user, obj.school_id)

        if role == "STUDENT":
            return obj.user_id == user.id

        if role == "PARENT":
            return obj.parent_links.filter(parent__user=user).exists()

        if role == "TEACHER":
            if obj.class_room_id is None:
                return False
            return (
                (obj.class_room.curator_id and obj.class_room.curator.user_id == user.id)
                or obj.class_room.lessons.filter(teacher__user=user).exists()
            )

        return False


class CanTransferStudent(BasePermission):
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return user_role(request.user) in {"ADMIN", "SUPERADMIN", "TEACHER"}


class CanEditStudentProfile(BasePermission):
    """Basic profile fields (name/phone/age/photo) may be edited by ADMIN/SUPERADMIN,
    the student's own teacher (curator or subject teacher), or a linked PARENT.
    Class transfer and student_code stay out of this serializer entirely — those only
    ever change through the dedicated `transfer` action."""

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        role = user_role(request.user)
        if request.method in {"PATCH", "PUT"}:
            return role in {"ADMIN", "SUPERADMIN", "TEACHER", "PARENT"}
        # DELETE and anything else stays admin-only.
        return role in {"ADMIN", "SUPERADMIN"}

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        return CanAccessStudentProfile().has_object_permission(request, view, obj)
