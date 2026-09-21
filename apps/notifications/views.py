from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from common.permissions import IsAdmin, user_role

from .models import Announcement, EmergencyAnnouncement, Notification
from .serializers import AnnouncementSerializer, EmergencyAnnouncementSerializer, NotificationSerializer


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
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


class AnnouncementViewSet(viewsets.ModelViewSet):
    serializer_class = AnnouncementSerializer
    filterset_fields = ["target", "priority", "target_class"]

    def get_queryset(self):
        qs = Announcement.objects.select_related("target_class", "created_by")
        role = user_role(self.request.user)
        if role in {"ADMIN", "SUPERADMIN"}:
            return qs

        target_map = {
            "TEACHER": Announcement.Target.TEACHERS,
            "STUDENT": Announcement.Target.STUDENTS,
            "PARENT": Announcement.Target.PARENTS,
        }
        role_target = target_map.get(role)
        visible = qs.filter(target=Announcement.Target.ALL)
        if role_target:
            visible = visible | qs.filter(target=role_target)
        if role == "STUDENT":
            class_room_id = getattr(getattr(self.request.user, "student_profile", None), "class_room_id", None)
            if class_room_id:
                visible = visible | qs.filter(target=Announcement.Target.CLASS, target_class_id=class_room_id)
        return visible.distinct()

    def get_permissions(self):
        if self.request.method not in permissions.SAFE_METHODS:
            return [IsAdmin()]
        return [permissions.IsAuthenticated()]

    def perform_create(self, serializer):
        announcement = serializer.save(created_by=self.request.user)
        from .tasks import broadcast_announcement

        broadcast_announcement.delay(announcement.id)


class EmergencyAnnouncementViewSet(viewsets.ModelViewSet):
    queryset = EmergencyAnnouncement.objects.select_related("created_by")
    serializer_class = EmergencyAnnouncementSerializer

    def get_permissions(self):
        if self.request.method not in permissions.SAFE_METHODS:
            return [IsAdmin()]
        return [permissions.IsAuthenticated()]

    def perform_create(self, serializer):
        emergency = serializer.save(created_by=self.request.user)
        from .tasks import broadcast_emergency

        broadcast_emergency.delay(emergency.id)
