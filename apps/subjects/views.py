from rest_framework import permissions, viewsets

from common.permissions import IsAdmin

from .models import Subject
from .serializers import SubjectSerializer


class SubjectViewSet(viewsets.ModelViewSet):
    queryset = Subject.objects.all()
    serializer_class = SubjectSerializer
    search_fields = ["name"]

    def get_permissions(self):
        if self.request.method not in permissions.SAFE_METHODS:
            return [IsAdmin()]
        return [permissions.IsAuthenticated()]
