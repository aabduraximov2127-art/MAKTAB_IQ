from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from common.models import TimeStampedModel


class Grade(TimeStampedModel):
    class GradeType(models.TextChoices):
        DAILY = "DAILY", "Daily"
        HOMEWORK = "HOMEWORK", "Homework"
        QUIZ = "QUIZ", "Quiz"
        QUARTER = "QUARTER", "Quarter"
        EXAM = "EXAM", "Exam"

    student = models.ForeignKey("users.StudentProfile", on_delete=models.CASCADE, related_name="grades")
    subject = models.ForeignKey("subjects.Subject", on_delete=models.CASCADE, related_name="grades")
    teacher = models.ForeignKey("users.TeacherProfile", on_delete=models.SET_NULL, null=True, related_name="grades")
    academic_year = models.ForeignKey("classes.AcademicYear", on_delete=models.CASCADE, related_name="grades")
    quarter = models.ForeignKey("classes.Quarter", on_delete=models.CASCADE, related_name="grades")
    value = models.PositiveSmallIntegerField(validators=[MinValueValidator(0), MaxValueValidator(10)])
    grade_type = models.CharField(max_length=20, choices=GradeType.choices, default=GradeType.DAILY)
    comment = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["student", "subject", "quarter"])]

    def __str__(self):
        return f"{self.student} - {self.subject} - {self.quarter}: {self.value}"
