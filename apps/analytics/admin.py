from django.contrib import admin

from .models import StudentProgress


@admin.register(StudentProgress)
class StudentProgressAdmin(admin.ModelAdmin):
    list_display = ("student", "academic_year", "average_grade", "attendance_percentage", "quiz_average")
