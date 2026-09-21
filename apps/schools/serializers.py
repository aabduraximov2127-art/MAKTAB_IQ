from rest_framework import serializers

from .models import School


class SchoolSerializer(serializers.ModelSerializer):
    class Meta:
        model = School
        fields = ("id", "name", "address", "phone", "email", "logo", "created_at")
        read_only_fields = ("id", "created_at")
