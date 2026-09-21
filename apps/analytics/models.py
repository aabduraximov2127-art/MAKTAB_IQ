from django.db import models

from common.models import TimeStampedModel


class StudentProgress(TimeStampedModel):
    """Periodic snapshot of a student's overall performance (populated by Celery)."""

    student = models.ForeignKey("users.StudentProfile", on_delete=models.CASCADE, related_name="progress_snapshots")
    academic_year = models.ForeignKey("classes.AcademicYear", on_delete=models.CASCADE, related_name="+")
    average_grade = models.FloatField(default=0)
    attendance_percentage = models.FloatField(default=0)
    homework_completion = models.FloatField(default=0, help_text="Percentage 0-100")
    quiz_average = models.FloatField(default=0)
    computed_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("student", "academic_year")
        ordering = ["-computed_at"]

    def __str__(self):
        return f"Progress: {self.student} ({self.academic_year})"
