from rest_framework import permissions, viewsets
from rest_framework.exceptions import PermissionDenied

from common import access, rbac
from common.permissions import require
from common.rbac import MANAGE_CLASSES
from common.guards import ForbidOutOfScopeMixin

from .models import AcademicYear, ClassRoom, Quarter
from .serializers import AcademicYearSerializer, ClassRoomSerializer, QuarterSerializer


class AcademicYearViewSet(viewsets.ModelViewSet):
    queryset = AcademicYear.objects.all()
    serializer_class = AcademicYearSerializer
    filterset_fields = ["is_active"]

    def get_permissions(self):
        if self.request.method not in permissions.SAFE_METHODS:
            return [require(MANAGE_CLASSES)()]
        return [permissions.IsAuthenticated()]


class QuarterViewSet(viewsets.ModelViewSet):
    queryset = Quarter.objects.select_related("academic_year")
    serializer_class = QuarterSerializer
    filterset_fields = ["academic_year", "number"]

    def get_permissions(self):
        if self.request.method not in permissions.SAFE_METHODS:
            return [require(MANAGE_CLASSES)()]
        return [permissions.IsAuthenticated()]


class ClassRoomViewSet(ForbidOutOfScopeMixin, viewsets.ModelViewSet):
    serializer_class = ClassRoomSerializer
    search_fields = ["name"]
    filterset_fields = ["school", "grade", "academic_year", "curator"]

    def get_queryset(self):
        qs = ClassRoom.objects.select_related("school", "academic_year", "curator__user")
        return access.classes_scope(self.request.user, qs)

    def get_permissions(self):
        if self.request.method not in permissions.SAFE_METHODS:
            return [require(MANAGE_CLASSES)()]
        return [permissions.IsAuthenticated()]

    def perform_create(self, serializer):
        self._enforce_own_school(serializer)
        serializer.save()

    def perform_update(self, serializer):
        self._enforce_own_school(serializer)
        serializer.save()

    def _enforce_own_school(self, serializer):
        # School Admin/Director may only create/update classes in their own school —
        # SUPERADMIN (and, unaffected, TEACHER/PARENT read-only access) keep existing
        # behavior. The class object itself is already school-scoped by get_queryset
        # for update, so this mainly guards against the `school` field being set/moved
        # to a different school in the request body.
        if rbac.is_global(self.request.user):
            return
        school = serializer.validated_data.get("school")
        if school is not None and school.id != self.request.user.school_id:
            raise PermissionDenied("Boshqa maktab uchun class yarata/o'zgartira olmaysiz.")
