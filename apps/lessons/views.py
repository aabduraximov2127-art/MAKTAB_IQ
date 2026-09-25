from rest_framework import permissions, viewsets
from rest_framework.exceptions import PermissionDenied

from common import access, rbac
from common.permissions import require
from common.rbac import MANAGE_SCHEDULE
from common.guards import ForbidOutOfScopeMixin

from .models import Lesson
from .serializers import LessonSerializer


class LessonViewSet(ForbidOutOfScopeMixin, viewsets.ModelViewSet):
    serializer_class = LessonSerializer
    filterset_fields = ["class_room", "subject", "teacher", "date"]

    def get_queryset(self):
        qs = Lesson.objects.select_related("class_room", "subject", "teacher__user")
        return access.lessons_scope(self.request.user, qs)

    def get_permissions(self):
        if self.request.method not in permissions.SAFE_METHODS:
            return [require(MANAGE_SCHEDULE)()]
        return [permissions.IsAuthenticated()]

    def perform_create(self, serializer):
        self._enforce_own_school(serializer)
        serializer.save()

    def perform_update(self, serializer):
        self._enforce_own_school(serializer)
        serializer.save()

    def _enforce_own_school(self, serializer):
        # School Admin/Director may only schedule lessons for their own school's
        # classes. The lesson itself is already school-scoped by get_queryset for
        # update (cross-school PATCH 404s before reaching here); this additionally
        # guards against re-pointing class_room to a different school's class.
        if rbac.is_global(self.request.user):
            return
        class_room = serializer.validated_data.get("class_room")
        if class_room is not None and class_room.school_id != self.request.user.school_id:
            raise PermissionDenied("Boshqa maktabning classiga dars biriktira olmaysiz.")
