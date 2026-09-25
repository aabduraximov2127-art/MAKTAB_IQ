from rest_framework import permissions, viewsets

from common import access
from common.permissions import require
from common.rbac import MANAGE_SUBJECTS
from common.guards import ForbidOutOfScopeMixin

from .models import Subject
from .serializers import SubjectSerializer


class SubjectViewSet(ForbidOutOfScopeMixin, viewsets.ModelViewSet):
    queryset = Subject.objects.all()
    serializer_class = SubjectSerializer
    search_fields = ["name"]

    def get_queryset(self):
        # Staff see the whole catalogue; a student the subjects of their class; a parent
        # their children's subjects (see common.access.subjects_scope).
        return access.subjects_scope(self.request.user, super().get_queryset())

    def get_permissions(self):
        if self.request.method not in permissions.SAFE_METHODS:
            return [require(MANAGE_SUBJECTS)()]
        return [permissions.IsAuthenticated()]
