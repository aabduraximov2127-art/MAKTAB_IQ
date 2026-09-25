from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from rest_framework.exceptions import PermissionDenied

from common import access, rbac
from common.permissions import require
from common.rbac import SEND_ANNOUNCEMENTS, SEND_CLASS_ANNOUNCEMENT
from common.guards import ForbidOutOfScopeMixin

from .models import Announcement, EmergencyAnnouncement, Notification
from .serializers import AnnouncementSerializer, EmergencyAnnouncementSerializer, NotificationSerializer


class NotificationViewSet(ForbidOutOfScopeMixin, viewsets.ReadOnlyModelViewSet):
    serializer_class = NotificationSerializer
    filterset_fields = ["type", "is_read"]

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)

    @action(detail=True, methods=["post"])
    def mark_read(self, request, pk=None):
        notification = self.get_object()
        notification.is_read = True
        notification.save(update_fields=["is_read"])
        return Response(NotificationSerializer(notification).data)

    @action(detail=False, methods=["post"])
    def mark_all_read(self, request):
        self.get_queryset().filter(is_read=False).update(is_read=True)
        return Response({"success": True, "message": "Barcha notification o'qilgan deb belgilandi"})


class AnnouncementViewSet(ForbidOutOfScopeMixin, viewsets.ModelViewSet):
    """School announcements. Anyone signed in reads what is addressed to them
    (``access.announcements_scope``); ``send_announcements`` (admin, superadmin) writes to
    any audience; a class teacher (``send_class_announcement``) may only address *their own
    class* and only edits/deletes what they sent themselves."""

    serializer_class = AnnouncementSerializer
    filterset_fields = ["target", "priority", "target_class"]

    def get_queryset(self):
        qs = Announcement.objects.select_related("target_class", "created_by")
        return access.announcements_scope(self.request.user, qs)

    def get_permissions(self):
        if self.request.method not in permissions.SAFE_METHODS:
            return [require(SEND_ANNOUNCEMENTS, SEND_CLASS_ANNOUNCEMENT)()]
        return [permissions.IsAuthenticated()]

    def _check_audience(self, serializer):
        user = self.request.user
        if rbac.has_perm(user, SEND_ANNOUNCEMENTS):
            return
        target = serializer.validated_data.get("target", getattr(serializer.instance, "target", None))
        target_class = serializer.validated_data.get("target_class", getattr(serializer.instance, "target_class", None))
        if target != Announcement.Target.CLASS or target_class is None or not access.curates(user, target_class):
            raise PermissionDenied("Faqat o'z sinfingizga e'lon yubora olasiz.")

    def get_object(self):
        obj = super().get_object()
        user = self.request.user
        if self.request.method not in permissions.SAFE_METHODS and not rbac.has_perm(user, SEND_ANNOUNCEMENTS):
            if obj.created_by_id != user.id:
                self.permission_denied(self.request)
        return obj

    def perform_create(self, serializer):
        self._check_audience(serializer)
        announcement = serializer.save(created_by=self.request.user)
        from .tasks import broadcast_announcement

        broadcast_announcement.delay(announcement.id)

    def perform_update(self, serializer):
        self._check_audience(serializer)
        serializer.save()


class EmergencyAnnouncementViewSet(viewsets.ModelViewSet):
    queryset = EmergencyAnnouncement.objects.select_related("created_by")
    serializer_class = EmergencyAnnouncementSerializer

    def get_permissions(self):
        if self.request.method not in permissions.SAFE_METHODS:
            return [require(SEND_ANNOUNCEMENTS)()]
        return [permissions.IsAuthenticated()]

    def perform_create(self, serializer):
        emergency = serializer.save(created_by=self.request.user)
        from .tasks import broadcast_emergency

        broadcast_emergency.delay(emergency.id)
