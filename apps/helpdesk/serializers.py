from rest_framework import serializers

from .models import HelpDeskTicket


class HelpDeskTicketSerializer(serializers.ModelSerializer):
    class Meta:
        model = HelpDeskTicket
        fields = (
            "id",
            "user",
            "title",
            "description",
            "category",
            "priority",
            "status",
            "assigned_to",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "user", "created_at", "updated_at")
