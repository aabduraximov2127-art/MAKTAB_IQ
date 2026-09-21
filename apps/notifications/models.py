from django.db import models

from common.models import TimeStampedModel


class NotificationType(models.TextChoices):
    GRADE = "GRADE", "New grade"
    ATTENDANCE = "ATTENDANCE", "Attendance"
    ABSENT = "ABSENT", "Absent"
    HOMEWORK = "HOMEWORK", "Homework"
    HOMEWORK_DEADLINE = "HOMEWORK_DEADLINE", "Homework deadline"
    QUIZ_RESULT = "QUIZ_RESULT", "Quiz result"
    ANNOUNCEMENT = "ANNOUNCEMENT", "Announcement"
    EMERGENCY = "EMERGENCY", "Emergency"
    CHAT_MESSAGE = "CHAT_MESSAGE", "Chat message"


class Notification(TimeStampedModel):
    user = models.ForeignKey("users.User", on_delete=models.CASCADE, related_name="notifications")
    title = models.CharField(max_length=255)
    message = models.TextField()
    type = models.CharField(max_length=30, choices=NotificationType.choices)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["user", "is_read"])]

    def __str__(self):
        return f"{self.user} - {self.type}: {self.title}"


class Announcement(TimeStampedModel):
    class Target(models.TextChoices):
        ALL = "ALL", "Whole school"
        TEACHERS = "TEACHERS", "Teachers"
        STUDENTS = "STUDENTS", "Students"
        PARENTS = "PARENTS", "Parents"
        CLASS = "CLASS", "Specific class"

    class Priority(models.TextChoices):
        LOW = "LOW", "Low"
        NORMAL = "NORMAL", "Normal"
        HIGH = "HIGH", "High"

    title = models.CharField(max_length=255)
    content = models.TextField()
    priority = models.CharField(max_length=10, choices=Priority.choices, default=Priority.NORMAL)
    target = models.CharField(max_length=10, choices=Target.choices, default=Target.ALL)
    target_class = models.ForeignKey(
        "classes.ClassRoom", on_delete=models.SET_NULL, null=True, blank=True, related_name="announcements"
    )
    created_by = models.ForeignKey("users.User", on_delete=models.SET_NULL, null=True, related_name="+")

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title


class EmergencyAnnouncement(TimeStampedModel):
    title = models.CharField(max_length=255)
    content = models.TextField()
    created_by = models.ForeignKey("users.User", on_delete=models.SET_NULL, null=True, related_name="+")

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"[EMERGENCY] {self.title}"
