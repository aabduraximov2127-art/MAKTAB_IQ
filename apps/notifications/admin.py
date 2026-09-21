from django.contrib import admin

from .models import Announcement, EmergencyAnnouncement, Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("user", "type", "title", "is_read", "created_at")
    list_filter = ("type", "is_read")


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ("title", "target", "priority", "created_by", "created_at")
    list_filter = ("target", "priority")


@admin.register(EmergencyAnnouncement)
class EmergencyAnnouncementAdmin(admin.ModelAdmin):
    list_display = ("title", "created_by", "created_at")
