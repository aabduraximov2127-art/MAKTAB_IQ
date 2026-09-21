from rest_framework import serializers

from .models import Attendance, TeacherAttendance


class AttendanceSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source="student.user.get_full_name", read_only=True)

    class Meta:
        model = Attendance
        fields = (
            "id",
            "student",
            "student_name",
            "class_room",
            "subject",
            "lesson",
            "date",
            "status",
            "marked_by",
            "parent_reason",
            "parent_reason_submitted_at",
            "created_at",
        )
        read_only_fields = ("id", "marked_by", "parent_reason_submitted_at", "created_at")


class ParentReasonSerializer(serializers.Serializer):
    parent_reason = serializers.CharField()


class TeacherAttendanceSerializer(serializers.ModelSerializer):
    teacher_name = serializers.CharField(source="teacher.user.get_full_name", read_only=True)

    class Meta:
        model = TeacherAttendance
        fields = ("id", "teacher", "teacher_name", "date", "status", "reason", "created_at")
        read_only_fields = ("id", "created_at")
