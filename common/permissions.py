from rest_framework.permissions import BasePermission

SAFE_ROLES = {"SUPERADMIN", "ADMIN", "TEACHER", "STUDENT", "PARENT"}


def user_role(user):
    return getattr(user, "role", None)


class HasRole(BasePermission):
    """Base class: subclass and set `allowed_roles`."""

    allowed_roles: set[str] = set()

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and user_role(request.user) in self.allowed_roles
        )


class IsSuperAdmin(HasRole):
    allowed_roles = {"SUPERADMIN"}


class IsAdmin(HasRole):
    allowed_roles = {"ADMIN", "SUPERADMIN"}


class IsTeacher(HasRole):
    allowed_roles = {"TEACHER"}


class IsStudent(HasRole):
    allowed_roles = {"STUDENT"}


class IsParent(HasRole):
    allowed_roles = {"PARENT"}


class IsAdminOrTeacher(HasRole):
    allowed_roles = {"ADMIN", "SUPERADMIN", "TEACHER"}


class IsStaff(HasRole):
    """Admin/Superadmin — used for sensitive data like passport, health record."""

    allowed_roles = {"ADMIN", "SUPERADMIN"}


class ReadOnly(BasePermission):
    def has_permission(self, request, view):
        return request.method in ("GET", "HEAD", "OPTIONS")
