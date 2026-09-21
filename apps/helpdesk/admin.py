from django.contrib import admin

from .models import HelpDeskTicket


@admin.register(HelpDeskTicket)
class HelpDeskTicketAdmin(admin.ModelAdmin):
    list_display = ("title", "user", "category", "priority", "status", "assigned_to")
    list_filter = ("status", "category", "priority")
