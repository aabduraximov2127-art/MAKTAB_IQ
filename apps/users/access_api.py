"""Role & permission administration API.

    GET    /api/v1/roles/                              role catalogue + default permissions
    GET    /api/v1/permissions/                        permission catalogue
    GET    /api/v1/users/{id}/access/                  one user's roles + effective permissions
    POST   /api/v1/users/{id}/roles/                   {"role": "DIRECTOR", "primary": false}
    DELETE /api/v1/users/{id}/roles/{ROLE}/            remove an extra role
    POST   /api/v1/users/{id}/permissions/             {"permission": "transfer_students"}
    DELETE /api/v1/users/{id}/permissions/{codename}/  revoke a per-user grant

Storage reuses what already exists: the primary role is ``User.role``, extra roles are
``User.groups`` memberships (group name == role code) and per-user permission grants are
``User.user_permissions`` — no new tables.

Guard rails (all enforced here, on the backend):

* the actor needs ``manage_roles`` (roles) or ``manage_permissions`` (permission grants);
* a school-bound admin only touches accounts of their own school and never a SUPERADMIN;
* nobody edits their **own** roles/permissions (no self-escalation, no accidental lock-out);
* only a SUPERADMIN may hand out the SUPERADMIN role, or the system-level permissions listed in
  ``SYSTEM_PERMISSIONS``;
* ``CLASS_TEACHER`` cannot be assigned — it exists automatically while the user is the
  curator of a class.
"""

from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from rest_framework import permissions, serializers, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from common import rbac
from common.audit import log_action
from common.permissions import require
from common.rbac import MANAGE_PERMISSIONS, MANAGE_ROLES

from .permissions import can_manage_user

# Permissions that only a global administrator (SUPERADMIN) may grant to a single user.
SYSTEM_PERMISSIONS = frozenset(
    {
        rbac.MANAGE_ROLES,
        rbac.MANAGE_PERMISSIONS,
        rbac.MANAGE_USERS,
        rbac.MANAGE_SCHOOL_SETTINGS,
        rbac.VIEW_SENSITIVE_STUDENT_DATA,
        rbac.MODERATE_CHAT,
        rbac.MANAGE_SCHOOLS,
        rbac.MANAGE_ADMINS,
        rbac.DELETE_USERS,
        rbac.VIEW_SYSTEM_STATS,
    }
)


class RoleAssignSerializer(serializers.Serializer):
    role = serializers.ChoiceField(choices=[(r, rbac.ROLE_LABELS[r]) for r in rbac.STORED_ROLES])
    primary = serializers.BooleanField(required=False, default=False)


class PermissionGrantSerializer(serializers.Serializer):
    permission = serializers.ChoiceField(choices=sorted(rbac.PERMISSIONS))


def _deny(message, code=status.HTTP_403_FORBIDDEN):
    return Response({"success": False, "message": message, "errors": {}}, status=code)


def describe_access(user):
    """Everything the RBAC layer knows about ``user`` (also what the admin UI renders)."""
    from apps.classes.models import ClassRoom

    fresh = get_user_model().objects.get(pk=user.pk)  # never reuse a cached instance
    info = rbac.access_for(fresh)
    extra_roles = sorted(
        name for name in fresh.groups.values_list("name", flat=True) if name in rbac.STORED_ROLES and name != fresh.role
    )
    return {
        "id": fresh.id,
        "username": fresh.username,
        "primary_role": fresh.role,
        "extra_roles": extra_roles,
        "roles": [r for r in rbac.ALL_ROLES if r in info.roles],
        "permissions": sorted(info.permissions),
        "extra_permissions": sorted(info.extra_permissions),
        "curated_classes": list(ClassRoom.objects.filter(curator__user=fresh).values("id", "name")),
    }


class UserAccessMixin:
    """Actions mixed into ``UserViewSet`` (kept here so ``views.py`` stays readable)."""

    def _target(self, pk):
        return get_object_or_404(get_user_model().objects.all(), pk=pk)

    def _guard(self, request, target):
        """Common checks for every role/permission mutation; returns an error Response or None."""
        if target.pk == request.user.pk:
            return _deny("O'z rolingiz va ruxsatlaringizni o'zgartira olmaysiz.")
        if not can_manage_user(request.user, target):
            return _deny("Bu foydalanuvchini boshqarishga ruxsatingiz yo'q.")
        return None

    # -- read -----------------------------------------------------------------
    @action(detail=True, methods=["get"], url_path="access", permission_classes=[permissions.IsAuthenticated])
    def access(self, request, pk=None):
        target = self._target(pk)
        if target.pk != request.user.pk and not can_manage_user(request.user, target):
            return _deny("Bu foydalanuvchining ruxsatlarini ko'rishga ruxsatingiz yo'q.")
        return Response(describe_access(target))

    # -- roles ----------------------------------------------------------------
    @action(detail=True, methods=["post"], url_path="roles", permission_classes=[require(MANAGE_ROLES)])
    def grant_role(self, request, pk=None):
        target = self._target(pk)
        if (error := self._guard(request, target)) is not None:
            return error

        serializer = RoleAssignSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        role = serializer.validated_data["role"]
        make_primary = serializer.validated_data["primary"]

        if role == rbac.SUPERADMIN and not rbac.is_global(request.user):
            return _deny("SUPERADMIN rolini faqat SUPERADMIN bera oladi.")

        if make_primary:
            if target.role == rbac.SUPERADMIN and not rbac.is_global(request.user):
                return _deny("SUPERADMIN foydalanuvchining rolini o'zgartira olmaysiz.")
            target.role = role
            target.save(update_fields=["role"])
            target.groups.remove(*target.groups.filter(name=role))  # primary role needs no group
        elif role != target.role:
            target.groups.add(rbac.get_role_group(role))

        rbac.invalidate(target)
        log_action(
            request.user,
            "ROLE_GRANTED",
            target=target.username,
            description=f"{role}{' (primary)' if make_primary else ''}",
            request=request,
        )
        return Response(describe_access(target), status=status.HTTP_200_OK)

    @action(
        detail=True,
        methods=["delete"],
        url_path=r"roles/(?P<role>[A-Z_]+)",
        url_name="remove-role",
        permission_classes=[require(MANAGE_ROLES)],
    )
    def remove_role(self, request, pk=None, role=None):
        target = self._target(pk)
        if (error := self._guard(request, target)) is not None:
            return error
        if role == rbac.CLASS_TEACHER:
            return _deny(
                "Sinf rahbari roli sinfga rahbar sifatida biriktirilganda avtomatik hosil bo'ladi; "
                "uni olib tashlash uchun sinfning rahbarini almashtiring.",
                status.HTTP_400_BAD_REQUEST,
            )
        if role not in rbac.STORED_ROLES:
            return _deny("Noma'lum rol.", status.HTTP_400_BAD_REQUEST)
        if role == target.role:
            return _deny(
                "Asosiy rolni olib tashlab bo'lmaydi — avval boshqa rolni asosiy qilib belgilang.",
                status.HTTP_400_BAD_REQUEST,
            )
        if role == rbac.SUPERADMIN and not rbac.is_global(request.user):
            return _deny("SUPERADMIN rolini faqat SUPERADMIN olib tashlay oladi.")

        target.groups.remove(*target.groups.filter(name=role))
        rbac.invalidate(target)
        log_action(request.user, "ROLE_REVOKED", target=target.username, description=role, request=request)
        return Response(describe_access(target))

    # -- per-user permission grants -----------------------------------------
    @action(detail=True, methods=["post"], url_path="permissions", permission_classes=[require(MANAGE_PERMISSIONS)])
    def grant_permission(self, request, pk=None):
        target = self._target(pk)
        if (error := self._guard(request, target)) is not None:
            return error

        serializer = PermissionGrantSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        codename = serializer.validated_data["permission"]
        if codename in SYSTEM_PERMISSIONS and not rbac.is_global(request.user):
            return _deny("Bu tizim darajasidagi ruxsatni faqat SUPERADMIN bera oladi.")

        target.user_permissions.add(rbac.get_permission_row(codename))
        rbac.invalidate(target)
        log_action(request.user, "PERMISSION_GRANTED", target=target.username, description=codename, request=request)
        return Response(describe_access(target))

    @action(
        detail=True,
        methods=["delete"],
        url_path=r"permissions/(?P<codename>[a-z_]+)",
        url_name="remove-permission",
        permission_classes=[require(MANAGE_PERMISSIONS)],
    )
    def remove_permission(self, request, pk=None, codename=None):
        target = self._target(pk)
        if (error := self._guard(request, target)) is not None:
            return error
        if codename not in rbac.PERMISSIONS:
            return _deny("Noma'lum ruxsat.", status.HTTP_400_BAD_REQUEST)
        if codename in SYSTEM_PERMISSIONS and not rbac.is_global(request.user):
            return _deny("Bu tizim darajasidagi ruxsatni faqat SUPERADMIN olib tashlay oladi.")

        target.user_permissions.remove(*target.user_permissions.filter(codename=codename))
        rbac.invalidate(target)
        log_action(request.user, "PERMISSION_REVOKED", target=target.username, description=codename, request=request)
        return Response(describe_access(target))


class RoleListView(APIView):
    """Role catalogue with each role's *default* permissions (the SuperAdmin's view of the role system)."""

    permission_classes = [require(MANAGE_ROLES)]
    serializer_class = serializers.Serializer

    def get(self, request):
        data = [
            {
                "code": role,
                "label": rbac.ROLE_LABELS[role],
                "derived": role in rbac.DERIVED_ROLES,
                "assignable": role in rbac.STORED_ROLES,
                "permissions": sorted(rbac.ROLE_PERMISSIONS[role]),
            }
            for role in rbac.ALL_ROLES
        ]
        return Response(data)


class PermissionListView(APIView):
    """Permission catalogue (codename, category, description)."""

    permission_classes = [require(MANAGE_PERMISSIONS, MANAGE_ROLES)]
    serializer_class = serializers.Serializer

    def get(self, request):
        data = [
            {
                "codename": info.codename,
                "category": info.category,
                "description": info.description,
                "system": info.codename in SYSTEM_PERMISSIONS,
            }
            for info in rbac.PERMISSIONS.values()
        ]
        return Response(data)
