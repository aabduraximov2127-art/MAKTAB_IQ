from rest_framework.permissions import BasePermission

from . import rbac

SAFE_ROLES = set(rbac.STORED_ROLES)


def user_role(user):
    """The user's *primary* role (``User.role``). Use ``rbac.effective_roles`` when the
    full set of roles matters (a user may hold several)."""
    return getattr(user, "role", None)


def _authenticated(request):
    return bool(request.user and request.user.is_authenticated)


class HasRole(BasePermission):
    """Base class: subclass and set `allowed_roles`. Multi-role aware: passes if *any* of
    the user's roles (primary, extra, derived) is allowed."""

    allowed_roles: set[str] = set()

    def has_permission(self, request, view):
        return _authenticated(request) and rbac.has_role(request.user, *self.allowed_roles)


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


# ---------------------------------------------------------------------------
# Permission-based access (the RBAC layer, see common/rbac.py)
# ---------------------------------------------------------------------------
class RBACPermission(BasePermission):
    """Table-driven permission check.

    A view declares which permission codenames unlock which action::

        rbac_permissions = {
            "list": [VIEW_ALL_STUDENTS, VIEW_OWN_PROFILE],   # ANY of these is enough
            "create": [MANAGE_STUDENTS],
            "*": [MANAGE_STUDENTS],                          # fallback for other actions
        }

    The key is the ViewSet ``action`` (``list``, ``retrieve``, ``create``, ``update``,
    ``partial_update``, ``destroy`` or a custom @action name); plain ``APIView``s use the
    lower-case HTTP method (``get``, ``post`` ...). An action with no entry and no ``"*"``
    fallback is **denied** (default closed). An empty list means "any authenticated user".

    Anonymous requests are always refused, which DRF turns into ``401 Unauthorized``;
    an authenticated user lacking the permission gets ``403 Forbidden``.

    Object-level rules: define ``rbac_check_object(self, request, obj) -> bool`` on the view
    — it is consulted by ``get_object()`` via ``has_object_permission``.
    """

    message = "Bu amal uchun sizda ruxsat yo'q."

    def has_permission(self, request, view):
        if not _authenticated(request):
            return False
        table = getattr(view, "rbac_permissions", None)
        if table is None:
            return False
        action = getattr(view, "action", None)
        if action is None and hasattr(view, "action_map"):
            # A ViewSet route that doesn't map this HTTP method: let DRF answer 405.
            return True
        key = action or request.method.lower()
        required = table.get(key, table.get("*"))
        if required is None:
            return False
        if len(required) == 0:
            return True
        return rbac.has_any_perm(request.user, *required)

    def has_object_permission(self, request, view, obj):
        check = getattr(view, "rbac_check_object", None)
        return True if check is None else bool(check(request, obj))


def require(*codenames: str):
    """Permission class that passes when the user holds ANY of ``codenames``::

        permission_classes = [require(MANAGE_USERS)]
    """

    class _Require(BasePermission):
        message = "Bu amal uchun sizda ruxsat yo'q."

        def has_permission(self, request, view):
            return _authenticated(request) and rbac.has_any_perm(request.user, *codenames)

    _Require.__name__ = "Require_" + "_or_".join(codenames)
    _Require.__qualname__ = _Require.__name__
    return _Require
