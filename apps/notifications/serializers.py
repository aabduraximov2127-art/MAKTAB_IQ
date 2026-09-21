from rest_framework import serializers

from .models import Announcement, EmergencyAnnouncement, Notification


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ("id", "title", "message", "type", "is_read", "created_at")
        read_only_fields = fields


class AnnouncementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Announcement
        fields = (
            "id",
            "title",
            "content",
            "priority",
            "target",
            "target_class",
            "created_by",
            "created_at",
        )
        read_only_fields = ("id", "created_by", "created_at")


class EmergencyAnnouncementSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmergencyAnnouncement
        fields = ("id", "title", "content", "created_by", "created_at")
        read_only_fields = ("id", "created_by", "created_at")
