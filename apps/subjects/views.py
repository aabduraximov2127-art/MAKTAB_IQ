from rest_framework import permissions, viewsets
from rest_framework.exceptions import PermissionDenied

from common import access, rbac
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

    def _guard_shared_subject(self, subject):
        # the catalogue is shared: a school admin cannot rename / delete a subject that other
        # schools' lessons, grades or teachers use — only the SuperAdmin can
        user = self.request.user
        if not rbac.is_global(user) and access.subject_used_outside_school(subject, user.school_id):
            raise PermissionDenied("Bu fan boshqa maktablarda ham ishlatiladi; uni faqat SuperAdmin o'zgartira oladi.")

    def perform_update(self, serializer):
        self._guard_shared_subject(serializer.instance)
        serializer.save()

    def perform_destroy(self, instance):
        self._guard_shared_subject(instance)
        instance.delete()
