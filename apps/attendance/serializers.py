from rest_framework import serializers

from apps.subjects.models import Subject

from .models import Attendance, AttendanceStatus, TeacherAttendance


class AttendanceSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source="student.user.get_full_name", read_only=True)
    # Daily (class register) attendance has no subject; only per-lesson marks name one.
    subject = serializers.PrimaryKeyRelatedField(queryset=Subject.objects.all(), required=False, allow_null=True, default=None)

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
            "absence_reason",
            "marked_by",
            "parent_reason",
            "parent_reason_submitted_at",
            "created_at",
        )
        read_only_fields = ("id", "marked_by", "parent_reason_submitted_at", "created_at")

    def validate(self, attrs):
        # The database treats two NULL subjects as different, so "one daily mark per pupil per
        # day" has to be enforced here.
        subject = attrs.get("subject", getattr(self.instance, "subject", None))
        student = attrs.get("student", getattr(self.instance, "student", None))
        date = attrs.get("date", getattr(self.instance, "date", None))
        if subject is None and student is not None and date is not None:
            clash = Attendance.objects.filter(student=student, date=date, subject__isnull=True)
            if self.instance is not None:
                clash = clash.exclude(pk=self.instance.pk)
            if clash.exists():
                raise serializers.ValidationError("Bu o'quvchining shu sanadagi davomati allaqachon belgilangan.")

        # A reason category only makes sense for an excused absence ("sababli"); every other
        # status (present / late / unexcused) carries none.
        status = attrs.get("status", getattr(self.instance, "status", None))
        if status != AttendanceStatus.EXCUSED:
            attrs["absence_reason"] = ""
        return attrs


class ParentReasonSerializer(serializers.Serializer):
    parent_reason = serializers.CharField()


class TeacherAttendanceSerializer(serializers.ModelSerializer):
    teacher_name = serializers.CharField(source="teacher.user.get_full_name", read_only=True)

    class Meta:
        model = TeacherAttendance
        fields = ("id", "teacher", "teacher_name", "date", "status", "reason", "created_at")
        read_only_fields = ("id", "created_at")
