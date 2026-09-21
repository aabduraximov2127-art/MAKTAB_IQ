from rest_framework import serializers

from .models import AcademicYear, ClassRoom, Quarter


class AcademicYearSerializer(serializers.ModelSerializer):
    class Meta:
        model = AcademicYear
        fields = ("id", "name", "start_date", "end_date", "is_active", "created_at")
        read_only_fields = ("id", "created_at")


class QuarterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Quarter
        fields = ("id", "academic_year", "number", "start_date", "end_date")
        read_only_fields = ("id",)


class ClassRoomSerializer(serializers.ModelSerializer):
    curator_name = serializers.CharField(source="curator.user.get_full_name", read_only=True, default=None)
    student_count = serializers.IntegerField(source="students.count", read_only=True)

    class Meta:
        model = ClassRoom
        fields = (
            "id",
            "school",
            "name",
            "grade",
            "academic_year",
            "curator",
            "curator_name",
            "student_count",
            "created_at",
        )
        read_only_fields = ("id", "created_at")
