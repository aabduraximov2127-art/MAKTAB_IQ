from rest_framework import permissions, viewsets

from common import rbac
from common.permissions import require
from common.rbac import MANAGE_SCHOOL_SETTINGS
from common.guards import ForbidOutOfScopeMixin

from .models import School
from .serializers import SchoolSerializer


class SchoolViewSet(ForbidOutOfScopeMixin, viewsets.ModelViewSet):
    serializer_class = SchoolSerializer
    search_fields = ["name", "address"]

    def _confined_to_own_school(self):
        """School-bound settings managers (admin) only ever browse/edit their own school.
        A global SUPERADMIN and every other authenticated user keep the existing
        unrestricted list (the school list is a public lookup, e.g. for registration)."""
        user = self.request.user
        return rbac.has_perm(user, MANAGE_SCHOOL_SETTINGS) and not rbac.is_global(user)

    def get_queryset(self):
        qs = School.objects.all()
        if self._confined_to_own_school():
            return qs.filter(id=self.request.user.school_id)
        return qs

    def get_permissions(self):
        if self.request.method not in permissions.SAFE_METHODS:
            return [require(MANAGE_SCHOOL_SETTINGS)()]
        return [permissions.IsAuthenticated()]

    def get_object(self):
        obj = super().get_object()
        if self._confined_to_own_school() and self.request.method not in permissions.SAFE_METHODS:
            if obj.id != self.request.user.school_id:
                self.permission_denied(self.request)
        return obj
