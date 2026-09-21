from rest_framework import viewsets
from rest_framework.permissions import SAFE_METHODS, BasePermission, IsAuthenticated

from common.permissions import user_role

from .models import HelpDeskTicket
from .serializers import HelpDeskTicketSerializer


class IsOwnerOrAdmin(BasePermission):
    def has_object_permission(self, request, view, obj):
        role = user_role(request.user)
        if role in {"ADMIN", "SUPERADMIN"}:
            return True
        if request.method in SAFE_METHODS:
            return obj.user_id == request.user.id
        return False


class HelpDeskTicketViewSet(viewsets.ModelViewSet):
    serializer_class = HelpDeskTicketSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]
    filterset_fields = ["status", "category", "priority", "assigned_to"]

    def get_queryset(self):
        qs = HelpDeskTicket.objects.select_related("user", "assigned_to")
        role = user_role(self.request.user)
        if role in {"ADMIN", "SUPERADMIN"}:
            return qs
        return qs.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
