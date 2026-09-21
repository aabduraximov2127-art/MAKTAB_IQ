from django.db import models

from common.models import TimeStampedModel


class AcademicYear(TimeStampedModel):
    name = models.CharField(max_length=20, unique=True, help_text="Masalan: 2026-2027")
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=False)

    class Meta:
        ordering = ["-start_date"]

    def __str__(self):
        return self.name


class Quarter(TimeStampedModel):
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, related_name="quarters")
    number = models.PositiveSmallIntegerField(choices=[(i, f"{i}-quarter") for i in range(1, 5)])
    start_date = models.DateField()
    end_date = models.DateField()

    class Meta:
        unique_together = ("academic_year", "number")
        ordering = ["academic_year", "number"]

    def __str__(self):
        return f"{self.academic_year} - {self.number}-quarter"


class ClassRoom(TimeStampedModel):
    school = models.ForeignKey("schools.School", on_delete=models.CASCADE, related_name="classes")
    name = models.CharField(max_length=20, help_text="Masalan: 9-A")
    grade = models.PositiveSmallIntegerField()
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.PROTECT, related_name="classes")
    curator = models.ForeignKey(
        "users.TeacherProfile", on_delete=models.SET_NULL, null=True, blank=True, related_name="curated_classes"
    )

    class Meta:
        unique_together = ("school", "name", "academic_year")
        ordering = ["grade", "name"]

    def __str__(self):
        return f"{self.name} ({self.academic_year})"
