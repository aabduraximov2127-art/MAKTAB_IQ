from rest_framework import permissions, status, viewsets
from rest_framework.response import Response

from common import rbac
from common.audit import log_action
from common.guards import ForbidOutOfScopeMixin
from common.permissions import require
from common.rbac import MANAGE_SCHOOL_SETTINGS, MANAGE_SCHOOLS

from .models import School
from .serializers import SchoolSerializer


class SchoolViewSet(ForbidOutOfScopeMixin, viewsets.ModelViewSet):
    """Schools.

    * Everybody signed in may *read* the list — it is a public lookup (registration forms).
    * ``manage_schools`` (SUPERADMIN) creates, edits and deletes any school.
    * ``manage_school_settings`` (a school's admin) may edit **only its own** school — an admin
      can neither create a school nor delete one (that would wipe a school's classes and
      orphan its accounts).
    * Deleting a school that still has classes, pupils, teachers or accounts needs an explicit
      ``?force=true``; without it the API answers 409 with what would be lost.
    """

    serializer_class = SchoolSerializer
    search_fields = ["name", "address"]

    def _confined_to_own_school(self):
        """School-bound settings managers (admin) only ever browse/edit their own school."""
        user = self.request.user
        return rbac.has_perm(user, MANAGE_SCHOOL_SETTINGS) and not rbac.has_perm(user, MANAGE_SCHOOLS)

    def get_queryset(self):
        qs = School.objects.all()
        if self._confined_to_own_school():
            return qs.filter(id=self.request.user.school_id)
        return qs

    def get_permissions(self):
        if self.request.method in permissions.SAFE_METHODS:
            return [permissions.IsAuthenticated()]
        if self.action in {"create", "destroy"}:
            return [require(MANAGE_SCHOOLS)()]
        return [require(MANAGE_SCHOOLS, MANAGE_SCHOOL_SETTINGS)()]

    def get_object(self):
        obj = super().get_object()
        if self._confined_to_own_school() and self.request.method not in permissions.SAFE_METHODS:
            if obj.id != self.request.user.school_id:
                self.permission_denied(self.request)
        return obj

    def perform_create(self, serializer):
        school = serializer.save()
        log_action(self.request.user, "SCHOOL_CREATED", target=school.name, description=f"id={school.pk}", request=self.request)

    def perform_update(self, serializer):
        school = serializer.save()
        log_action(self.request.user, "SCHOOL_UPDATED", target=school.name, description=f"id={school.pk}", request=self.request)

    def destroy(self, request, *args, **kwargs):
        school = self.get_object()
        dependents = {
            "classes": school.classes.count(),
            "students": school.students.count(),
            "teachers": school.teachers.count(),
            "users": school.users.count(),
        }
        if any(dependents.values()) and request.query_params.get("force") != "true":
            return Response(
                {
                    "success": False,
                    "message": "Maktabda hali sinflar, o'quvchilar, o'qituvchilar yoki hisoblar bor. "
                    "O'chirilsa sinflar va ular bilan bog'liq darslar, davomat, baholar yo'qoladi.",
                    "errors": {"dependents": dependents},
                },
                status=status.HTTP_409_CONFLICT,
            )
        log_action(request.user, "SCHOOL_DELETED", target=school.name, description=f"id={school.pk} {dependents}", request=request)
        return super().destroy(request, *args, **kwargs)
