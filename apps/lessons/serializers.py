from rest_framework import serializers

from .models import Lesson


class LessonSerializer(serializers.ModelSerializer):
    subject_name = serializers.CharField(source="subject.name", read_only=True)
    teacher_name = serializers.CharField(source="teacher.user.get_full_name", read_only=True)
    class_room_name = serializers.CharField(source="class_room.name", read_only=True)

    class Meta:
        model = Lesson
        fields = (
            "id",
            "class_room",
            "class_room_name",
            "subject",
            "subject_name",
            "teacher",
            "teacher_name",
            "room",
            "date",
            "start_time",
            "end_time",
            "created_at",
        )
        read_only_fields = ("id", "created_at")

    def validate(self, attrs):
        start_time = attrs.get("start_time", getattr(self.instance, "start_time", None))
        end_time = attrs.get("end_time", getattr(self.instance, "end_time", None))
        date = attrs.get("date", getattr(self.instance, "date", None))
        teacher = attrs.get("teacher", getattr(self.instance, "teacher", None))
        room = attrs.get("room", getattr(self.instance, "room", None))
        class_room = attrs.get("class_room", getattr(self.instance, "class_room", None))

        if start_time and end_time and start_time >= end_time:
            raise serializers.ValidationError("start_time end_time'dan oldin bo'lishi kerak.")

        overlapping = Lesson.objects.filter(date=date, start_time__lt=end_time, end_time__gt=start_time)
        if self.instance is not None:
            overlapping = overlapping.exclude(pk=self.instance.pk)

        if overlapping.filter(teacher=teacher).exists():
            raise serializers.ValidationError(
                "Bu teacher shu vaqtda boshqa darsga band."
            )
        if overlapping.filter(room=room).exists():
            raise serializers.ValidationError(
                "Bu xona shu vaqtda boshqa dars uchun band."
            )
        if overlapping.filter(class_room=class_room).exists():
            raise serializers.ValidationError(
                "Bu class shu vaqtda boshqa darsga band."
            )
        return attrs
