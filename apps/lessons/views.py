from rest_framework import permissions, viewsets
from rest_framework.exceptions import PermissionDenied

from common import access, rbac
from common.rbac import MANAGE_CLASS_SCHEDULE, MANAGE_SCHEDULE
from common.guards import ForbidOutOfScopeMixin

from .models import Lesson
from .serializers import LessonSerializer


class CanManageSchedule(permissions.BasePermission):
    """Reading needs authentication only (the queryset already scopes rows); writing needs
    ``manage_schedule`` (school-wide: admin/director/deputy/superadmin) or, for a class
    teacher, ``manage_class_schedule`` limited to the class(es) they curate."""

    def has_permission(self, request, view):
        user = request.user
        if not (user and user.is_authenticated):
            return False
        if request.method in permissions.SAFE_METHODS:
            return True
        return rbac.has_any_perm(user, MANAGE_SCHEDULE, MANAGE_CLASS_SCHEDULE)

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return access.can_manage_schedule(request.user, obj.class_room)


class LessonViewSet(ForbidOutOfScopeMixin, viewsets.ModelViewSet):
    serializer_class = LessonSerializer
    permission_classes = [CanManageSchedule]
    filterset_fields = ["class_room", "subject", "teacher", "date"]

    def get_queryset(self):
        qs = Lesson.objects.select_related("class_room", "subject", "teacher__user")
        return access.lessons_scope(self.request.user, qs)

    def perform_create(self, serializer):
        class_room = serializer.validated_data.get("class_room")
        if class_room is None or not access.can_manage_schedule(self.request.user, class_room):
            raise PermissionDenied("Bu sinf uchun dars jadvalini boshqarishga ruxsatingiz yo'q.")
        serializer.save()

    def perform_update(self, serializer):
        class_room = serializer.validated_data.get("class_room", serializer.instance.class_room)
        if not access.can_manage_schedule(self.request.user, class_room):
            raise PermissionDenied("Bu sinf uchun dars jadvalini boshqarishga ruxsatingiz yo'q.")
        serializer.save()
