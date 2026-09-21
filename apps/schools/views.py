from rest_framework import permissions, viewsets

from common.permissions import IsAdmin, user_role

from .models import School
from .serializers import SchoolSerializer


class SchoolViewSet(viewsets.ModelViewSet):
    serializer_class = SchoolSerializer
    search_fields = ["name", "address"]

    def get_queryset(self):
        qs = School.objects.all()
        # School Admin/Director only ever browses/edits their own school. Creating a
        # school (existing behavior, unchanged) isn't a detail action so is unaffected.
        # SUPERADMIN and every other role keep the existing unrestricted list.
        if user_role(self.request.user) == "ADMIN":
            return qs.filter(id=self.request.user.school_id)
        return qs

    def get_permissions(self):
        if self.request.method not in permissions.SAFE_METHODS:
            return [IsAdmin()]
        return [permissions.IsAuthenticated()]

    def get_object(self):
        obj = super().get_object()
        role = user_role(self.request.user)
        if role == "ADMIN" and self.request.method not in permissions.SAFE_METHODS:
            if obj.id != self.request.user.school_id:
                self.permission_denied(self.request)
        return obj
