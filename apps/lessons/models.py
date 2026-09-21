from django.db import models

from common.models import TimeStampedModel


class Lesson(TimeStampedModel):
    class_room = models.ForeignKey("classes.ClassRoom", on_delete=models.CASCADE, related_name="lessons")
    subject = models.ForeignKey("subjects.Subject", on_delete=models.CASCADE, related_name="lessons")
    teacher = models.ForeignKey("users.TeacherProfile", on_delete=models.CASCADE, related_name="lessons")
    room = models.CharField(max_length=50)
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()

    class Meta:
        ordering = ["date", "start_time"]
        indexes = [
            models.Index(fields=["date", "start_time", "end_time"]),
            models.Index(fields=["teacher", "date"]),
            models.Index(fields=["room", "date"]),
        ]

    def __str__(self):
        return f"{self.class_room} - {self.subject} - {self.date} {self.start_time}"
