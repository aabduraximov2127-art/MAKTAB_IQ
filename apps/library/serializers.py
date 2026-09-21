from rest_framework import serializers

from .models import LibraryMaterial


class LibraryMaterialSerializer(serializers.ModelSerializer):
    class Meta:
        model = LibraryMaterial
        fields = (
            "id",
            "title",
            "material_type",
            "subject",
            "author",
            "file",
            "link",
            "uploaded_by",
            "created_at",
        )
        read_only_fields = ("id", "uploaded_by", "created_at")
