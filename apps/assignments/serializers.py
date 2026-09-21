from rest_framework import serializers

from .models import Assignment, AssignmentSubmission


class AssignmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Assignment
        fields = (
            "id",
            "lesson",
            "teacher",
            "title",
            "description",
            "attachment",
            "deadline",
            "created_at",
        )
        read_only_fields = ("id", "teacher", "created_at")


class AssignmentSubmissionSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source="student.user.get_full_name", read_only=True)

    class Meta:
        model = AssignmentSubmission
        fields = (
            "id",
            "assignment",
            "student",
            "student_name",
            "answer",
            "attachment",
            "submitted_at",
            "status",
            "score",
        )
        read_only_fields = ("id", "student", "submitted_at", "status", "score")


class SubmissionGradeSerializer(serializers.Serializer):
    score = serializers.IntegerField(min_value=0, max_value=100)
