from rest_framework import permissions, viewsets
from rest_framework.exceptions import PermissionDenied

from common.permissions import IsAdmin, user_role

from .models import Lesson
from .serializers import LessonSerializer


class LessonViewSet(viewsets.ModelViewSet):
    serializer_class = LessonSerializer
    filterset_fields = ["class_room", "subject", "teacher", "date"]

    def get_queryset(self):
        qs = Lesson.objects.select_related("class_room", "subject", "teacher__user")
        role = user_role(self.request.user)
        user = self.request.user

        if role == "SUPERADMIN":
            return qs
        if role == "ADMIN":
            return qs.filter(class_room__school=user.school)
        if role == "TEACHER":
            return qs.filter(teacher__user=user)
        if role == "STUDENT":
            return qs.filter(class_room__students__user=user)
        if role == "PARENT":
            return qs.filter(class_room__students__parent_links__parent__user=user)
        return qs.none()

    def get_permissions(self):
        if self.request.method not in permissions.SAFE_METHODS:
            return [IsAdmin()]
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
        if user_role(self.request.user) != "ADMIN":
            return
        class_room = serializer.validated_data.get("class_room")
        if class_room is not None and class_room.school_id != self.request.user.school_id:
            raise PermissionDenied("Boshqa maktabning classiga dars biriktira olmaysiz.")
