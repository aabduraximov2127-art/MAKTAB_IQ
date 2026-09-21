from rest_framework import serializers

from .models import Subject


class SubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = ("id", "name", "description", "icon", "created_at")
        read_only_fields = ("id", "created_at")
