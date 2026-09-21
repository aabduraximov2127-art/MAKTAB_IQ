from rest_framework import serializers

from .models import StudentProgress


class StudentProgressResponseSerializer(serializers.Serializer):
    success = serializers.BooleanField()
    student = serializers.IntegerField()
    average_grade = serializers.FloatField()
    attendance_percentage = serializers.FloatField()
    homework_completion = serializers.FloatField()
    quiz_average = serializers.FloatField()


class AdminAnalyticsResponseSerializer(serializers.Serializer):
    success = serializers.BooleanField()
    total_students = serializers.IntegerField()
    total_teachers = serializers.IntegerField()
    total_classes = serializers.IntegerField()
    attendance_percentage = serializers.FloatField()
    average_grades = serializers.FloatField()
    homework_completion = serializers.FloatField()
    quiz_average = serializers.FloatField()
    active_users = serializers.IntegerField()
    absent_students = serializers.IntegerField()
    teacher_attendance_percentage = serializers.FloatField()


class StudentProgressSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentProgress
        fields = (
            "id",
            "student",
            "academic_year",
            "average_grade",
            "attendance_percentage",
            "homework_completion",
            "quiz_average",
            "computed_at",
        )
        read_only_fields = fields
