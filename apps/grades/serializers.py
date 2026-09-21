from rest_framework import serializers

from .models import Grade


class GradeSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source="student.user.get_full_name", read_only=True)
    subject_name = serializers.CharField(source="subject.name", read_only=True)

    class Meta:
        model = Grade
        fields = (
            "id",
            "student",
            "student_name",
            "subject",
            "subject_name",
            "teacher",
            "academic_year",
            "quarter",
            "value",
            "grade_type",
            "comment",
            "created_at",
        )
        read_only_fields = ("id", "teacher", "created_at")


class AnnualResultSerializer(serializers.Serializer):
    subject = serializers.IntegerField(source="subject_id")
    subject_name = serializers.CharField()
    annual_average = serializers.FloatField()
    quarter_averages = serializers.DictField()
