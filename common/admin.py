from django.contrib import admin

from .models import AuditLog, LoginHistory


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("actor", "action", "target", "ip_address", "created_at")
    list_filter = ("action",)
    search_fields = ("target", "description", "actor__username")
    ordering = ("-created_at",)


@admin.register(LoginHistory)
class LoginHistoryAdmin(admin.ModelAdmin):
    list_display = ("user", "ip_address", "success", "login_at")
    list_filter = ("success",)
    ordering = ("-login_at",)
