from django.db import models

from common.models import TimeStampedModel


class AttendanceStatus(models.TextChoices):
    PRESENT = "PRESENT", "Present"
    ABSENT = "ABSENT", "Absent"
    LATE = "LATE", "Late"
    EXCUSED = "EXCUSED", "Excused"


class Attendance(TimeStampedModel):
    student = models.ForeignKey("users.StudentProfile", on_delete=models.CASCADE, related_name="attendances")
    class_room = models.ForeignKey("classes.ClassRoom", on_delete=models.CASCADE, related_name="attendances")
    subject = models.ForeignKey(
        "subjects.Subject", on_delete=models.SET_NULL, null=True, blank=True, related_name="attendances"
    )
    lesson = models.ForeignKey(
        "lessons.Lesson", on_delete=models.SET_NULL, null=True, blank=True, related_name="attendances"
    )
    date = models.DateField()
    status = models.CharField(max_length=10, choices=AttendanceStatus.choices, default=AttendanceStatus.PRESENT)
    marked_by = models.ForeignKey(
        "users.TeacherProfile", on_delete=models.SET_NULL, null=True, related_name="marked_attendances"
    )
    parent_reason = models.TextField(blank=True, help_text="Parent tomonidan yuborilgan sabab")
    parent_reason_submitted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ("student", "date", "subject")
        ordering = ["-date"]
        indexes = [models.Index(fields=["student", "date"]), models.Index(fields=["class_room", "date"])]

    def __str__(self):
        return f"{self.student} - {self.date}: {self.status}"


class TeacherAttendance(TimeStampedModel):
    teacher = models.ForeignKey("users.TeacherProfile", on_delete=models.CASCADE, related_name="attendances")
    date = models.DateField()
    status = models.CharField(max_length=10, choices=AttendanceStatus.choices, default=AttendanceStatus.PRESENT)
    reason = models.CharField(max_length=255, blank=True)

    class Meta:
        unique_together = ("teacher", "date")
        ordering = ["-date"]

    def __str__(self):
        return f"{self.teacher} - {self.date}: {self.status}"
