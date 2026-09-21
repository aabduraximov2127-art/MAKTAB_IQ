from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from common.models import TimeStampedModel
from common.validators import validate_file_size


class Assignment(TimeStampedModel):
    lesson = models.ForeignKey("lessons.Lesson", on_delete=models.CASCADE, related_name="assignments")
    teacher = models.ForeignKey("users.TeacherProfile", on_delete=models.CASCADE, related_name="assignments")
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    attachment = models.FileField(
        upload_to="assignments/attachments/", null=True, blank=True, validators=[validate_file_size]
    )
    deadline = models.DateTimeField()

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title


class AssignmentSubmission(TimeStampedModel):
    class Status(models.TextChoices):
        SUBMITTED = "SUBMITTED", "Submitted"
        LATE = "LATE", "Late"
        GRADED = "GRADED", "Graded"

    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name="submissions")
    student = models.ForeignKey("users.StudentProfile", on_delete=models.CASCADE, related_name="submissions")
    answer = models.TextField(blank=True)
    attachment = models.FileField(
        upload_to="assignments/submissions/", null=True, blank=True, validators=[validate_file_size]
    )
    submitted_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.SUBMITTED)
    score = models.PositiveSmallIntegerField(
        null=True, blank=True, validators=[MinValueValidator(0), MaxValueValidator(100)]
    )

    class Meta:
        unique_together = ("assignment", "student")
        ordering = ["-submitted_at"]

    def __str__(self):
        return f"{self.student} -> {self.assignment}"
