from rest_framework import viewsets
from rest_framework.permissions import SAFE_METHODS, BasePermission, IsAuthenticated

from common import rbac
from common.rbac import MANAGE_HELPDESK
from common.guards import ForbidOutOfScopeMixin

from .models import HelpDeskTicket
from .serializers import HelpDeskTicketSerializer


class IsOwnerOrAdmin(BasePermission):
    def has_object_permission(self, request, view, obj):
        if rbac.has_perm(request.user, MANAGE_HELPDESK):
            return True
        if request.method in SAFE_METHODS:
            return obj.user_id == request.user.id
        return False


class HelpDeskTicketViewSet(ForbidOutOfScopeMixin, viewsets.ModelViewSet):
    serializer_class = HelpDeskTicketSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]
    filterset_fields = ["status", "category", "priority", "assigned_to"]

    def get_queryset(self):
        qs = HelpDeskTicket.objects.select_related("user", "assigned_to")
        if rbac.has_perm(self.request.user, MANAGE_HELPDESK):
            return qs
        return qs.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
